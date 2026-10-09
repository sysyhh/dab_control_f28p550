"""Export the existing FLOAT baseline, not an NPU-quantized model.
Run with onnx and numpy installed. No training/calibration range is inferred.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
from onnx.reference import ReferenceEvaluator

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "dab_control_f28p550"

def arrays(path, prefix):
    source = path.read_text(encoding="utf-8-sig", errors="replace").replace("\\\n", "")
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    result = {}
    for k in range(1, 5):
        for kind in ("w", "b"):
            name = f"{prefix}{kind}{k}"
            found = re.search(r"\b" + name + r"\s*\[[^\]]*\]\s*=\s*\{([^}]*)\}", source, re.S)
            assert found, name
            result[f"{kind}{k}"] = np.array([float(x.strip().rstrip("fF")) for x in found[1].split(",") if x.strip()], dtype=np.float32)
    return result

def original_float32(weights, vin):
    x = np.array([-.5, np.float32(vin) / np.float32(140), .285714], dtype=np.float32)
    for k, (nin, nout) in enumerate(((3,29), (29,12), (12,6), (6,4)), 1):
        y = np.empty(nout, dtype=np.float32)
        w, b = weights[f"w{k}"], weights[f"b{k}"]
        for i in range(nout):
            total = np.float32(x[0] * w[i*nin])
            for j in range(1, nin):
                total = np.float32(total + np.float32(x[j] * w[i*nin+j]))
            total = np.float32(total + b[i])
            y[i] = max(total, np.float32(0)) if k < 4 else total
        x = y
    return x

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=APP / "model")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    old = arrays(ROOT / "DAB_20250829_Ver4/source/NN_28335.c", "row_")
    new = arrays(APP / "dab_nn.c", "s_")
    assert all(np.array_equal(old[key], new[key]) for key in old)
    nodes, initializers = [], []
    previous = "normalized_features"
    for k, (nin,nout) in enumerate(((3,29), (29,12), (12,6), (6,4)), 1):
        initializers += [
            numpy_helper.from_array(new[f"w{k}"].reshape(nout,nin), f"W{k}"),
            numpy_helper.from_array(new[f"b{k}"], f"B{k}")]
        gemm_output = "modulation" if k == 4 else f"affine{k}"
        nodes.append(helper.make_node("Gemm", [previous, f"W{k}", f"B{k}"], [gemm_output],
                                      name=f"linear{k}", alpha=1.0, beta=1.0, transB=1))
        previous = gemm_output
        if k < 4:
            previous = f"relu{k}"
            nodes.append(helper.make_node("Relu", [gemm_output], [previous], name=previous))
    graph = helper.make_graph(nodes, "DAB_3_29_12_6_4_FLOAT_BASELINE",
        [helper.make_tensor_value_info("normalized_features", TensorProto.FLOAT, [1,3])],
        [helper.make_tensor_value_info("modulation", TensorProto.FLOAT, [1,4])], initializers)
    model = helper.make_model(graph, producer_name="DAB baseline export", opset_imports=[helper.make_opsetid("",13)])
    model.ir_version = 7
    helper.set_model_props(model, {
        "input_contract": "[-0.5, Vin_volts/140.0, 0.285714]; meanings of constants require training records",
        "output_contract": "[D1,D0,D2,T], linear output; controller divides D1/D0/D2 by T",
        "quantization_status": "FLOAT baseline only; not an NPU binary or calibration dataset",
        "validation_range": "20..140 V step 1 V: synthetic tests, not asserted training range"})
    onnx.checker.check_model(model, full_check=True)
    path = args.output_dir / "dab_float_baseline.onnx"
    onnx.save_model(model, path)
    evaluator = ReferenceEvaluator(str(path))
    maximum = 0.0
    rows = []
    for vin in range(20,141):
        feature = np.array([[-.5, np.float32(vin)/np.float32(140), .285714]], dtype=np.float32)
        output = evaluator.run(None, {"normalized_features": feature})[0][0]
        expected = original_float32(old, vin)
        maximum = max(maximum, float(np.max(np.abs(output-expected))))
        rows.append([vin, *map(float, output)])
    assert maximum < 1e-5, maximum
    np.savetxt(args.output_dir / "validation_vectors_NOT_calibration.csv", rows, delimiter=",",
               header="Vin_test_volts,D1,D0,D2,T", comments="", fmt="%.9g")
    manifest = {
        "onnx_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "model_kind": "float32 baseline, no NPU quantization or binary",
        "structure": [3,29,12,6,4], "parameter_count": sum(x.size for x in new.values()),
        "original_parameters_equal": True, "opset": 13, "ir_version": 7,
        "input_dtype": "float32", "input_shape": [1,3], "output_dtype": "float32", "output_shape": [1,4],
        "normalization": [-.5, "Vin_volts / 140.0", .285714], "output_order": ["D1","D0","D2","T"],
        "validation_test_range": "20..140 V step 1 V, not asserted training/calibration range",
        "validation_vectors": 121, "max_absolute_error_vs_original_float32": maximum,
        "onnx_version": onnx.__version__,
        "required_for_real_npu": ["training input meanings and domain", "representative calibration/training data",
            "TI-supported quantized model", "DAB-specific tvmgen_default.h and mod.a", "on-target numerical and timing checks"]}
    (args.output_dir / "dab_model_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
