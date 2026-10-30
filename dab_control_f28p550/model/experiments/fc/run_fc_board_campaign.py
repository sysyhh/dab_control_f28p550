"""Native 3-input FC board campaign: package, accuracy, and isolated LaunchPad tests.

Does not overwrite model/generated/npu. PWM OST stays latched. Power start remains blocked.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
ROOT = APP.parent
TOOLS = APP / "tools"
sys.path.insert(0, str(TOOLS))
from analyze_int8_error import firmware_pwm, nn_valid, pwm_error  # noqa: E402
from expand_and_quantize_npu import firmware_features, load_weights, original_forward  # noqa: E402

NNC_PY = ROOT / "review_20261003/npu_integration_20261009/nnc211_env/python.exe"
COMPILER = HERE / "compile_fc_npu.py"
PREPARE = TOOLS / "prepare_fc_ccs_build.py"
BENCH = ROOT / "tools/c2000_debug/benchmark_nn.py"
NN_C = APP / "dab_nn.c"
ONNX = {
    "int8": HERE / "onnx/int8_zero_neuron.onnx",
    "int4": HERE / "onnx/int4_zero_neuron.onnx",
}
SRC = {
    "int8": HERE / "generated/int8_zero_neuron_force_hw",
    "int4": HERE / "generated/int4_zero_neuron_force_hw",
}
FW = {
    "int8": APP / "model/generated/fc_int8",
    "int4": APP / "model/generated/fc_int4",
    "int8_detail": APP / "model/generated/fc_int8_detail",
    "int4_detail": APP / "model/generated/fc_int4_detail",
}
SHAPES = {
    "fpu": (3, 29, 12, 6, 4),
    "int8": (16, 29, 16, 16, 4),
    "int4": (8, 29, 12, 8, 4),
}
WIDTH = {"int8": 16, "int4": 8}


def dump(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def macs(shape):
    return int(sum(shape[i] * shape[i + 1] for i in range(len(shape) - 1)))


def native_features(vin, width):
    x = np.zeros(width, np.float32)
    x[0] = np.float32(-0.5)
    x[1] = np.float32(vin) / np.float32(140.0)
    x[2] = np.float32(0.285714)
    return x


def onnx_predict(path: Path, vins, width):
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        name = session.get_inputs()[0].name
        rows = [session.run(None, {name: native_features(vin, width).reshape(1, -1)})[0].reshape(-1).astype(np.float32)
                for vin in vins]
        return np.stack(rows)
    except ImportError:
        helper = r"""
import json, sys, numpy as np, onnxruntime as ort
path, width = sys.argv[1], int(sys.argv[2])
vins = json.load(sys.stdin)
session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
name = session.get_inputs()[0].name
rows = []
for vin in vins:
    x = np.zeros((1, width), np.float32)
    x[0, 0] = np.float32(-0.5)
    x[0, 1] = np.float32(vin) / np.float32(140.0)
    x[0, 2] = np.float32(0.285714)
    rows.append(session.run(None, {name: x})[0].reshape(-1).astype(np.float32).tolist())
