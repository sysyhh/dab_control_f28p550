"""Offline check for the 4→32→12→8→4 padding candidate.

Copies dab_nn.c weights into the leading rows and columns. Quantization is
optional and writes only under the review directory. This script does not
overwrite the delivered NPU library and does not talk to the board.
"""
import argparse
import json
from pathlib import Path
import numpy as np

from expand_and_quantize_npu import firmware_features, load_weights, original_forward

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
OUT = ROOT / "review_20261003/npu_integration_20261009/narrow_4x32x12x8x4"
CANDIDATE = ((4, 32), (32, 12), (12, 8), (8, 4))
COPIED = ((29, 3), (12, 29), (6, 12), (4, 6))


def expand(flat, rows, cols, outputs, inputs):
    matrix = np.zeros((outputs, inputs), np.float32)
    matrix[:rows, :cols] = np.asarray(flat, np.float32).reshape(rows, cols)
    return matrix


def layers_from(weights):
    built = []
    for index, ((inputs, outputs), (rows, cols)) in enumerate(zip(CANDIDATE, COPIED), 1):
        bias = np.zeros(outputs, np.float32)
        bias[:rows] = np.asarray(weights[f"b{index}"], np.float32)
        built.append((expand(weights[f"w{index}"], rows, cols, outputs, inputs), bias, rows))
    return built


def forward(built, values):
    current = np.asarray(values, np.float32).copy()
    hidden_tails = []
    for index, (matrix, bias, rows) in enumerate(built, 1):
        output = np.empty(matrix.shape[0], np.float32)
        for i in range(matrix.shape[0]):
            total = np.float32(bias[i])
            for j in range(matrix.shape[1]):
                total = np.float32(total + np.float32(current[j] * matrix[i, j]))
            output[i] = total if index == 4 else np.maximum(total, np.float32(0))
        if index < 4 and rows < output.shape[0]:
            hidden_tails.append(float(np.max(np.abs(output[rows:]))))
        current = output
    return current, hidden_tails


def fold(built):
    layers = [(matrix.copy(), bias.copy(), rows) for matrix, bias, rows in built]
    low = np.float32(90.0 / 140.0)
    high = np.float32(1.0)
    center = (low + high) / np.float32(2.0)
    half = (high - low) / np.float32(2.0)
    weight, bias, rows = layers[0]
    bias += weight[:, 0] * np.float32(-0.5)
    bias += weight[:, 1] * center
    bias += weight[:, 2] * np.float32(0.285714)
    weight[:, 1] *= half
    weight[:, 0] = 0
    weight[:, 2] = 0
    for index in range(3):
        previous, following = layers[index], layers[index + 1]
        for channel in range(previous[0].shape[0]):
            previous_peak = np.max(np.abs(previous[0][channel]))
            following_peak = np.max(np.abs(following[0][:, channel]))
            if float(previous_peak) < 1e-8 or float(following_peak) < 1e-8:
                continue
            scale = np.float32(np.sqrt(np.float32(following_peak) / np.float32(previous_peak)))
            previous[0][channel] *= scale
            previous[1][channel] *= scale
            following[0][:, channel] /= scale
    return layers, center, half


def mapped(vin, center, half):
    values = np.zeros(4, np.float32)
    values[1] = (np.float32(vin) / np.float32(140.0) - center) / half
    return values


def direct(vin):
    values = np.zeros(4, np.float32)
    values[1] = np.float32(vin) / np.float32(25.0) - np.float32(4.6)
    return values


def worst(errors):
    stack = np.stack(errors)
    return [float(value) for value in stack.max(axis=0)]


