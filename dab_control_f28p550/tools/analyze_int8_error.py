"""Layer-wise INT8 error attribution against the FPU teacher in dab_nn.c.

Uses the compact 4->32->12->8->4 float network as the equivalence baseline and
the delivered narrow PTQ ONNX as the INT8 object. PWM counts follow dab_control.c
and dab_pwm.c at ramp=1, duty=0. Does not overwrite the delivered NPU library
and does not talk to the board.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_narrow_npu_candidate import COPIED, CANDIDATE, fold, forward, layers_from
from expand_and_quantize_npu import firmware_features, load_weights, original_forward

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
OUT = ROOT / "tools/c2000_debug/experiments/accuracy_20261030"
PTQ = APP / "model/dab_npu_narrow_ptq.onnx"
CONV = APP / "model/dab_npu_narrow_conv.onnx"
TBPRD = 2500.0
PHASE_TOL = 0.005
NAMES = ("D1", "D0", "D2", "T")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapped_vin(vin: float) -> np.ndarray:
    values = np.zeros(4, np.float32)
    values[1] = np.float32(vin) / np.float32(25.0) - np.float32(4.6)
    return values


def teacher(weights, vin: float) -> np.ndarray:
    return original_forward(weights, firmware_features(vin))


def compact_float(folded, vin: float) -> np.ndarray:
    return forward(folded, mapped_vin(vin))[0]


def nn_valid(output) -> bool:
    values = np.asarray(output, np.float32)
    if not np.isfinite(values).all():
        return False
    if values[3] < 0.5 or values[3] > 2.0:
        return False
    limit = PHASE_TOL * values[3]
    return bool(np.all(values[:3] >= -limit) and np.all(values[:3] <= (1.0 + PHASE_TOL) * values[3]))


def c_trunc_u32(value: float) -> int:
    return int(np.float32(value)) & 0xFFFFFFFF


def c_trunc_u16(value: float) -> int:
    return int(np.float32(value)) & 0xFFFF


def firmware_pwm(output, duty: float = 0.0, ramp: float = 1.0) -> dict:
    d1, d0, d2, period_gain = [float(np.float32(v)) for v in output]
    inv_t = 1.0 / period_gain
    duty = float(np.float32(duty))
    ramp = float(np.float32(ramp))

    def clamp(value, low, high):
        value = float(np.float32(value))
        if value < low:
            return low
        if value > high:
            return high
        return value

    d1_n = (1.0 - ramp) + ramp * clamp(d1 * inv_t - duty, 0.001, 0.999)
    d2_n = (1.0 - ramp) + ramp * clamp(d2 * inv_t - duty, 0.001, 0.999)
    d0_n = ramp * clamp(d0 * inv_t + duty, 0.0, 0.999)
    t_gain = 1.0 + ramp * (period_gain - 1.0)
    tbprd = c_trunc_u32(float(np.float32(t_gain) * np.float32(TBPRD)))
    period = tbprd & 0xFFFF
    return {
        "tbprd": period,
        "cmpA2": c_trunc_u16(float(np.float32(d1_n) * np.float32(period))),
        "cmpA4": c_trunc_u16(float(np.float32(d2_n) * np.float32(period))),
        "phase34": c_trunc_u16(float(np.float32(d0_n) * np.float32(period))),
        "D1": d1_n,
        "D0": d0_n,
        "D2": d2_n,
        "T_gain": t_gain,
        "clamped": {
            "D1": abs(d1 * inv_t - duty - d1_n) > 1e-12 and (d1_n in (0.001, 0.999) or ramp != 1.0),
            "D2": abs(d2 * inv_t - duty - d2_n) > 1e-12,
            "D0": abs(d0 * inv_t + duty - d0_n) > 1e-12,
        },
    }


def pwm_error(reference, candidate) -> dict:
    ref = firmware_pwm(reference)
    cand = firmware_pwm(candidate)
    return {
        "tbprd": abs(cand["tbprd"] - ref["tbprd"]),
        "cmpA2": abs(cand["cmpA2"] - ref["cmpA2"]),
        "cmpA4": abs(cand["cmpA4"] - ref["cmpA4"]),
        "phase34": abs(cand["phase34"] - ref["phase34"]),
        "max_count": max(
            abs(cand["tbprd"] - ref["tbprd"]),
            abs(cand["cmpA2"] - ref["cmpA2"]),
            abs(cand["cmpA4"] - ref["cmpA4"]),
            abs(cand["phase34"] - ref["phase34"]),
        ),
        "ref": ref,
        "cand": cand,
    }


def quantize_symmetric(values, scale: float, bits: int = 8):
    qmin, qmax = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    codes = np.floor(values / np.float32(scale) + np.float32(0.5))
    codes = np.clip(codes, qmin, qmax)
    clipped = (codes <= qmin) | (codes >= qmax)
    return codes.astype(np.float32) * np.float32(scale), codes, clipped


def ti_round_codes(values, scale: float):
    """Match TINPU floor((x + scale/2) / scale) used in the exported ONNX."""
    codes = np.floor(values / np.float32(scale) + np.float32(0.5))
    codes = np.clip(codes, -128, 127)
    return codes.astype(np.float32) * np.float32(scale), codes, (codes <= -128) | (codes >= 127)


def dense_forward(layers, features, quant=None):
    current = np.asarray(features, np.float32).copy()
    traces = []
    for index, (matrix, bias, _rows) in enumerate(layers, 1):
        pre = bias.astype(np.float32) + matrix.astype(np.float32) @ current
        post = pre if index == 4 else np.maximum(pre, np.float32(0))
        info = {"pre": pre.copy(), "post": post.copy(), "clipped": np.zeros(post.shape, bool)}
        if quant is not None:
            scale = quant[index - 1]
            if scale is not None:
                post, _codes, clipped = ti_round_codes(post, scale)
                info["post"] = post.copy()
                info["clipped"] = clipped
        traces.append(info)
        current = post
    return current, traces


def load_onnx_session(path: Path):
    import onnxruntime as ort
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def onnx_batch(session, vins):
    name = session.get_inputs()[0].name
    rows = []
    for vin in vins:
        features = mapped_vin(vin).reshape(1, -1)
        rows.append(session.run(None, {name: features})[0].reshape(-1).astype(np.float32))
    return np.stack(rows)


def add_hidden_outputs(source: Path, destination: Path):
    import onnx
    from onnx import helper
    model = onnx.load(str(source))
    existing = {item.name for item in model.graph.output}
    for name in ("/Relu_output_0", "/Relu_1_output_0", "/Relu_2_output_0", "modulation"):
        if name in existing:
            continue
        model.graph.output.append(helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None))
    onnx.save(model, str(destination))
    return destination


def summarize_abs(errors: np.ndarray) -> dict:
    return {
        "max": [float(v) for v in errors.max(axis=0)],
        "mean": [float(v) for v in errors.mean(axis=0)],
        "p95": [float(v) for v in np.quantile(errors, 0.95, axis=0)],
    }


def worst_rows(vins, errors, pwm_counts, valid, extra=None, limit=8):
    score = errors.max(axis=1)
    order = np.argsort(-score)
    rows = []
    for index in order[:limit]:
        item = {
            "vin": float(vins[index]),
            "abs": [float(v) for v in errors[index]],
            "pwm_max_count": int(pwm_counts[index]),
            "valid": bool(valid[index]),
        }
        if extra:
            item.update({key: extra[key][index] for key in extra})
        rows.append(item)
    return rows


def write_grid_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    weights = load_weights(APP / "dab_nn.c")
    folded, _center, _half = fold(layers_from(weights))
    float_layers = [(matrix.copy(), bias.copy(), rows) for matrix, bias, rows in folded]
    session = load_onnx_session(PTQ)
    hidden_onnx = add_hidden_outputs(PTQ, out / "dab_npu_narrow_ptq_hidden.onnx")
    hidden_session = load_onnx_session(hidden_onnx)

    official = [round(90.0 + 0.1 * i, 1) for i in range(501)]
    dense = [round(92.20 + 0.01 * i, 2) for i in range(31)]
    extra = [round(20.0 + 0.1 * i, 1) for i in range(1201)]

    teacher_official = np.stack([teacher(weights, vin) for vin in official])
    compact_official = np.stack([compact_float(folded, vin) for vin in official])
    int8_official = onnx_batch(session, official)
    compact_error = np.abs(compact_official - teacher_official)
    int8_error = np.abs(int8_official - teacher_official)

    output_scale = 1.0 / 64.0
    hidden_scales = (1.0 / 64.0, 1.0 / 128.0, 1.0 / 256.0, 1.0 / 64.0)
    ablations = {}
    ablation_pwm = {}
    for name, quant in (
        ("float_compact", (None, None, None, None)),
        ("output_quant_1_64_only", (None, None, None, output_scale)),
        ("hidden1_quant_1_64", (hidden_scales[0], None, None, None)),
        ("hidden2_quant_1_128", (None, hidden_scales[1], None, None)),
        ("hidden3_quant_1_256", (None, None, hidden_scales[2], None)),
        ("all_hidden_quant", (hidden_scales[0], hidden_scales[1], hidden_scales[2], None)),
        ("all_hidden_and_output_quant", hidden_scales),
        ("hybrid_int_hidden_float_last", (hidden_scales[0], hidden_scales[1], hidden_scales[2], None)),
    ):
        predicted = []
        clip_frac = [0.0, 0.0, 0.0, 0.0]
        for vin in official:
            output, traces = dense_forward(float_layers, mapped_vin(vin), quant)
            predicted.append(output)
            for layer, trace in enumerate(traces):
                clip_frac[layer] += float(np.mean(trace["clipped"]))
        predicted = np.stack(predicted)
        errors = np.abs(predicted - teacher_official)
        pwm = [pwm_error(teacher_official[i], predicted[i])["max_count"] for i in range(len(official))]
        ablations[name] = {
            "max_abs": [float(v) for v in errors.max(axis=0)],
            "clip_fraction": [value / len(official) for value in clip_frac],
            "max_pwm_count": int(max(pwm)),
            "invalid_count": int(sum(not nn_valid(row) for row in predicted)),
        }
        ablation_pwm[name] = pwm

    hybrid = []
    hidden_name = hidden_session.get_inputs()[0].name
    hidden_outputs = [item.name for item in hidden_session.get_outputs()]
    relu3_index = hidden_outputs.index("/Relu_2_output_0")
    w4, b4, _rows = float_layers[3]
    for vin in official:
        features = mapped_vin(vin).reshape(1, -1)
        blobs = hidden_session.run(None, {hidden_name: features})
        relu3 = blobs[relu3_index].reshape(-1).astype(np.float32)
        hybrid.append(b4.astype(np.float32) + w4.astype(np.float32) @ relu3)
    hybrid = np.stack(hybrid)
    hybrid_error = np.abs(hybrid - teacher_official)
    hybrid_pwm = [pwm_error(teacher_official[i], hybrid[i])["max_count"] for i in range(len(official))]
    ablations["hybrid_onnx_hidden_float_last"] = {
        "max_abs": [float(v) for v in hybrid_error.max(axis=0)],
        "max_pwm_count": int(max(hybrid_pwm)),
        "invalid_count": int(sum(not nn_valid(row) for row in hybrid)),
        "note": "INT8 ONNX hidden ReLU3, original folded float last layer; hidden quant error remains",
    }

    ranges = {
        "teacher": {
            name: {"min": float(teacher_official[:, i].min()), "max": float(teacher_official[:, i].max()),
                   "span": float(teacher_official[:, i].max() - teacher_official[:, i].min())}
            for i, name in enumerate(NAMES)
        },
        "int8": {
            name: {"min": float(int8_official[:, i].min()), "max": float(int8_official[:, i].max()),
                   "span": float(int8_official[:, i].max() - int8_official[:, i].min()),
                   "unique_codes": int(len(np.unique(np.round(int8_official[:, i] / output_scale))))}
            for i, name in enumerate(NAMES)
        },
        "unified_output_scale": output_scale,
        "int8_output_range": 127 * output_scale,
        "needed_scale_for_span": {
            name: float(2 ** np.ceil(np.log2(max(abs(info["min"]), abs(info["max"]), 1e-12) / 127.0)))
            for name, info in {
                n: {"min": float(teacher_official[:, i].min()), "max": float(teacher_official[:, i].max())}
                for i, n in enumerate(NAMES)
            }.items()
        },
    }
    per_channel_scales = [ranges["needed_scale_for_span"][name] for name in NAMES]
    per_channel = np.stack(
        [ti_round_codes(teacher_official[:, i], per_channel_scales[i])[0] for i in range(4)], axis=1)
    per_channel_error = np.abs(per_channel - teacher_official)
    per_channel_pwm = [pwm_error(teacher_official[i], per_channel[i])["max_count"] for i in range(len(official))]
    t_lsb_counts = 0.5 * output_scale * TBPRD
    ranges["per_channel_output_quant_vs_teacher"] = {
        "scales": dict(zip(NAMES, [float(s) for s in per_channel_scales])),
        "max_abs": [float(v) for v in per_channel_error.max(axis=0)],
        "max_pwm_count": int(max(per_channel_pwm)),
        "t_half_lsb_period_counts": float(t_lsb_counts),
        "note": (
            "Even with ideal per-channel 8-bit power-of-two output quantizers, T still needs 1/64 "
            "to cover 1.15, so the period counter has a ~20 count rounding floor. 1/128 cannot "
            "represent T=1.15. Last-layer FPU is required to remove this floor."
        ),
    }

    weight_report = []
    for index, ((matrix, bias, rows), (copied_rows, copied_cols), (inputs, outputs)) in enumerate(
            zip(folded, COPIED, CANDIDATE), 1):
        used = matrix[:copied_rows, :copied_cols]
        peak = float(np.max(np.abs(used)))
        scale = 2 ** np.ceil(np.log2(max(peak / 127.0, 1e-12)))
        dequant, _codes, clipped = ti_round_codes(used, scale)
        weight_report.append({
            "layer": index,
            "shape": [int(outputs), int(inputs)],
            "copied": [int(copied_rows), int(copied_cols)],
            "float_peak": peak,
            "symmetric_pot_scale": float(scale),
            "max_abs_weight_quant_error": float(np.max(np.abs(dequant - used))),
            "clip_count": int(np.count_nonzero(clipped)),
            "bias_peak": float(np.max(np.abs(bias[:copied_rows]))),
        })

    hidden_stats = [{"min": 1e9, "max": -1e9, "scale": scale} for scale in hidden_scales]
    clip_counts = [0, 0, 0, 0]
    for vin in official:
        _output, traces = dense_forward(float_layers, mapped_vin(vin), None)
        for layer, (trace, scale) in enumerate(zip(traces, hidden_scales)):
            _q, _c, clipped = ti_round_codes(trace["post"], scale)
            clip_counts[layer] += int(np.count_nonzero(clipped))
            hidden_stats[layer]["min"] = min(hidden_stats[layer]["min"], float(trace["post"].min()))
            hidden_stats[layer]["max"] = max(hidden_stats[layer]["max"], float(trace["post"].max()))
    for layer, stats in enumerate(hidden_stats, 1):
        stats["layer"] = layer
        stats["clip_count_on_official_grid"] = clip_counts[layer - 1]
        stats["effective_lsb"] = stats["scale"]

    grid_rows = []
    pwm_counts = []
    valid_int8 = []
    for i, vin in enumerate(official):
        pwm = pwm_error(teacher_official[i], int8_official[i])
        pwm_counts.append(pwm["max_count"])
        valid_int8.append(nn_valid(int8_official[i]))
        grid_rows.append({
            "set": "official_90_140_step_0_1",
            "vin": vin,
            "teacher_D1": float(teacher_official[i, 0]),
            "teacher_D0": float(teacher_official[i, 1]),
            "teacher_D2": float(teacher_official[i, 2]),
            "teacher_T": float(teacher_official[i, 3]),
            "compact_D1": float(compact_official[i, 0]),
            "compact_D0": float(compact_official[i, 1]),
            "compact_D2": float(compact_official[i, 2]),
            "compact_T": float(compact_official[i, 3]),
            "int8_D1": float(int8_official[i, 0]),
            "int8_D0": float(int8_official[i, 1]),
            "int8_D2": float(int8_official[i, 2]),
            "int8_T": float(int8_official[i, 3]),
            "abs_D1": float(int8_error[i, 0]),
            "abs_D0": float(int8_error[i, 1]),
            "abs_D2": float(int8_error[i, 2]),
            "abs_T": float(int8_error[i, 3]),
            "pwm_tbprd": pwm["tbprd"],
            "pwm_cmpA2": pwm["cmpA2"],
            "pwm_cmpA4": pwm["cmpA4"],
            "pwm_phase34": pwm["phase34"],
            "pwm_max_count": pwm["max_count"],
            "teacher_valid": int(nn_valid(teacher_official[i])),
            "int8_valid": int(valid_int8[-1]),
            "int8_on_1_64": int(np.max(np.abs(int8_official[i] - np.round(int8_official[i] / output_scale) * output_scale)) < 1e-7),
        })
    write_grid_csv(out / "official_grid.csv", grid_rows)

    dense_rows = []
    for vin in dense:
        t_row = teacher(weights, vin)
        c_row = compact_float(folded, vin)
        i_row = onnx_batch(session, [vin])[0]
        pwm = pwm_error(t_row, i_row)
        dense_rows.append({
            "set": "dense_92_2_92_5",
            "vin": vin,
            "teacher_D1": float(t_row[0]), "teacher_D0": float(t_row[1]),
            "teacher_D2": float(t_row[2]), "teacher_T": float(t_row[3]),
            "compact_D1": float(c_row[0]), "int8_D1": float(i_row[0]),
            "int8_D0": float(i_row[1]), "int8_D2": float(i_row[2]), "int8_T": float(i_row[3]),
            "abs_D1": float(abs(i_row[0] - t_row[0])),
            "abs_D0": float(abs(i_row[1] - t_row[1])),
            "abs_D2": float(abs(i_row[2] - t_row[2])),
            "abs_T": float(abs(i_row[3] - t_row[3])),
            "pwm_max_count": pwm["max_count"],
            "teacher_valid": int(nn_valid(t_row)),
            "int8_valid": int(nn_valid(i_row)),
        })
    write_grid_csv(out / "dense_92_2_92_5.csv", dense_rows)

    extra_invalid = []
    extra_max = np.zeros(4, np.float32)
    extra_pwm = 0
    for vin in extra:
        t_row = teacher(weights, vin)
        i_row = onnx_batch(session, [vin])[0]
        err = np.abs(i_row - t_row)
        extra_max = np.maximum(extra_max, err)
        extra_pwm = max(extra_pwm, pwm_error(t_row, i_row)["max_count"])
        if not nn_valid(i_row):
            extra_invalid.append(float(vin))

    vin90 = 90.0
    report = {
        "power_control_approved": False,
        "teacher": "dab_nn.c FPU 3x29x12x6x4",
        "compact_float": "4x32x12x8x4 padded + folded constants",
        "int8": str(PTQ.relative_to(ROOT)).replace("\\", "/"),
        "int8_sha256": sha(PTQ),
        "conv_sha256": sha(CONV) if CONV.exists() else None,
        "firmware_mapping": {
            "ramp": 1.0,
            "duty": 0.0,
            "tbprd": "uint32(T_gain * 2500) truncation",
            "compare": "uint16(normalized_duty * period) truncation",
            "validity": "T in [0.5,2], phases in [-0.005T, 1.005T]",
        },
        "vin90": {
            "teacher": [float(v) for v in teacher(weights, vin90)],
            "compact": [float(v) for v in compact_float(folded, vin90)],
            "int8": [float(v) for v in onnx_batch(session, [vin90])[0]],
        },
        "compact_vs_teacher_official": summarize_abs(compact_error),
        "int8_vs_teacher_official": summarize_abs(int8_error),
        "int8_pwm_official": {
            "max_count": int(max(pwm_counts)),
            "mean_count": float(np.mean(pwm_counts)),
            "within_one_count": bool(max(pwm_counts) <= 1),
            "invalid_vin": [float(official[i]) for i, ok in enumerate(valid_int8) if not ok],
        },
        "output_ranges": ranges,
        "weight_quant": weight_report,
        "hidden_activation_ranges": hidden_stats,
        "ablations_vs_teacher": ablations,
        "worst_official_points": worst_rows(official, int8_error, np.array(pwm_counts), np.array(valid_int8)),
        "dense_92_2_92_5": {
            "invalid_int8_vin": [row["vin"] for row in dense_rows if not row["int8_valid"]],
            "max_abs": [
                max(row["abs_D1"] for row in dense_rows),
                max(row["abs_D0"] for row in dense_rows),
                max(row["abs_D2"] for row in dense_rows),
                max(row["abs_T"] for row in dense_rows),
            ],
            "max_pwm_count": max(row["pwm_max_count"] for row in dense_rows),
        },
        "extrapolation_20_140_not_acceptance": {
            "max_abs": [float(v) for v in extra_max],
            "max_pwm_count": int(extra_pwm),
            "invalid_count": len(extra_invalid),
            "invalid_vin_first_last": extra_invalid[:8] + extra_invalid[-4:] if extra_invalid else [],
        },
        "bottleneck": "filled after ablations",
    }
    ranked = sorted(
        ((name, info["max_pwm_count"], info["max_abs"]) for name, info in ablations.items()),
        key=lambda item: item[1],
    )
    report["bottleneck"] = {
        "ranking_by_max_pwm_count": [
            {"name": name, "max_pwm_count": count, "max_abs": abs_err} for name, count, abs_err in ranked
        ],
        "interpretation": (
            "If output_quant_1_64_only is already far above 1 PWM count, unified output scale is a hard floor. "
            "If hidden3_quant_1_256 or hybrid still fail, last-hidden quantization dominates and last-layer FPU "
            "cannot recover the lost hidden codes."
        ),
    }
    (out / "int8_error_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "report": str(out / "int8_error_report.json"),
        "compact_max_abs": report["compact_vs_teacher_official"]["max"],
        "int8_max_abs": report["int8_vs_teacher_official"]["max"],
        "int8_max_pwm_count": report["int8_pwm_official"]["max_count"],
        "invalid_official": report["int8_pwm_official"]["invalid_vin"],
        "vin90": report["vin90"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
