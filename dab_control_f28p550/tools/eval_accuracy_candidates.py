"""Offline accuracy candidates: quant-config, QAT, and hybrid last-layer FPU.

Writes only under tools/c2000_debug/experiments/accuracy_20261030. Never replaces
model/generated/npu or the delivered mod.a. Does not enable power output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_int8_error import (
    NAMES, compact_float, firmware_pwm, mapped_vin, nn_valid, pwm_error, sha, teacher,
)
from check_narrow_npu_candidate import fold, layers_from, torch_model
from expand_and_quantize_npu import load_weights, original_forward_batch, quantize, tighten_prelu_ranges

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
OUT = ROOT / "tools/c2000_debug/experiments/accuracy_20261030"
PTQ = APP / "model/dab_npu_narrow_ptq.onnx"


def vins_official():
    return [round(90.0 + 0.1 * i, 1) for i in range(501)]


def vins_holdout():
    return [round(90.05 + 0.1 * i, 2) for i in range(500)]


def mapped_tensor(vins):
    return torch.from_numpy(np.stack([mapped_vin(vin) for vin in vins]))


def metrics(predicted, expected):
    predicted = np.asarray(predicted, np.float32)
    expected = np.asarray(expected, np.float32)
    error = np.abs(predicted - expected)
    pwm = [pwm_error(expected[i], predicted[i])["max_count"] for i in range(len(expected))]
    invalid = [i for i, row in enumerate(predicted) if not nn_valid(row)]
    return {
        "max_abs": [float(v) for v in error.max(axis=0)],
        "mean_abs": [float(v) for v in error.mean(axis=0)],
        "max_pwm_count": int(max(pwm)),
        "mean_pwm_count": float(np.mean(pwm)),
        "within_one_pwm": bool(max(pwm) <= 1),
        "invalid_count": len(invalid),
        "invalid_index_sample": invalid[:8],
    }


def export_quantized(converted, example, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    converted.export(example, str(path), input_names=["features"], output_names=["modulation"], simplify=False)
    return path


def onnx_predict(path: Path, vins):
    import onnxruntime as ort
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name
    rows = []
    for vin in vins:
        rows.append(session.run(None, {name: mapped_vin(vin).reshape(1, 4)})[0].reshape(-1))
    return np.stack(rows)


def route_a_output_scale_override():
    """Keep TINPU PTQ, but force a smaller unified output scale after observers.

    TI NPU activations are per-tensor power-of-two. A smaller scale only helps if
    every output still fits in int8. T around 1.15 forbids 1/128 as a unified scale.
    """
    from tinyml_torchmodelopt.quantization.common import TinyMLQConfigType
    from tinyml_torchmodelopt.quantization import TINPUTinyMLPTQFxModule

    weights = load_weights(APP / "dab_nn.c")
    model = torch_model(fold(layers_from(weights))[0])
    calibration = mapped_tensor(list(range(90, 141)))
    qconfig = TinyMLQConfigType(weight_bitwidth=8, activation_bitwidth=8, auto_quantization=False)
    wrapped = TINPUTinyMLPTQFxModule(
        model, total_epochs=1, qconfig_type=qconfig, example_inputs=calibration[:1].contiguous(),
        output_int=False, num_observer_update_epochs=False, num_batch_norm_update_epochs=False)
    wrapped.train()
    with torch.no_grad():
        wrapped(calibration)
    tighten_prelu_ranges(wrapped)
    return wrapped


def inspect_qconfig_support():
    from tinyml_torchmodelopt.quantization.common import TinyMLQConfigType
    cfg = TinyMLQConfigType(weight_bitwidth=8, activation_bitwidth=8, auto_quantization=False)
    return {
        "weight_qscheme": str(cfg.qconfig_type["weight"]["qscheme"]),
        "activation_qscheme": str(cfg.qconfig_type["activation"]["qscheme"]),
        "weight_power2": cfg.qconfig_type["weight"]["power2_scale"],
        "activation_power2": cfg.qconfig_type["activation"]["power2_scale"],
        "npu_kernel_note": (
            "TINPU default is per-channel weights and per-tensor activations, both power-of-two. "
            "Generated C for this model dequantizes all four outputs with 1/64. "
            "A per-channel output scale is not present in the delivered NNC 2.1.1 PWCONV path."
        ),
    }


def route_a(weights, folded, expected_official, expected_holdout):
    model = torch_model(folded)
    official = vins_official()
    holdout = vins_holdout()
    variants = {
        "ptq_step1V": list(range(90, 141)),
        "ptq_step0_1V": official,
        "ptq_step0_1V_plus_dense_92": official + [round(92.20 + 0.01 * i, 2) for i in range(31)],
    }
    results = {"qconfig": inspect_qconfig_support(), "variants": {}}
    for name, calibration_vins in variants.items():
        converted = quantize(model, mapped_tensor(calibration_vins))
        path = OUT / "candidates" / f"{name}.onnx"
        export_quantized(converted, mapped_tensor(calibration_vins[:1]), path)
        predicted = onnx_predict(path, official)
        hold = onnx_predict(path, holdout)
        results["variants"][name] = {
            "onnx": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha(path),
            "official": metrics(predicted, expected_official),
            "holdout": metrics(hold, expected_holdout),
        }
    t_max = float(np.max(np.abs(expected_official[:, 3])))
    d_max = [float(np.max(np.abs(expected_official[:, i]))) for i in range(4)]
    unified_128_ok = t_max <= 127 / 128.0
    results["unified_output_scale"] = {
        "teacher_abs_max": dict(zip(NAMES, d_max)),
        "int8_range_at_1_64": 127 / 64.0,
        "int8_range_at_1_128": 127 / 128.0,
        "unified_1_128_fits_T": unified_128_ok,
        "per_channel_needed_scale": {
            name: float(2 ** np.ceil(np.log2(max(peak / 127.0, 1e-12))))
            for name, peak in zip(NAMES, d_max)
        },
    }
    return results


def route_b(weights, folded, expected_official, expected_holdout):
    from tinyml_torchmodelopt.quantization.common import TinyMLQConfigType
    from tinyml_torchmodelopt.quantization import TINPUTinyMLQATFxModule

    model = torch_model(folded)
    train_vins = vins_official()
    x = mapped_tensor(train_vins)
    y = torch.from_numpy(np.stack([teacher(weights, vin) for vin in train_vins]))
    qconfig = TinyMLQConfigType(weight_bitwidth=8, activation_bitwidth=8, auto_quantization=False)
    wrapped = TINPUTinyMLQATFxModule(
        model, total_epochs=40, qconfig_type=qconfig, example_inputs=x[:1].contiguous(),
        output_int=False, num_observer_update_epochs=False, num_batch_norm_update_epochs=False)
    wrapped.train()
    optimizer = torch.optim.Adam(wrapped.parameters(), lr=1e-3)
    loss_curve = []
    for epoch in range(40):
        optimizer.zero_grad()
        predicted = wrapped(x)
        loss = torch.mean((predicted - y) ** 2)
        loss.backward()
        optimizer.step()
        loss_curve.append(float(loss.detach()))
    tighten_prelu_ranges(wrapped)
    wrapped.freeze(freeze_bn=True, freeze_observers=True)
    converted = wrapped.convert()
    path = OUT / "candidates" / "qat_teacher_distill.onnx"
    export_quantized(converted, x[:1], path)
    official = onnx_predict(path, vins_official())
    holdout = onnx_predict(path, vins_holdout())
    return {
        "onnx": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha(path),
        "epochs": 40,
        "final_mse": loss_curve[-1],
        "loss_start": loss_curve[0],
        "official": metrics(official, expected_official),
        "holdout": metrics(holdout, expected_holdout),
        "generalization_gap_max_abs": [
            float(a - b) for a, b in zip(
                metrics(holdout, expected_holdout)["max_abs"],
                metrics(official, expected_official)["max_abs"])
        ],
    }


def route_c(weights, folded, expected_official):
    import onnx
    from onnx import helper
    import onnxruntime as ort

    model = onnx.load(str(PTQ))
    existing = {item.name for item in model.graph.output}
    if "/Relu_2_output_0" not in existing:
        model.graph.output.append(helper.make_tensor_value_info("/Relu_2_output_0", onnx.TensorProto.FLOAT, None))
    hidden_path = OUT / "candidates" / "hybrid_hidden_probe.onnx"
    hidden_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(hidden_path))
    session = ort.InferenceSession(str(hidden_path), providers=["CPUExecutionProvider"])
    outputs = [item.name for item in session.get_outputs()]
    relu3_index = outputs.index("/Relu_2_output_0")
    w4, b4, _rows = folded[3]
    hybrid = []
    int8_out = []
    hidden_err = []
    float_relu3 = []
    for vin in vins_official():
        blobs = session.run(None, {session.get_inputs()[0].name: mapped_vin(vin).reshape(1, 4)})
        int8_out.append(blobs[outputs.index("modulation")].reshape(-1))
        relu3 = blobs[relu3_index].reshape(-1).astype(np.float32)
        hybrid.append(b4.astype(np.float32) + w4.astype(np.float32) @ relu3)
        _y, traces = None, None
        from analyze_int8_error import dense_forward
        _y, traces = dense_forward([(m, b, r) for m, b, r in folded], mapped_vin(vin), None)
        float_relu3.append(traces[2]["post"])
        hidden_err.append(np.max(np.abs(relu3[:8] - traces[2]["post"][:8])))
    hybrid = np.stack(hybrid)
    int8_out = np.stack(int8_out)
    return {
        "hidden3_max_abs_vs_float": float(max(hidden_err)),
        "int8_full": metrics(int8_out, expected_official),
        "hybrid_float_last": metrics(hybrid, expected_official),
        "recovered_pwm_counts": int8_out is not None and (
            metrics(int8_out, expected_official)["max_pwm_count"]
            - metrics(hybrid, expected_official)["max_pwm_count"]
        ),
        "note": "Last-layer FPU cannot undo hidden INT8 clipping; it only avoids the 1/64 output grid.",
        "latency_note": (
            "Board hybrid compile is deferred until accuracy clears 1 PWM count. "
            "Estimate uses current NPU minus last-layer wait plus an 8x4 FPU GEMM."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-qat", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "candidates").mkdir(parents=True, exist_ok=True)
    weights = load_weights(APP / "dab_nn.c")
    folded, _c, _h = fold(layers_from(weights))
    expected_official = original_forward_batch(weights, vins_official())
    expected_holdout = original_forward_batch(weights, vins_holdout())
    current_int8 = onnx_predict(PTQ, vins_official())
    report = {
        "power_control_approved": False,
        "baselines": {
            "fpu_teacher": {"max_abs": [0, 0, 0, 0], "max_pwm_count": 0},
            "current_int8_npu": metrics(current_int8, expected_official),
            "compact_float": metrics(
                np.stack([compact_float(folded, vin) for vin in vins_official()]),
                expected_official),
        },
        "route_a_quant_config": route_a(weights, folded, expected_official, expected_holdout),
        "route_c_hybrid": route_c(weights, folded, expected_official),
    }
    if not args.skip_qat:
        report["route_b_qat"] = route_b(weights, folded, expected_official, expected_holdout)
    else:
        report["route_b_qat"] = "skipped"
    (OUT / "candidates_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "report": str(OUT / "candidates_report.json"),
        "current_int8": report["baselines"]["current_int8_npu"],
        "route_a_best": min(
            ((k, v["official"]["max_pwm_count"]) for k, v in report["route_a_quant_config"]["variants"].items()),
            key=lambda item: item[1]),
        "route_c": report["route_c_hybrid"]["hybrid_float_last"],
        "route_b": report["route_b_qat"]["official"] if isinstance(report["route_b_qat"], dict) else report["route_b_qat"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
