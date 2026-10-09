"""Express the checked quantized dense candidate as equivalent 1x1 convolutions.

TI NNC 2.1.0 uses C28 CPU kernels for dense layers by default. 1x1 Conv
allows the same integer weights and arithmetic to use the hardware NPU.
No training, recalibration, or weight rounding is performed here.
"""
from pathlib import Path
import json
import numpy as np
import onnx
from onnx import helper, numpy_helper
import onnxruntime as ort

APP = Path(__file__).resolve().parents[1]


def prepare():
    source = APP / "model/dab_npu_tinpu_ptq.onnx"
    target = APP / "model/dab_npu_tinpu_conv.onnx"
    model = onnx.load(str(source))
    weights = {t.name: numpy_helper.to_array(t) for t in model.graph.initializer}
    nodes = [helper.make_node("Reshape", ["features", "dab_nchw_shape"], ["dab_features_nchw"])]
    model.graph.initializer.append(numpy_helper.from_array(np.array([1, 16, 1, 1], np.int64), "dab_nchw_shape"))
    dense_count = 0
    for node in model.graph.node:
        for i, name in enumerate(node.input):
            if name == "features":
                node.input[i] = "dab_features_nchw"
        if node.op_type == "MatMul":
            name = node.input[1]
            array = weights[name].T[:, :, None, None].copy()
            for i, tensor in enumerate(model.graph.initializer):
                if tensor.name == name:
                    model.graph.initializer[i].CopyFrom(numpy_helper.from_array(array, name))
            node.op_type = "Conv"
            node.attribute.extend([helper.make_attribute("kernel_shape", [1, 1])])
            dense_count += 1
        if node.output[0] == "modulation":
            node.output[0] = "dab_modulation_nchw"
        nodes.append(node)
    if dense_count != 4:
        raise RuntimeError("Expected exactly four dense layers")
    for i, tensor in enumerate(model.graph.initializer):
        if tensor.name.startswith("fc"):
            array = numpy_helper.to_array(tensor)
            if array.ndim == 2 and array.shape[0] == 1:
                model.graph.initializer[i].CopyFrom(numpy_helper.from_array(array.reshape(1, -1, 1, 1), tensor.name))
    nodes.append(helper.make_node("Transpose", ["dab_modulation_nchw"], ["modulation"], perm=[0, 2, 3, 1]))
    del model.graph.node[:]
    model.graph.node.extend(nodes)
    del model.graph.value_info[:]
    onnx.checker.check_model(model)
    onnx.save(model, str(target))
    baseline = ort.InferenceSession(str(source), providers=["CPUExecutionProvider"])
    candidate = ort.InferenceSession(str(target), providers=["CPUExecutionProvider"])
    teacher = ort.InferenceSession(str(APP / "model/dab_float_baseline.onnx"), providers=["CPUExecutionProvider"])
    rows, maximum = [], 0.0
    errors, phase_counts, period_counts, invalid = [], [], [], []
    for vin in np.linspace(90, 140, 501):
        features = np.zeros((1, 16), np.float32)
        features[0, 1] = np.float32(vin) / np.float32(25) - np.float32(4.6)
        old = baseline.run(None, {"features": features})[0].ravel()
        new = candidate.run(None, {"features": features})[0].ravel()
        maximum = max(maximum, float(np.max(np.abs(old-new))))
        original = np.array([[-.5, np.float32(vin)/np.float32(140), .285714]], np.float32)
        expected = teacher.run(None, {teacher.get_inputs()[0].name: original})[0].ravel()
        error = np.abs(new-expected)
        errors.append(error)
        phase_counts.append(error[:3]/expected[3]*2500)
        period_counts.append(float(error[3]*2500))
        if not (np.isfinite(new).all() and .5 <= new[3] <= 2 and
                (new[:3] >= -.005*new[3]).all() and (new[:3] <= 1.005*new[3]).all()):
            invalid.append(float(vin))
        if vin in (90, 100, 110, 120, 130, 140):
            rows.append({"vin": float(vin), "output": new.tolist()})
    report = {"samples": 501, "vin_range": [90, 140], "max_abs_difference_from_dense_quantized": maximum,
              "max_abs_vs_float_onnx": np.max(errors, axis=0).tolist(),
              "estimated_phase_count_error": np.max(phase_counts, axis=0).tolist(),
              "period_count_error": max(period_counts), "invalid_output_vin": invalid,
              "count_error_definition": "phase=abs(output-teacher)/teacher.T*2500; period=abs(T-teacher.T)*2500; diagnostic estimate, not full PWM packet comparison",
              "vectors": rows, "power_control_approved": False}
    (APP / "model/dab_npu_conv_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if maximum != 0:
        raise RuntimeError(f"Conv adapter changed quantized outputs: {maximum}")
    print(json.dumps(report, indent=2))
    return target


if __name__ == "__main__":
    prepare()