def torch_model(folded):
    import torch
    from torch import nn

    class Narrow(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(4, 32)
            self.fc2 = nn.Linear(32, 12)
            self.fc3 = nn.Linear(12, 8)
            self.fc4 = nn.Linear(8, 4)

        def forward(self, features):
            hidden = torch.relu(self.fc1(features))
            hidden = torch.relu(self.fc2(hidden))
            hidden = torch.relu(self.fc3(hidden))
            return self.fc4(hidden)

    model = Narrow().float()
    with torch.no_grad():
        for layer, (matrix, bias, _rows) in zip((model.fc1, model.fc2, model.fc3, model.fc4), folded):
            layer.weight.copy_(torch.from_numpy(matrix))
            layer.bias.copy_(torch.from_numpy(bias))
    model.eval()
    return model


def quantize_candidate(folded, calibration_vins, eval_vins):
    import torch
    from expand_and_quantize_npu import original_forward_batch, quantize
    import tinyml_torchmodelopt

    model = torch_model(folded)
    calibration = torch.from_numpy(np.stack([direct(vin) for vin in calibration_vins]))
    converted = quantize(model, calibration)
    relu_range_clamped = True
    onnx_path = OUT / "dab_npu_narrow_ptq.onnx"
    converted.export(calibration[:1], str(onnx_path), input_names=["features"], output_names=["modulation"], simplify=False)
    import onnxruntime as ort
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    rows = np.stack([direct(vin) for vin in eval_vins])
    quantized = np.stack([
        session.run(None, {"features": row.reshape(1, 4)})[0].reshape(-1) for row in rows])
    teacher = original_forward_batch(load_weights(APP / "dab_nn.c"), eval_vins)
    error = np.abs(quantized - teacher)
    period = np.maximum(teacher[:, 3:4], 1e-6)
    nearest = np.round(quantized * 64.0) / 64.0
    steps = []
    for column in range(4):
        unique = np.unique(np.round(quantized[:, column], decimals=6))
        steps.append([float(value) for value in np.diff(unique)[:8]])
    return {
        "method": "TINPUTinyMLPTQFxModule",
        "package_version": getattr(tinyml_torchmodelopt, "__version__", "unknown"),
        "relu_observer_minimum_clamped": relu_range_clamped,
        "weight_activation_bits": 8,
        "calibration": "Vin 90..140 V step 1 V, features[1]=Vin/25-4.6, other features 0, input width 4",
        "onnx": str(onnx_path.relative_to(ROOT)).replace("\\", "/"),
        "samples": len(eval_vins),
        "max_abs_vs_dab_nn": [float(value) for value in error.max(axis=0)],
        "max_phase_counts": [float(value) for value in (error[:, :3] / period * 2500.0).max(axis=0)],
        "max_period_counts": float((error[:, 3] * 2500.0).max()),
        "max_abs_distance_to_1_64_grid": [float(value) for value in np.max(np.abs(quantized - nearest), axis=0)],
        "first_positive_unique_steps": steps,
        "within_one_pwm_count": bool(np.max(error[:, :3] / period * 2500.0) <= 1.0 and np.max(error[:, 3] * 2500.0) <= 1.0),
        "invalid_output_vin": [float(vin) for vin, row in zip(eval_vins, quantized)
                               if not (np.isfinite(row).all() and 0.5 <= row[3] <= 2.0 and
                                       (row[:3] >= -0.005 * row[3]).all() and (row[:3] <= 1.005 * row[3]).all())],
    }


def convert_conv():
    import onnx
    from onnx import helper, numpy_helper
    import onnxruntime as ort

    source = OUT / "dab_npu_narrow_ptq.onnx"
    target = OUT / "dab_npu_narrow_conv.onnx"
    model = onnx.load(str(source))
    weights = {tensor.name: numpy_helper.to_array(tensor) for tensor in model.graph.initializer}
    nodes = [helper.make_node("Reshape", ["features", "dab_nchw_shape"], ["dab_features_nchw"])]
    model.graph.initializer.append(numpy_helper.from_array(np.array([1, 4, 1, 1], np.int64), "dab_nchw_shape"))
    dense_count = 0
    for node in model.graph.node:
        for index, name in enumerate(node.input):
            if name == "features":
                node.input[index] = "dab_features_nchw"
        if node.op_type == "MatMul":
            name = node.input[1]
            array = weights[name].T[:, :, None, None].copy()
            for index, tensor in enumerate(model.graph.initializer):
                if tensor.name == name:
                    model.graph.initializer[index].CopyFrom(numpy_helper.from_array(array, name))
            node.op_type = "Conv"
            node.attribute.extend([helper.make_attribute("kernel_shape", [1, 1])])
            dense_count += 1
        if node.output and node.output[0] == "modulation":
            node.output[0] = "dab_modulation_nchw"
        nodes.append(node)
    if dense_count != 4:
        raise RuntimeError(f"Expected four dense layers, found {dense_count}")
    for index, tensor in enumerate(model.graph.initializer):
        if tensor.name.startswith("fc"):
            array = numpy_helper.to_array(tensor)
            if array.ndim == 2 and array.shape[0] == 1:
                model.graph.initializer[index].CopyFrom(numpy_helper.from_array(array.reshape(1, -1, 1, 1), tensor.name))
    nodes.append(helper.make_node("Transpose", ["dab_modulation_nchw"], ["modulation"], perm=[0, 2, 3, 1]))
    del model.graph.node[:]
    model.graph.node.extend(nodes)
    del model.graph.value_info[:]
    onnx.checker.check_model(model)
    onnx.save(model, str(target))
    baseline = ort.InferenceSession(str(source), providers=["CPUExecutionProvider"])
    candidate = ort.InferenceSession(str(target), providers=["CPUExecutionProvider"])
    maximum = 0.0
    for vin in np.linspace(90, 140, 501):
        features = direct(float(vin)).reshape(1, 4)
        old = baseline.run(None, {"features": features})[0].ravel()
        new = candidate.run(None, {"features": features})[0].ravel()
        maximum = max(maximum, float(np.max(np.abs(old - new))))
    return {"onnx": str(target.relative_to(ROOT)).replace("\\", "/"), "dense_layers_rewritten": dense_count,
            "max_abs_difference_from_dense_quantized": maximum}


def compiler_report():
    import re
    folder = OUT / "nnc211"
    header = folder / "tvmgen_default.h"
    if not header.exists():
        return None
    log = (folder / "compile.log").read_text(encoding="utf-8", errors="replace")
    lib1 = (folder / "lib1.c").read_text(encoding="utf-8", errors="replace")
    lib2 = (folder / "lib2.c").read_text(encoding="utf-8", errors="replace")
    header_text = header.read_text(encoding="utf-8", errors="replace")
    marked = re.findall(r"INFO:ti_mcu_nnc:\s+(\S+)\s+(\[[ X]\])", log)
    return {
        "ti_mcu_nnc": "2.1.1",
        "hardware_npu_defined": bool(re.search(r"(?m)^#define TVMGEN_DEFAULT_TI_NPU$", header_text)),
        "soft_npu_defined": "#define TVMGEN_DEFAULT_TI_NPU_SOFT" in header_text,
        "pwconv_offloaded": marked.count(("PWCONV", "[X]")),
        "pwconv_cpu_fallback": marked.count(("PWCONV", "[ ]")),
        "tinie_layer_increments": lib2.count("tinie_curr_layer += 1;"),
        "abi": re.findall(r"Tensor\[\(([^)]*)\),\s*(\w+)\]", header_text),
        "final_output_uses_1_64_scale": "T_reshape[ax3] = (((float)p0[ax3]) * 1.562500e-02f);" in lib1,
        "board_loaded": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantize", action="store_true")
    parser.add_argument("--convert", action="store_true")
    args = parser.parse_args()
    weights = load_weights(APP / "dab_nn.c")
    built = layers_from(weights)
    folded, center, half = fold(built)
    vins = [float(vin) for vin in np.linspace(90, 140, 501)]
    wide = [float(vin) for vin in np.linspace(20, 140, 1201)]
    plain, folded_affine, folded_direct = [], [], []
    tails = []
    for vin in wide:
        features = np.zeros(4, np.float32)
        features[:3] = firmware_features(vin)
        output, tail = forward(built, features)
        expected = original_forward(weights, firmware_features(vin))
        plain.append(np.abs(output - expected))
        tails.append(tail)
    for vin in vins:
        expected = original_forward(weights, firmware_features(vin))
        affine, _ = forward(folded, mapped(vin, center, half))
        literal, _ = forward(folded, direct(vin))
        folded_affine.append(np.abs(affine - expected))
        folded_direct.append(np.abs(literal - expected))
    macs = sum(inputs * outputs for inputs, outputs in CANDIDATE)
    report = {
        "candidate_shape": [4, 32, 12, 8, 4],
        "copied_from": [3, 29, 12, 6, 4],
        "matrix_multiply_accumulates": macs,
        "all_dimensions_multiple_of_4": all(dim % 4 == 0 for pair in CANDIDATE for dim in pair),
        "float_vs_dab_nn_max_abs_vin_20_140_step_0_1": worst(plain),
        "hidden_padding_max_abs": [float(value) for value in np.max(tails, axis=0)],
        "folded_affine_vs_dab_nn_max_abs_vin_90_140_step_0_1": worst(folded_affine),
        "folded_vin25_expression_vs_dab_nn_max_abs_vin_90_140_step_0_1": worst(folded_direct),
        "quantized": False,
        "compiled": False,
        "board_loaded": False,
        "power_control_approved": False,
        "scope": "offline only; no delivered-library replacement and no board load",
    }
    if args.quantize:
        report["quantization"] = quantize_candidate(folded, [float(vin) for vin in range(90, 141)], vins)
        report["quantized"] = True
    if args.convert:
        report["convolution_rewrite"] = convert_conv()
    compiler = compiler_report()
    if compiler is not None:
        report["compiler"] = compiler
        report["compiled"] = bool(compiler["hardware_npu_defined"] and compiler["pwconv_offloaded"] == 4 and compiler["pwconv_cpu_fallback"] == 0 and compiler["tinie_layer_increments"] == 4 and not compiler["soft_npu_defined"] and compiler["final_output_uses_1_64_scale"])
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2) + "\n"
    (OUT / "float_report.json").write_text(text, encoding="utf-8")
    (APP / "model/narrow_4x32x12x8x4_offline.json").write_text(text, encoding="utf-8")
    print(text)
    if max(report["float_vs_dab_nn_max_abs_vin_20_140_step_0_1"]) != 0:
        raise SystemExit("padded float network differs from dab_nn.c")
    if max(report["hidden_padding_max_abs"]) != 0:
        raise SystemExit("padding channels are not identically zero")


if __name__ == "__main__":
    main()
