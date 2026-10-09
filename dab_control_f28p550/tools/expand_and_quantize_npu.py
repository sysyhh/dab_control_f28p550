"""Expand the DAB float network to an NPU-legal MLP and quantize it.

Shape: 16 -> 32 -> 16 -> 16 -> 4. Original weights are copied into the
leading rows and columns; every added weight and bias is zero, so a
zero-padded 3-input vector has the same float32 function as dab_nn.c.

The quantized model keeps that function, then folds the two constant
firmware inputs into the first bias and maps Vin/140 on 90..140 V onto
[-1, 1]. TI 8-bit quantization is per-tensor and power-of-two, so the
unmapped Vin channel only had a few dozen codes and the control law
moved by hundreds of PWM counts. Install tinyml_torchmodelopt in the
interpreter that runs this script. The quantized ONNX is the input to
TI NNC; this script does not call tvmc and does not replace dab_nn.c.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "dab_control_f28p550"
SHAPES = ((3, 29), (29, 12), (12, 6), (6, 4))
NPU_SHAPES = ((16, 32), (32, 16), (16, 16), (16, 4))
TBPRD = 2500.0


def load_weights(path):
    source = path.read_text(encoding="utf-8-sig", errors="replace").replace("\\\n", "")
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    weights = {}
    for layer in range(1, 5):
        for kind in ("w", "b"):
            name = f"s_{kind}{layer}"
            found = re.search(r"\b" + name + r"\s*\[[^\]]*\]\s*=\s*\{([^}]*)\}", source, re.S)
            if not found:
                raise RuntimeError(f"missing {name} in {path}")
            weights[f"{kind}{layer}"] = np.array(
                [float(item.strip().rstrip("fF")) for item in found.group(1).split(",") if item.strip()],
                dtype=np.float32)
    return weights


def original_forward(weights, features):
    values = np.array(features, dtype=np.float32)
    for layer, (nin, nout) in enumerate(SHAPES, 1):
        matrix = weights[f"w{layer}"]
        bias = weights[f"b{layer}"]
        output = np.empty(nout, dtype=np.float32)
        for i in range(nout):
            total = np.float32(bias[i])
            for j in range(nin):
                total = np.float32(total + np.float32(values[j] * matrix[i * nin + j]))
            output[i] = total if layer == 4 else np.maximum(total, np.float32(0))
        values = output
    return values


def firmware_features(vin):
    return np.array([-0.5, np.float32(vin) / np.float32(140.0), np.float32(0.285714)], dtype=np.float32)


def pad_features(features):
    padded = np.zeros(16, dtype=np.float32)
    padded[:3] = np.array(features, dtype=np.float32)
    return padded


class DabNpuMlp(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(16, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 16)
        self.fc4 = nn.Linear(16, 4)

    def forward(self, features):
        hidden = torch.relu(self.fc1(features))
        hidden = torch.relu(self.fc2(hidden))
        hidden = torch.relu(self.fc3(hidden))
        return self.fc4(hidden)


def load_padded(weights):
    model = DabNpuMlp().float()
    copied = (
        (model.fc1, weights["w1"].reshape(29, 3), weights["b1"], 29, 3),
        (model.fc2, weights["w2"].reshape(12, 29), weights["b2"], 12, 29),
        (model.fc3, weights["w3"].reshape(6, 12), weights["b3"], 6, 12),
        (model.fc4, weights["w4"].reshape(4, 6), weights["b4"], 4, 6),
    )
    with torch.no_grad():
        for layer, matrix, bias, rows, cols in copied:
            layer.weight.zero_()
            layer.bias.zero_()
            layer.weight[:rows, :cols] = torch.from_numpy(matrix)
            layer.bias[:rows] = torch.from_numpy(bias)
    model.eval()
    return model


def batch_from_vins(vins):
    rows = [pad_features(firmware_features(vin)) for vin in vins]
    return torch.from_numpy(np.stack(rows))


def vin_window_affine():
    """Map Vin/140 on 90..140 V to exactly [-1, 1]. u = Vin/25 - 23/5."""
    low = np.float32(90.0 / 140.0)
    high = np.float32(140.0 / 140.0)
    center = (low + high) / np.float32(2.0)
    half = (high - low) / np.float32(2.0)
    return center, half


def mapped_features(vin):
    center, half = vin_window_affine()
    encoded = np.zeros(16, dtype=np.float32)
    encoded[1] = (np.float32(vin) / np.float32(140.0) - center) / half
    return encoded


def mapped_batch(vins):
    return torch.from_numpy(np.stack([mapped_features(vin) for vin in vins]))


def prepare_quant_model(model):
    """Fold the constant inputs and balance per-channel ranges.

    The float result matches dab_nn.c when features[1] is the mapped Vin
    channel and every other feature is zero. Positive channel scales keep
    ReLU(s*z) = s*ReLU(z), so the balance step is float-exact.
    """
    prepared = copy.deepcopy(model).float()
    center, half = vin_window_affine()
    with torch.no_grad():
        weight = prepared.fc1.weight
        bias = prepared.fc1.bias
        bias += weight[:, 0] * np.float32(-0.5)
        bias += weight[:, 1] * center
        bias += weight[:, 2] * np.float32(0.285714)
        weight[:, 1] *= half
        weight[:, 0] = 0
        weight[:, 2] = 0
        for previous, following in (
            (prepared.fc1, prepared.fc2),
            (prepared.fc2, prepared.fc3),
            (prepared.fc3, prepared.fc4),
        ):
            for channel in range(previous.weight.shape[0]):
                previous_peak = previous.weight[channel].abs().max()
                following_peak = following.weight[:, channel].abs().max()
                if float(previous_peak) < 1e-8 or float(following_peak) < 1e-8:
                    continue
                scale = torch.sqrt(following_peak / previous_peak)
                previous.weight[channel] *= scale
                previous.bias[channel] *= scale
                following.weight[:, channel] /= scale
    prepared.eval()
    return prepared


def tighten_prelu_ranges(wrapped):
    """Give ReLU inputs a non-negative observer range.

    A large negative pre-activation sets the shared power-of-two scale,
    so the positive lobe that survives ReLU gets only a few codes.
    Clamping the observer minimum to 0 leaves ReLU(z) unchanged.
    """
    for node in wrapped.module.graph.nodes:
        if node.op != "call_function" or node.target is not torch.relu:
            continue
        source = node.args[0]
        if source.op != "call_module":
            continue
        quantizer = wrapped.module.get_submodule(source.target)
        quantizer.activation_post_process.min_val.fill_(0)
        scale, zero_point = quantizer.calculate_qparams()
        quantizer.scale.copy_(scale)
        quantizer.zero_point.copy_(zero_point)


def compare(model, vins):
    absolute = []
    phase_counts = []
    period_counts = []
    with torch.no_grad():
        predicted = model(batch_from_vins(vins)).numpy()
    for vin, output in zip(vins, predicted):
        expected = original_forward(compare.weights, firmware_features(vin))
        error = np.abs(output - expected)
        absolute.append(error)
        period = max(float(expected[3]), 1e-6)
        phase_counts.append(error[:3] / period * TBPRD)
        period_counts.append(error[3] * TBPRD)
    absolute = np.stack(absolute)
    phase_counts = np.stack(phase_counts)
    return {
        "samples": len(vins),
        "max_abs": [float(value) for value in absolute.max(axis=0)],
        "max_phase_counts": [float(value) for value in phase_counts.max(axis=0)],
        "max_period_counts": float(np.max(period_counts)),
    }


def float_error(model, vins):
    with torch.no_grad():
        predicted = model(mapped_batch(vins)).numpy()
    absolute = []
    for vin, output in zip(vins, predicted):
        absolute.append(np.abs(output - original_forward(compare.weights, firmware_features(vin))))
    absolute = np.stack(absolute)
    return {
        "samples": len(vins),
        "max_abs": [float(value) for value in absolute.max(axis=0)],
    }


def attach_weights(function, weights):
    function.weights = weights
    return function


def quantize(model, calibration):
    from tinyml_torchmodelopt.quantization import TINPUTinyMLPTQFxModule
    from tinyml_torchmodelopt.quantization.common import TinyMLQConfigType

    example = calibration[:1].contiguous()
    qconfig = TinyMLQConfigType(weight_bitwidth=8, activation_bitwidth=8, auto_quantization=False)
    wrapped = TINPUTinyMLPTQFxModule(
        model, total_epochs=1, qconfig_type=qconfig, example_inputs=example,
        output_int=False, num_observer_update_epochs=False, num_batch_norm_update_epochs=False)
    # train() enables observers. eval() before any data would freeze them on this one-epoch wrapper.
    wrapped.train()
    with torch.no_grad():
        wrapped(calibration)
    tighten_prelu_ranges(wrapped)
    wrapped.freeze(freeze_bn=True, freeze_observers=True)
    return wrapped.convert()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=APP / "model")
    parser.add_argument("--skip-quantize", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    weights = load_weights(APP / "dab_nn.c")
    attach_weights(compare, weights)
    model = load_padded(weights)
    torch.save(model.state_dict(), args.output_dir / "dab_npu_float_16x32x16x16x4.pt")
    quantized_model = prepare_quant_model(model)
    torch.save(quantized_model.state_dict(), args.output_dir / "dab_npu_float_folded_16x32x16x16x4.pt")

    operating = [float(vin) for vin in range(90, 141)]
    wider = [float(vin) for vin in range(20, 141)]
    labels = []
    dataset_x = []
    dataset_y = np.array([
        [0.85, 0.2, 0.1, 1.15],
        [0.5, 0.1, 0, 0.85],
        [0.6, 0.2, 0.1, 0.95],
        [0.5, 0.1, 0, 0.9],
        [0.4, 0.1, 0, 0.85],
        [0.4, 0.1, 0, 0.9],
        [0.5, 0.1, 0, 1.0],
        [0.5, 0.1, 0, 1.05],
        [0.5, 0.1, 0, 1.1],
        [0.5, 0.1, 0, 1.15],
        [0.45, 0.25, 0, 1.0],
    ], dtype=np.float32)
    for index, numerator in enumerate(range(28, 17, -1)):
        features = np.array([-0.5, np.float32(numerator / 28.0), np.float32(2.0 / 7.0)], dtype=np.float32)
        dataset_x.append(pad_features(features))
        labels.append(dataset_y[index])
    with torch.no_grad():
        dataset_prediction = model(torch.from_numpy(np.stack(dataset_x))).numpy()
    dataset_error = np.abs(dataset_prediction - np.stack(labels))

    report = {
        "structure": [16, 32, 16, 16, 4],
        "copied_from": [3, 29, 12, 6, 4],
        "padding": "leading rows and columns hold dab_nn.c weights; every added weight and bias is zero",
        "float_input_contract": "[-0.5, Vin/140, 0.285714, then 13 zeros]",
        "quant_input_contract": {
            "features[1]": "Vin/25 - 4.6",
            "other_features": 0,
            "folded_constants": [-0.5, 0.285714],
            "unsaturated_vin": [90, 140],
        },
        "float_vs_dab_nn_vin_90_140": compare(model, operating),
        "float_vs_dab_nn_vin_20_140": compare(model, wider),
        "folded_float_vs_dab_nn_vin_90_140": float_error(quantized_model, operating),
        "folded_float_vs_dab_nn_vin_20_140": float_error(quantized_model, wider),
        "float_vs_screenshot_labels_max_abs": [float(value) for value in dataset_error.max(axis=0)],
        "quantization": "not run",
    }
    if not args.skip_quantize:
        calibration = mapped_batch(operating)
        converted = quantize(quantized_model, calibration)
        onnx_path = args.output_dir / "dab_npu_tinpu_ptq.onnx"
        converted.export(
            calibration[:1], str(onnx_path), input_names=["features"], output_names=["modulation"],
            simplify=False)
        import onnxruntime as ort
        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        quantized = []
        for row in calibration.numpy():
            quantized.append(session.run(None, {"features": row.reshape(1, 16)})[0].reshape(-1))
        quantized = np.stack(quantized)
        teacher = original_forward_batch(weights, operating)
        error = np.abs(quantized - teacher)
        period = np.maximum(teacher[:, 3:4], 1e-6)
        phase_counts = error[:, :3] / period * TBPRD
        period_counts = error[:, 3] * TBPRD
        worst = int(np.argmax(error.max(axis=1)))
        report["quantization"] = {
            "method": "TINPUTinyMLPTQFxModule",
            "weight_activation_bits": 8,
            "activation_scale": "per-tensor, symmetric, power-of-two",
            "output_int": False,
            "calibration": "Vin 90..140 V step 1 V, features[1]=Vin/25-4.6, other features 0",
            "onnx": onnx_path.name,
            "max_abs_vs_dab_nn": [float(value) for value in error.max(axis=0)],
            "median_abs_vs_dab_nn": [float(value) for value in np.median(error, axis=0)],
            "max_phase_counts": [float(value) for value in phase_counts.max(axis=0)],
            "max_period_counts": float(period_counts.max()),
            "worst_vin": operating[worst],
            "within_one_pwm_count": bool(phase_counts.max() <= 1.0 and period_counts.max() <= 1.0),
        }
    (args.output_dir / "dab_npu_quantize_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def original_forward_batch(weights, vins):
    return np.stack([original_forward(weights, firmware_features(vin)) for vin in vins])


if __name__ == "__main__":
    main()
