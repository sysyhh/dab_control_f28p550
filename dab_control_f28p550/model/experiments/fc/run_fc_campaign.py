"""FC mapping campaign from the original FPU 3-29-12-6-4 network.

Builds padded / zero-neuron INT8 and INT4 MatMul graphs, checks float
equivalence and PWM-count error against dab_nn.c, then compiles with
NNC 2.1.1 without converting MatMul to Conv. All artifacts stay under
model/experiments/fc. Does not overwrite the live NPU library, does not
flash a board, and does not enable power output.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
ROOT = APP.parent
TOOLS = APP / "tools"
NN_C = APP / "dab_nn.c"
sys.path.insert(0, str(TOOLS))
from analyze_int8_error import NAMES, firmware_pwm, nn_valid, pwm_error  # noqa: E402
from expand_and_quantize_npu import (  # noqa: E402
    firmware_features, load_weights, original_forward, tighten_prelu_ranges,
)

ORIGINAL = ((3, 29), (29, 12), (12, 6), (6, 4))
ORIGINAL_MACS = sum(a * b for a, b in ORIGINAL)
PWCONV_SHAPE = (4, 32, 12, 8, 4)
PWCONV_MACS = 4 * 32 + 32 * 12 + 12 * 8 + 8 * 4
TBPRD = 2500.0
NNC_PY = ROOT / "review_20261003/npu_integration_20261009/nnc211_env/python.exe"
COMPILER = HERE / "compile_fc_npu.py"

CANDIDATES = {
    "int8_input_pad": {
        "bits": 8,
        "in_width": 16,
        "layers": ((16, 29, True, 29), (29, 12, True, 12), (16, 6, True, 6), (16, 4, False, 4)),
        "orig_in": (3, 29, 12, 6),
        "pad_after": (None, 16, 16, None),
        "method": "input_and_intermediate_zero_pad",
        "runtime_pad_ops": 2,
        "input_pad": 13,
    },
    "int8_zero_neuron": {
        "bits": 8,
        "in_width": 16,
        "layers": ((16, 29, True, 29), (29, 16, True, 12), (16, 16, True, 6), (16, 4, False, 4)),
        "orig_in": (3, 29, 12, 6),
        "pad_after": (None, None, None, None),
        "method": "zero_output_neurons",
        "runtime_pad_ops": 0,
        "input_pad": 13,
    },
    "int4_input_pad": {
        "bits": 4,
        "in_width": 8,
        "layers": ((8, 29, True, 29), (29, 12, True, 12), (12, 6, True, 6), (8, 4, False, 4)),
        "orig_in": (3, 29, 12, 6),
        "pad_after": (None, None, 8, None),
        "method": "input_and_intermediate_zero_pad",
        "runtime_pad_ops": 1,
        "input_pad": 5,
    },
    "int4_zero_neuron": {
        "bits": 4,
        "in_width": 8,
        "layers": ((8, 29, True, 29), (29, 12, True, 12), (12, 8, True, 6), (8, 4, False, 4)),
        "orig_in": (3, 29, 12, 6),
        "pad_after": (None, None, None, None),
        "method": "zero_output_neurons",
        "runtime_pad_ops": 0,
        "input_pad": 5,
    },
}


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pad_vec(values, width):
    out = np.zeros(width, np.float32)
    src = np.asarray(values, np.float32).reshape(-1)
    out[: src.shape[0]] = src
    return out


def features(vin, width):
    return pad_vec(firmware_features(vin), width)


def macs(spec):
    return int(sum(a * b for a, b, _relu, _keep in spec["layers"]))


class CandidateMlp(nn.Module):
    def __init__(self, spec):
        super().__init__()
        self.spec = spec
        self.layers = nn.ModuleList()
        self.pad_sizes = []
        for index, (nin, nout, _relu, _keep) in enumerate(spec["layers"]):
            self.layers.append(nn.Linear(nin, nout))
            target = spec["pad_after"][index]
            extra = 0 if target is None or target <= nout else int(target - nout)
            self.pad_sizes.append(extra)

    def forward(self, features):
        hidden = features
        for index, layer in enumerate(self.layers):
            hidden = layer(hidden)
            if self.spec["layers"][index][2]:
                hidden = torch.relu(hidden)
            extra = self.pad_sizes[index]
            if extra:
                hidden = F.pad(hidden, (0, extra))
        return hidden


def load_candidate(weights, spec):
    model = CandidateMlp(spec).float()
    copied = [
        (weights["w1"].reshape(29, 3), weights["b1"], 29, 3),
        (weights["w2"].reshape(12, 29), weights["b2"], 12, 29),
        (weights["w3"].reshape(6, 12), weights["b3"], 6, 12),
        (weights["w4"].reshape(4, 6), weights["b4"], 4, 6),
    ]
    with torch.no_grad():
        for layer, (matrix, bias, rows, cols), (nin, nout, _relu, keep) in zip(
                model.layers, copied, spec["layers"]):
            layer.weight.zero_()
            layer.bias.zero_()
            if keep < rows or layer.weight.shape[1] < cols:
                raise RuntimeError("candidate smaller than original copied block")
            layer.weight[:rows, :cols] = torch.from_numpy(matrix)
            layer.bias[:rows] = torch.from_numpy(bias)
            extra_w = layer.weight.clone()
            extra_w[:rows, :cols] = 0
            extra_b = layer.bias.clone()
            extra_b[:rows] = 0
            if float(extra_w.abs().max()) != 0 or float(extra_b.abs().max()) != 0:
                # extra rows/cols must stay zero; the check below uses the live tensors
                pass
            if keep != nout and float(layer.weight[keep:].abs().sum() + layer.bias[keep:].abs().sum()) != 0:
                raise RuntimeError("extra output neurons are not zero")
            if layer.weight.shape[1] > cols and float(layer.weight[:, cols:].abs().sum()) != 0:
                raise RuntimeError("padded input columns are not zero")
    model.eval()
    return model


def numpy_forward(spec, weights, vin):
    orig = [
        (weights["w1"].reshape(29, 3), weights["b1"], 29, 3),
        (weights["w2"].reshape(12, 29), weights["b2"], 12, 29),
        (weights["w3"].reshape(6, 12), weights["b3"], 6, 12),
        (weights["w4"].reshape(4, 6), weights["b4"], 4, 6),
    ]
    hidden = features(vin, spec["in_width"])
    extras = []
    traces = []
    for (matrix, bias, rows, cols), (nin, nout, relu, keep), pad_to in zip(
            orig, spec["layers"], spec["pad_after"]):
        if hidden.shape[0] < nin:
            hidden = pad_vec(hidden, nin)
        if hidden.shape[0] != nin:
            raise RuntimeError(f"input width {hidden.shape[0]} != {nin}")
        wide_w = np.zeros((nout, nin), np.float32)
        wide_b = np.zeros(nout, np.float32)
        wide_w[:rows, :cols] = matrix
        wide_b[:rows] = bias
        pre = wide_b.copy()
        for i in range(nout):
            total = np.float32(wide_b[i])
            for j in range(nin):
                total = np.float32(total + np.float32(hidden[j] * wide_w[i, j]))
            pre[i] = total
        extra = pre[keep:]
        extras.append(float(np.max(np.abs(extra))) if extra.size else 0.0)
        post = np.maximum(pre, np.float32(0)) if relu else pre
        traces.append({"pre_min": float(pre.min()), "pre_max": float(pre.max()),
                       "post_min": float(post.min()), "post_max": float(post.max()),
                       "extra_max_abs": extras[-1]})
        hidden = post
        if pad_to is not None:
            hidden = pad_vec(hidden, pad_to)
    return hidden, extras, traces


def quantize(model, calibration, bits):
    from tinyml_torchmodelopt.quantization import TINPUTinyMLPTQFxModule
    from tinyml_torchmodelopt.quantization.common import TinyMLQConfigType
    example = calibration[:1].contiguous()
    qconfig = TinyMLQConfigType(weight_bitwidth=bits, activation_bitwidth=8, auto_quantization=False)
    wrapped = TINPUTinyMLPTQFxModule(
        model, total_epochs=1, qconfig_type=qconfig, example_inputs=example,
        output_int=False, num_observer_update_epochs=False, num_batch_norm_update_epochs=False)
    wrapped.train()
    with torch.no_grad():
        wrapped(calibration)
    tighten_prelu_ranges(wrapped)
    wrapped.freeze(freeze_bn=True, freeze_observers=True)
    return wrapped.convert()


def squeeze_tinpu_fc_onnx(path: Path) -> dict:
    """Keep MatMul/FC in NC. TINPU broadcasts (1,1,1,1) scales to 4D, and NNC then
    inserts reshape between qnn.dense and bias_add, which breaks the FC pattern.
    This does not rewrite MatMul as Conv.
    """
    import onnx
    from onnx import numpy_helper, helper, TensorProto, shape_inference
    import onnxruntime as ort

    import shutil
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    in_name = session.get_inputs()[0].name
    in_shape = [d if isinstance(d, int) and d > 0 else 1 for d in session.get_inputs()[0].shape]
    probe = np.zeros(in_shape, np.float32)
    probe.reshape(-1)[min(1, probe.size - 1)] = 0.7
    before = session.run(None, {in_name: probe})[0].reshape(-1)

    work = path.with_suffix(".squeeze_work.onnx")
    shutil.copyfile(path, work)
    model = onnx.load(str(work))
    squeezed = 0
    pad_inputs = {node.input[1] for node in model.graph.node if node.op_type == "Pad" and len(node.input) > 1}
    for tensor in model.graph.initializer:
        array = numpy_helper.to_array(tensor)
        if tensor.name in pad_inputs and array.size == 8:
            new = np.array([array[0], array[3], array[4], array[7]], array.dtype)
            tensor.CopyFrom(numpy_helper.from_array(new, tensor.name))
            squeezed += 1
            continue
        if array.ndim >= 3 and all(dim == 1 for dim in array.shape[:-1]):
            flat = array.reshape(-1)
            replacement = flat.reshape(()) if flat.size == 1 else flat.reshape(flat.shape[-1],)
            tensor.CopyFrom(numpy_helper.from_array(replacement, tensor.name))
            squeezed += 1
        elif array.ndim == 4 and array.shape[0] == 1 and array.shape[1] == 1 and array.shape[2] == 1:
            tensor.CopyFrom(numpy_helper.from_array(array.reshape(1, array.shape[3]), tensor.name))
            squeezed += 1
    out = model.graph.output[0]
    out_dims = [d.dim_value for d in out.type.tensor_type.shape.dim]
    if len(out_dims) == 4 and out_dims[:3] == [1, 1, 1]:
        new_out = helper.make_tensor_value_info(out.name, TensorProto.FLOAT, [1, out_dims[3]])
        del model.graph.output[:]
        model.graph.output.append(new_out)
    del model.graph.value_info[:]
    model = shape_inference.infer_shapes(model)
    onnx.checker.check_model(model)
    ranks = []
    for value in list(model.graph.input) + list(model.graph.output) + list(model.graph.value_info):
        ranks.append(len(value.type.tensor_type.shape.dim))
    onnx.save(model, str(work))
    after = ort.InferenceSession(str(work), providers=["CPUExecutionProvider"]).run(None, {in_name: probe})[0].reshape(-1)
    max_diff = float(np.max(np.abs(after - before)))
    if max_diff > 1e-6:
        work.unlink(missing_ok=True)
        raise RuntimeError(f"2D squeeze changed values by {max_diff}")
    shutil.move(str(work), str(path))
    return {"squeezed_initializers": squeezed, "max_rank": int(max(ranks) if ranks else 0),
            "output_shape": [d.dim_value for d in model.graph.output[0].type.tensor_type.shape.dim],
            "max_abs_vs_4d": max_diff}


def export_quant(converted, example, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    converted.export(example, str(path), input_names=["features"], output_names=["modulation"], simplify=False)
    try:
        squeeze_tinpu_fc_onnx(path)
    except Exception as error:
        dump(path.with_suffix(".squeeze_error.json"), {"error": str(error)})
    return path


def onnx_ops(path: Path) -> dict:
    import onnx
    model = onnx.load(str(path))
    ops = Counter(node.op_type for node in model.graph.node)
    return {"ops": dict(ops), "matmul": int(ops.get("MatMul", 0) + ops.get("Gemm", 0)),
            "conv": int(ops.get("Conv", 0)), "relu": int(ops.get("Relu", 0)),
            "pad": int(ops.get("Pad", 0)), "concat": int(ops.get("Concat", 0))}


def onnx_predict(path: Path, vins, width):
    import onnxruntime as ort
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name
    rows = []
    for vin in vins:
        item = features(vin, width).reshape(1, -1)
        rows.append(session.run(None, {name: item})[0].reshape(-1).astype(np.float32))
    return np.stack(rows)


def metrics(predicted, expected, vins):
    predicted = np.asarray(predicted, np.float32)
    expected = np.asarray(expected, np.float32)
    error = np.abs(predicted - expected)
    pwm = [pwm_error(expected[i], predicted[i]) for i in range(len(expected))]
    counts = np.array([item["max_count"] for item in pwm], np.int32)
    invalid = [i for i, row in enumerate(predicted) if not nn_valid(row)]
    worst_abs = int(np.argmax(error.max(axis=1)))
    worst_pwm = int(np.argmax(counts))
    return {
        "max_abs": [float(v) for v in error.max(axis=0)],
        "mean_abs": [float(v) for v in error.mean(axis=0)],
        "max_pwm_count": int(counts.max()) if len(counts) else 0,
        "mean_pwm_count": float(counts.mean()) if len(counts) else 0,
        "pwm_tbprd_max": int(max(item["tbprd"] for item in pwm)) if pwm else 0,
        "pwm_cmpA2_max": int(max(item["cmpA2"] for item in pwm)) if pwm else 0,
        "pwm_cmpA4_max": int(max(item["cmpA4"] for item in pwm)) if pwm else 0,
        "pwm_phase34_max": int(max(item["phase34"] for item in pwm)) if pwm else 0,
        "within_one_pwm": bool(len(counts) and int(counts.max()) <= 1),
        "invalid_count": len(invalid),
        "invalid_vins": [float(vins[i]) for i in invalid[:12]],
        "worst_abs_vin": float(vins[worst_abs]),
        "worst_abs": [float(v) for v in error[worst_abs]],
        "worst_pwm_vin": float(vins[worst_pwm]),
        "worst_pwm_count": int(counts[worst_pwm]),
        "teacher_invalid": int(sum(not nn_valid(row) for row in expected)),
    }


def mini_linear(nin, nout):
    model = nn.Sequential(nn.Linear(nin, nout)).float()
    nn.init.uniform_(model[0].weight, -0.25, 0.25)
    nn.init.zeros_(model[0].bias)
    model.eval()
    return model


def mini_mlp(widths):
    layers = []
    for index in range(len(widths) - 1):
        layers.append(nn.Linear(widths[index], widths[index + 1]))
        if index != len(widths) - 2:
            layers.append(nn.ReLU())
    model = nn.Sequential(*layers).float()
    for module in model.modules():
        if isinstance(module, nn.Linear):
            nn.init.uniform_(module.weight, -0.25, 0.25)
            nn.init.zeros_(module.bias)
    model.eval()
    return model


def build_mini(name, model, bits, nin, out_dir: Path):
    torch.manual_seed(0)
    calibration = torch.randn(64, nin) * 0.3
    converted = quantize(model, calibration, bits)
    path = out_dir / f"{name}.onnx"
    export_quant(converted, calibration[:1], path)
    info = onnx_ops(path)
    info["name"] = name
    info["bits"] = bits
    info["in_width"] = nin
    info["onnx"] = str(path)
    return path, info


def compile_one(onnx_path: Path, out: Path, force_hw: bool) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    command = [str(NNC_PY), str(COMPILER), "--onnx", str(onnx_path), "--out", str(out)]
    if force_hw:
        command.append("--force-hw")
    completed = subprocess.run(command, capture_output=True, text=True, errors="replace")
    audit_path = out / "fc_audit.json"
    if audit_path.exists():
        report = json.loads(audit_path.read_text(encoding="utf-8"))
    else:
        report = {"returncode": completed.returncode, "stdout_tail": (completed.stdout + completed.stderr)[-4000:]}
    report["subprocess_returncode"] = completed.returncode
    if completed.returncode and "compile_error_tail" not in report:
        report["compile_error_tail"] = (completed.stdout + completed.stderr)[-4000:]
    dump(out / "fc_audit.json", report)
    return report


def phase0(out: Path) -> dict:
    onnx_dir = out / "onnx"
    gen = out / "generated"
    minis = []
    jobs = [
        ("mini_int8_16x4", mini_linear(16, 4), 8, 16),
        ("mini_int8_8x4", mini_linear(8, 4), 8, 8),
        ("mini_int4_8x4", mini_linear(8, 4), 4, 8),
        ("mini_int8_3x4", mini_linear(3, 4), 8, 3),
        ("mini_int8_16_8_8_4", mini_mlp((16, 8, 8, 4)), 8, 16),
    ]
    for name, model, bits, nin in jobs:
        path, info = build_mini(name, model, bits, nin, onnx_dir)
        minis.append(info)
        dump(onnx_dir / f"{name}_graph.json", info)
    compiles = []
    schedule = [
        ("mini_int8_16x4", False),
        ("mini_int8_16x4", True),
        ("mini_int8_8x4", True),
        ("mini_int4_8x4", True),
        ("mini_int8_3x4", True),
        ("mini_int8_16_8_8_4", True),
    ]
    for name, force_hw in schedule:
        tag = f"{name}_{'force_hw' if force_hw else 'default'}"
        print(f"NNC compile {tag}", flush=True)
        report = compile_one(onnx_dir / f"{name}.onnx", gen / tag, force_hw)
        report["job"] = tag
        compiles.append(report)
        dump(out / "results" / f"phase0_{tag}.json", report)
    docs = {
        "nnc": "2.1.1",
        "official_fc_table": {
            "int8_weights_kB8": {"iC": "m1b16 (>=16)", "oC": "any"},
            "int4_weights_kB4": {"iC": "m1b8 (>=8)", "oC": "any"},
        },
        "pattern": "MatMul => BNORM (Add bias => Mul scale => right shift => Floor => Clip)",
        "relu_in_fc_pattern": False,
        "c28_default": "TINIE_fullyConnected software/DMAC; FORCE_NO_TI_C28_SOFT_OFFLOAD selects TINIE_fullyConnectedNHWC",
        "force_flag_comment": "TI internal flag for testing FC TI-NPU microcode on the C28",
        "params_bufsize": 2048,
        "fc_max_ic_no_host": (2048 // 8 - 2) * 8,
    }
    summary = {"docs": docs, "graphs": minis, "compiles": [
        {k: report.get(k) for k in (
            "job", "returncode", "force_no_c28_soft_offload", "hardware_fc_mapped",
            "software_fc_library", "cpu_generated_fc", "log_fc_offloaded", "log_fc_cpu",
            "tinie_fullyConnectedNHWC", "tinie_fullyConnected_soft_calls", "fc_ins_tables",
            "tinie_layer_increments", "header_ti_npu", "header_ti_npu_soft", "iC_warnings",
            "fc_offload_info", "conv_rewrite_detected", "onnx")}
        for report in compiles
    ]}
    dump(out / "results" / "phase0.json", summary)
    return summary


def phase1(weights, out: Path) -> dict:
    rows = []
    for name, spec in CANDIDATES.items():
        model = load_candidate(weights, spec)
        torch.save(model.state_dict(), out / "onnx" / f"{name}_float.pt")
        extra_peaks = []
        float_err = []
        for vin in [round(90.0 + 0.1 * i, 1) for i in range(501)]:
            pred, extras, _traces = numpy_forward(spec, weights, vin)
            expected = original_forward(weights, firmware_features(vin))
            float_err.append(np.abs(pred[:4] - expected))
            extra_peaks.append(max(extras) if extras else 0.0)
        float_err = np.stack(float_err)
        rows.append({
            "name": name,
            "bits": spec["bits"],
            "method": spec["method"],
            "in_width": spec["in_width"],
            "structure": [spec["in_width"]] + [layer[1] for layer in spec["layers"]],
            "copied_from": [3, 29, 12, 6, 4],
            "macs": macs(spec),
            "original_macs": ORIGINAL_MACS,
            "pwconv_macs": PWCONV_MACS,
            "runtime_pad_ops": spec["runtime_pad_ops"],
            "input_zero_pad": spec["input_pad"],
            "fp32_max_abs": [float(v) for v in float_err.max(axis=0)],
            "extra_neuron_max_abs": float(max(extra_peaks)),
            "fp32_equivalent": bool(float_err.max() < 2e-6),
            "extra_neurons_zero": bool(max(extra_peaks) < 1e-12),
        })
    dump(out / "results" / "phase1.json", {"candidates": rows})
    return {"candidates": rows}


def evaluate_quant(name, spec, weights, path: Path, vins_sets):
    width = spec["in_width"]
    report = {"name": name, "onnx": str(path), "graph": onnx_ops(path)}
    for set_name, vins in vins_sets.items():
        expected = np.stack([original_forward(weights, firmware_features(vin)) for vin in vins])
        predicted = onnx_predict(path, vins, width)
        report[set_name] = metrics(predicted, expected, vins)
    traces = []
    for vin in vins_sets["official_90_140_step_0_1"]:
        _out, _extras, layer_traces = numpy_forward(spec, weights, vin)
        traces.append(layer_traces)
    relu_range = []
    for layer in range(3):
        lows = [row[layer]["pre_min"] for row in traces]
        highs = [row[layer]["pre_max"] for row in traces]
        posts = [row[layer]["post_max"] for row in traces]
        relu_range.append({
            "layer": layer + 1,
            "pre_min": float(min(lows)),
            "pre_max": float(max(highs)),
            "relu_post_max": float(max(posts)),
            "negative_pre_exists": bool(min(lows) < 0),
        })
    report["relu_float_ranges"] = relu_range
    return report


def phase2(weights, out: Path) -> dict:
    onnx_dir = out / "onnx"
    operating = [float(vin) for vin in range(90, 141)]
    official = [round(90.0 + 0.1 * i, 1) for i in range(501)]
    dense = [round(92.20 + 0.01 * i, 2) for i in range(31)]
    holdout = [round(90.05 + 0.1 * i, 2) for i in range(500)]
    vins_sets = {
        "cal_90_140_step_1": operating,
        "official_90_140_step_0_1": official,
        "dense_92_2_92_5": dense,
        "holdout_90_140_step_0_1_offset": holdout,
    }
    rows = []
    for name, spec in CANDIDATES.items():
        print(f"quantize {name}", flush=True)
        model = load_candidate(weights, spec)
        calibration = torch.from_numpy(np.stack([features(vin, spec["in_width"]) for vin in operating]))
        converted = quantize(model, calibration, spec["bits"])
        path = onnx_dir / f"{name}.onnx"
        export_quant(converted, calibration[:1], path)
        item = evaluate_quant(name, spec, weights, path, vins_sets)
        item["macs"] = macs(spec)
        item["structure"] = [spec["in_width"]] + [layer[1] for layer in spec["layers"]]
        rows.append(item)
        dump(out / "results" / f"phase2_{name}.json", item)
    dump(out / "results" / "phase2.json", {"candidates": rows})
    return {"candidates": rows}


def phase3(out: Path) -> dict:
    onnx_dir = out / "onnx"
    gen = out / "generated"
    jobs = [
        ("int8_input_pad", False),
        ("int8_input_pad", True),
        ("int8_zero_neuron", True),
        ("int4_input_pad", True),
        ("int4_zero_neuron", True),
    ]
    compiles = []
    for name, force_hw in jobs:
        tag = f"{name}_{'force_hw' if force_hw else 'default'}"
        print(f"NNC compile {tag}", flush=True)
        report = compile_one(onnx_dir / f"{name}.onnx", gen / tag, force_hw)
        report["job"] = tag
        compiles.append(report)
        dump(out / "results" / f"phase3_{tag}.json", report)
    live = APP / "model/generated/npu"
    pwconv = None
    if (live / "lib2.c").exists():
        lib2 = (live / "lib2.c").read_text(encoding="utf-8", errors="replace")
        pwconv = {
            "shape": list(PWCONV_SHAPE),
            "macs": PWCONV_MACS,
            "tinie_layer_increments": lib2.count("tinie_curr_layer += 1;"),
            "pwconv_params": lib2.count("PWCONV_PARAMS"),
            "lib2_bytes": (live / "lib2.c").stat().st_size,
            "mod_a_bytes": (live / "mod.a").stat().st_size if (live / "mod.a").exists() else None,
            "hardware_operator": "TINIE_convolve1x1NHWC / PWCONV",
        }
    summary = {
        "compiles": compiles,
        "pwconv_live": pwconv,
        "isolation": {
            "live_npu_untouched": True,
            "board_flash": False,
            "power_control": False,
            "ccs_project_modified": False,
        },
    }
    dump(out / "results" / "phase3.json", summary)
    return summary


def fmt_list(values, digits=6):
    return "[" + ", ".join(f"{float(v):.{digits}g}" for v in values) + "]"


def write_report(out: Path, phase0_data, phase1_data, phase2_data, phase3_data) -> Path:
    p0 = {item["job"]: item for item in phase0_data["compiles"]}
    p1 = {item["name"]: item for item in phase1_data["candidates"]}
    p2 = {item["name"]: item for item in phase2_data["candidates"]}
    p3 = {item.get("job"): item for item in phase3_data["compiles"]}

    def mapping_line(job):
        item = job if isinstance(job, dict) else {}
        if item.get("hardware_fc_mapped"):
            return (f"硬件 FC：NHWC={item.get('tinie_fullyConnectedNHWC')}，"
                    f"INS={item.get('fc_ins_tables')}，"
                    f"layer+={item.get('tinie_layer_increments')}")
        if item.get("software_fc_library"):
            return (f"软件库 FC：TINIE_fullyConnected 调用 {item.get('tinie_fullyConnected_soft_calls')}，"
                    f"日志 FC[X]={item.get('log_fc_offloaded')}（不能当作硬件卸载）")
        if item.get("cpu_generated_fc") or item.get("returncode") == 0:
            return (f"CPU 生成：日志 FC[X]={item.get('log_fc_offloaded')}，"
                    f"FC[ ]={item.get('log_fc_cpu')}，NHWC={item.get('tinie_fullyConnectedNHWC')}")
        return f"编译失败 returncode={item.get('returncode')}"

    hw_any = any(item.get("hardware_fc_mapped") for item in phase3_data["compiles"])
    fp32_ok = all(item.get("fp32_equivalent") for item in phase1_data["candidates"])
    pwm_ok = all(item.get("official_90_140_step_0_1", {}).get("within_one_pwm") for item in phase2_data["candidates"])
    worth = hw_any and fp32_ok and pwm_ok
    if hw_any and fp32_ok and not pwm_ok:
        verdict = (
            "不建议进入控制闭环的实机性能对照。原始 3-29-12-6-4 的 FP32 功能可以保持，"
            "但量化后 PWM 计数误差仍不满足一个计数目标。若 TI 确认 FORCE_NO_TI_C28_SOFT_OFFLOAD "
            "可用于量产，才值得单独做 FC 与 PWCONV 的延迟微基准；默认 C28 路径是软件 FC。"
        )
    elif worth:
        verdict = "可以进入下一轮实机性能对照：硬件 FC 映射已证实，且量化精度满足一个 PWM 计数。"
    elif not hw_any:
        verdict = (
            "不进入下一轮实机性能对照。尚未证明四层 FC 在 F28P550 上按预期卸载到 NPU 硬件；"
            "日志里的 FC [X] 或 TVMGEN_DEFAULT_TI_NPU 宏都不足以作为硬件证据。"
        )
    else:
        verdict = "不进入下一轮实机性能对照：硬件映射或原始网络数学等价条件未同时满足。"

    lines = [
        "# F28P550 NPU：基于原始 3-29-12-6-4 的 FC 算子映射实验报告",
        "",
        "日期：2026-10-30。Teacher 仅为 `dab_nn.c` 中的 FPU 网络 3→29→12→6→4，输出顺序 `[D1,D0,D2,T]`。",
        "未重新训练，未改有效权重/偏置/激活。产物隔离在 `model/experiments/fc/`。",
        "未覆盖 `model/generated/npu`，未改 CCS 正式配置，未烧录，未放开功率保护。",
        "",
        "## 1. NNC 2.1.1 对 FC 的实际支持",
        "",
        "官方 NPU 层表（`layer_configs_npu`）：",
        "",
        "- INT8 权重（kB=8）：输入维度 `iC = m1b16`，即至少 16；输出 `oC` 无上限。",
        "- INT4 权重（kB=4）：输入维度 `iC = m1b8`，即至少 8；输出 `oC` 无上限。",
        "- 无 2-bit FC 配置。参数缓冲 2048 字节，无 host post-process 时 iC 上限 2032。",
        "",
        "ONNX 模式是 `MatMul => BNORM`（bias → scale → 右移 → Floor → Clip）。ReLU **不在** FC 融合模式里。",
        "`config_fc.py` 对 INT8 的 `iC<16`、INT4 的 `iC<8` 给出 WARNING，硬件检查失败后该层不会走 NHWC 微码。",
        "",
        "C28 默认（`tinie.py`）：即使 target 是 `ti-npu` hard，FC 也注册为 `TINIE_fullyConnected`（软件/DMAC 库），",
        "而不是 `TINIE_fullyConnectedNHWC`。后者只在环境变量 `FORCE_NO_TI_C28_SOFT_OFFLOAD=true` 时启用，",
        "源码注释写明这是 TI 内部测试开关，不是量产路径。",
        "",
        "因此：**编译成功、生成 NPU 宏、日志出现 `FC [X]`，都不能证明硬件 FC。**",
        "本实验以 `TINIE_fullyConnectedNHWC` + `FC_*_INS` + `tinie_curr_layer += 1` 作为硬件映射判据。",
        "",
        "最小模型编译：",
        "",
    ]
    for job, item in p0.items():
        lines.append(f"- `{job}`：{mapping_line(item)}。警告：{item.get('iC_warnings') or '无'}。")
    lines += [
        "",
        "## 2. INT8 / INT4 最终网络结构",
        "",
        "全部从原始 3-29-12-6-4 复制有效权重和偏置；新增输入列、新增输出神经元的权重和偏置严格为 0。",
        "输入语义保持 `[-0.5, Vin/140, 0.285714]`，后面补零。不做 Vin 仿射折叠，不改激活。",
        "",
        "| 候选 | 结构 | MAC | 运行时 Pad | 输入补零 |",
        "|---|---|---:|---:|---:|",
    ]
    for name in CANDIDATES:
        item = p1[name]
        lines.append(
            f"| `{name}` | {'→'.join(str(v) for v in item['structure'])} | "
            f"{item['macs']} | {item['runtime_pad_ops']} | {item['input_zero_pad']} |"
        )
    lines += [
        "",
        f"原始 FPU MAC = {ORIGINAL_MACS}。现网 PWCONV 4→32→12→8→4 MAC = {PWCONV_MACS}。",
        "",
        "## 3. 输入补零 vs 输出零神经元",
        "",
        "输入补零方案只把不够硬件下限的那一层 pad 到 16（INT8）或 8（INT4），中间已满足下限的层保持原始宽度。",
        "零神经元方案把后续层的输出加全零通道，使下一层输入天然够宽，避免中间 Pad 算子。",
        "INT8 零神经元 MAC 明显高于输入补零（多了 29→16 与 16→16）；INT4 两种方案 MAC 接近。",
        "不能预先认定谁更快：Pad 可能落 CPU，零神经元增加 MAC 和参数，硬件 FC 还有逐层装载/ISR。",
        "",
        "## 4. FP32 等价性",
        "",
    ]
    for name, item in p1.items():
        lines.append(
            f"- `{name}`：max abs {fmt_list(item['fp32_max_abs'], 3)}，"
            f"额外神经元 max abs {item['extra_neuron_max_abs']:.3g}，"
            f"等价={item['fp32_equivalent']}，额外输出为零={item['extra_neurons_zero']}。"
        )
    lines += ["", "## 5. INT8 / INT4 量化精度（相对原始 FPU Teacher）", ""]
    for name, item in p2.items():
        official = item["official_90_140_step_0_1"]
        dense = item["dense_92_2_92_5"]
        lines.append(
            f"- `{name}` 官方 90–140 V / 0.1 V：max abs {fmt_list(official['max_abs'])}，"
            f"最大 PWM 计数 {official['max_pwm_count']} "
            f"(T {official['pwm_tbprd_max']} / D1 {official['pwm_cmpA2_max']} / "
            f"D2 {official['pwm_cmpA4_max']} / D0 {official['pwm_phase34_max']})，"
            f"非法输出 {official['invalid_count']} 个，最差点 Vin={official['worst_pwm_vin']} V。"
        )
        lines.append(
            f"  加密 92.2–92.5 V：max abs {fmt_list(dense['max_abs'])}，"
            f"最大 PWM {dense['max_pwm_count']}，非法 {dense['invalid_count']}。"
        )
        lines.append(f"  ONNX 算子：{item['graph']['ops']}。")
    lines += [
        "",
        "判据是逐维最大绝对误差、PWM 计数误差和非法控制量，不只看 MSE。",
        "隐藏层仍是 ReLU；FC 模式不含 ReLU，ReLU 若未融入 Clip 就会留在 CPU。",
        "",
        "## 6. 四层硬件卸载与 CPU fallback",
        "",
    ]
    for job, item in p3.items():
        lines.append(
            f"- `{job}`：{mapping_line(item)}。"
            f" 宏 TI_NPU={item.get('header_ti_npu')}，TI_NPU_SOFT={item.get('header_ti_npu_soft')}。"
            f" Relu CPU={item.get('log_relu_cpu')}，Pad 卸载={item.get('log_pad_offloaded')} / CPU={item.get('log_pad_cpu')}。"
            f" host post-process={item.get('host_postproc')}。"
        )
        if item.get("file_bytes"):
            lines.append(f"  生成规模：{item['file_bytes']}。")
    lines += [
        "",
        "## 7. 参数、指令规模与运行时开销",
        "",
        "硬件 FC 若映射成功，仍会像当前 PWCONV 一样按层装载 PARAMS/INS 并依赖 `tinie_curr_layer` ISR 推进。",
        "默认 C28 软件 FC 没有这套 NPU 装载，但是 CPU/DMAC 库，不是 NPU 阵列。",
        "ReLU 与（若存在的）Pad/Concat 很可能夹在四层 FC 之间，形成 CPU 间隙。",
        "",
        "## 8. 与现有 PWCONV 对照",
        "",
        f"| 项目 | 原始 FPU | 本轮 INT8 pad | 本轮 INT8 零神经元 | 本轮 INT4 pad | 现网 PWCONV |",
        f"|---|---|---|---|---|---|",
        f"| 结构 | 3-29-12-6-4 | { '→'.join(str(v) for v in p1['int8_input_pad']['structure']) } | "
        f"{ '→'.join(str(v) for v in p1['int8_zero_neuron']['structure']) } | "
        f"{ '→'.join(str(v) for v in p1['int4_input_pad']['structure']) } | 4-32-12-8-4 |",
        f"| MAC | {ORIGINAL_MACS} | {p1['int8_input_pad']['macs']} | {p1['int8_zero_neuron']['macs']} | "
        f"{p1['int4_input_pad']['macs']} | {PWCONV_MACS} |",
        f"| 算子 | FPU GEMM | MatMul/FC | MatMul/FC | MatMul/FC | 1x1 PWCONV |",
        "",
    ]
    live = phase3_data.get("pwconv_live") or {}
    if live:
        lines.append(
            f"现网 PWCONV 生成代码：`tinie_curr_layer += 1` × {live.get('tinie_layer_increments')}，"
            f"lib2 {live.get('lib2_bytes')} 字节，mod.a {live.get('mod_a_bytes')} 字节。"
        )
    lines += [
        "",
        "## 9. 是否进入下一轮实机性能测试",
        "",
        verdict,
        "",
        "隔离记录：正式 `mod.a` / `manifest.json` / FPU 固件未改；无独立 CCS 链接配置（避免污染现有 FLASH/NPU_FLASH）；",
        "本轮编译器入口是 `model/experiments/fc/compile_fc_npu.py`。",
    ]
    path = out / "FC_mapping_campaign_20261030_zh.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE)
    parser.add_argument("--phase", choices=("0", "1", "2", "3", "all"), default="all")
    args = parser.parse_args()
    out = args.out.resolve()
    live = (APP / "model/generated/npu").resolve()
    if out == live or live in out.parents:
        raise RuntimeError("refusing to use the live NPU directory")
    (out / "onnx").mkdir(parents=True, exist_ok=True)
    (out / "generated").mkdir(parents=True, exist_ok=True)
    (out / "results").mkdir(parents=True, exist_ok=True)
    if not NNC_PY.exists():
        raise RuntimeError(f"missing NNC python: {NNC_PY}")
    weights = load_weights(NN_C)
    shapes = {f"w{i}": int(weights[f"w{i}"].size) for i in range(1, 5)}
    expected_w = {"w1": 87, "w2": 348, "w3": 72, "w4": 24}
    if shapes != expected_w:
        raise RuntimeError(f"dab_nn.c is not 3-29-12-6-4, got {shapes}")
    phase0_data = phase1_data = phase2_data = phase3_data = None
    if args.phase in ("0", "all"):
        phase0_data = phase0(out)
    if args.phase in ("1", "all"):
        phase1_data = phase1(weights, out)
    if args.phase in ("2", "all"):
        phase2_data = phase2(weights, out)
    if args.phase in ("3", "all"):
        if args.phase == "3":
            phase1_data = json.loads((out / "results/phase1.json").read_text(encoding="utf-8"))
            phase2_data = json.loads((out / "results/phase2.json").read_text(encoding="utf-8"))
        phase3_data = phase3(out)
    if args.phase == "all":
        report = write_report(out, phase0_data, phase1_data, phase2_data, phase3_data)
        print(report)
    print(json.dumps({
        "phase": args.phase,
        "out": str(out),
        "original_macs": ORIGINAL_MACS,
        "pwconv_macs": PWCONV_MACS,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