print(json.dumps(rows))
"""
        completed = subprocess.run([str(NNC_PY), "-c", helper, str(path), str(width)],
                                   input=json.dumps([float(v) for v in vins]),
                                   capture_output=True, text=True, encoding="utf-8", check=True)
        return np.asarray(json.loads(completed.stdout), np.float32)


def metrics(predicted, expected, vins):
    predicted = np.asarray(predicted, np.float32)
    expected = np.asarray(expected, np.float32)
    error = np.abs(predicted - expected)
    pwm = [pwm_error(expected[i], predicted[i]) for i in range(len(expected))]
    counts = np.array([item["max_count"] for item in pwm], np.int32)
    invalid = [i for i, row in enumerate(predicted) if not nn_valid(row)]
    crypto = [i for i, vin in enumerate(vins) if 92.2 - 1e-9 <= vin <= 92.5 + 1e-9]
    worst_abs = int(np.argmax(error.max(axis=1)))
    worst_pwm = int(np.argmax(counts))
    return {
        "points": int(len(vins)),
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
        "invalid_vins": [float(vins[i]) for i in invalid[:16]],
        "crypto_max_pwm": int(max((counts[i] for i in crypto), default=0)),
        "crypto_invalid": int(sum(i in invalid for i in crypto)),
        "worst_abs_vin": float(vins[worst_abs]),
        "worst_abs": [float(v) for v in error[worst_abs]],
        "worst_pwm_vin": float(vins[worst_pwm]),
        "worst_pwm_count": int(counts[worst_pwm]),
        "teacher_invalid": int(sum(not nn_valid(row) for row in expected)),
        "vin90": {
            "teacher": [float(v) for v in expected[0]],
            "quant": [float(v) for v in predicted[0]],
            "pwm": pwm[0],
        },
    }


def accuracy() -> dict:
    weights = load_weights(NN_C)
    official = np.round(np.arange(90.0, 140.0 + 1e-9, 0.1), 4)
    crypto = np.round(np.arange(92.2, 92.5 + 1e-9, 0.01), 4)
    teacher = np.stack([original_forward(weights, firmware_features(v)) for v in official])
    teacher_c = np.stack([original_forward(weights, firmware_features(v)) for v in crypto])
    report = {"teacher_macs": macs(SHAPES["fpu"]), "candidates": {}}
    for name in ("int8", "int4"):
        pred = onnx_predict(ONNX[name], official, WIDTH[name])
        pred_c = onnx_predict(ONNX[name], crypto, WIDTH[name])
        report["candidates"][name] = {
            "onnx": str(ONNX[name]),
            "shape": list(SHAPES[name]),
            "macs": macs(SHAPES[name]),
            "native_input_dim": 3,
            "zero_pad_channels": WIDTH[name] - 3,
            "official_90_140_step_0_1": metrics(pred, teacher, official),
            "crypto_92_2_92_5": metrics(pred_c, teacher_c, crypto),
        }
    dump(HERE / "results/board_accuracy_501.json", report)
    return report


def run(command, cwd=ROOT, timeout=240):
    completed = subprocess.run([str(x) for x in command], cwd=cwd, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if completed.returncode:
        raise RuntimeError(completed.stdout[-4000:] + "\n" + completed.stderr[-4000:])
    return completed.stdout


def package(variant: str, detail: bool) -> dict:
    out = FW["int8_detail" if detail else "int8"] if variant == "int8" else FW["int4_detail" if detail else "int4"]
    command = [NNC_PY, COMPILER, "--package-firmware", "--src", SRC[variant], "--out", out,
               "--onnx", ONNX[variant], "--optimization-level", "5", "--reuse-instructions"]
    if detail:
        command.append("--detail-profile")
    text = run(command, cwd=ROOT, timeout=180)
    manifest = json.loads(text[text.rfind("{"):] if text.strip().startswith("{") else text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text[text.find("{"):])


def swap_firmware(variant: str, detail: bool):
    live = FW[variant]
    source = FW[f"{variant}_detail" if detail else variant]
    live.mkdir(parents=True, exist_ok=True)
    for name in ("mod.a", "tvmgen_default.h", "dab_npu_contract.h", "manifest.json", "lib1.c", "lib2.c"):
        shutil.copy2(source / name, live / name)


def board(backend: str, label: str, repeats: int) -> dict:
    text = run([sys.executable, BENCH, "--backend", backend, "--label", label, "--repeats", repeats],
               cwd=ROOT, timeout=repeats * 240 + 60)
    return json.loads(text[text.find("{"):])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-package", action="store_true")
    parser.add_argument("--skip-accuracy", action="store_true")
    parser.add_argument("--board", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    summary = {"ok": False, "live_npu_untouched": True, "power_control_approved": 0}
    try:
        if not args.skip_accuracy:
            summary["accuracy"] = accuracy()
        if not args.skip_package:
            summary["package"] = {
                "int8": package("int8", False),
                "int4": package("int4", False),
                "int8_detail": package("int8", True),
                "int4_detail": package("int4", True),
            }
            run([sys.executable, PREPARE, "--variant", "all"], cwd=ROOT, timeout=60)
            swap_firmware("int8", False)
            swap_firmware("int4", False)
        if args.board:
            summary["board"] = {}
            summary["board"]["fpu"] = board("fpu", "fc_native_fpu", args.repeats)
            summary["board"]["int8"] = board("fc_int8", "fc_native_int8", args.repeats)
            swap_firmware("int8", True)
            summary["board"]["int8_detail"] = board("fc_int8", "fc_native_int8_detail", 1)
            swap_firmware("int8", False)
            summary["board"]["int4"] = board("fc_int4", "fc_native_int4", args.repeats)
            swap_firmware("int4", True)
            summary["board"]["int4_detail"] = board("fc_int4", "fc_native_int4_detail", 1)
            swap_firmware("int4", False)
            summary["ok"] = all(item.get("ok") for item in summary["board"].values())
        else:
            summary["ok"] = True
    except Exception as error:
        summary["error"] = str(error)
    dump(HERE / "results/board_campaign.json", summary)
    print(json.dumps({"ok": summary.get("ok"), "error": summary.get("error"),
                      "report": str(HERE / "results/board_campaign.json")}, ensure_ascii=False))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
