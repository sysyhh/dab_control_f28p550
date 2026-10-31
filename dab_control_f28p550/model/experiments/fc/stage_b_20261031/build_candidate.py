"""Pad frozen, already-quantized FC tensors; no calibration or retraining."""
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
import onnx
from onnx import numpy_helper as nh

HERE=Path(__file__).resolve().parent
FC=HERE.parent
APP=FC.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')


def main():
    src=FC/'onnx/int8_zero_neuron.onnx'
    model=onnx.load(src)
    original={t.name:nh.to_array(t).copy() for t in model.graph.initializer}
    assert original['onnx::MatMul_118'].shape==(16,29)
    assert original['onnx::MatMul_123'].shape==(29,16)
    # First hidden real scale is 1/256, and NNC's unsigned hidden encoding uses
    # zero point 0 (verified also in generated lib1). All new products/biases are 0.
    new={k:v.copy() for k,v in original.items()}
    new['onnx::MatMul_118']=np.pad(original['onnx::MatMul_118'],((0,0),(0,3)))
    new['onnx::MatMul_123']=np.pad(original['onnx::MatMul_123'],((0,3),(0,0)))
    for name,fill in [('layers.0.1.offset',0),('layers.0.1.mult',1),('layers.0.1.shift_mult',1/32)]:
        new[name]=np.pad(original[name],((0,0),(0,3)),constant_values=fill)
    changes=[]
    for i,t in enumerate(model.graph.initializer):
        if not np.array_equal(original[t.name],new[t.name]):
            changes.append(dict(name=t.name,before=list(original[t.name].shape),after=list(new[t.name].shape)))
            model.graph.initializer[i].CopyFrom(nh.from_array(new[t.name],t.name))
    assert len(changes)==5
    assert np.array_equal(new['onnx::MatMul_118'][:,:29],original['onnx::MatMul_118'])
    assert not np.any(new['onnx::MatMul_118'][:,29:]) and not np.any(new['onnx::MatMul_123'][29:])
    assert not np.any(new['layers.0.1.offset'][:,29:])
    # Do not leave original 29-channel intermediate shape annotations behind.
    del model.graph.value_info[:]
    model=onnx.shape_inference.infer_shapes(model)
    onnx.checker.check_model(model)
    out=HERE/'onnx/B1_16_32_16_16_4.onnx'
    out.parent.mkdir(parents=True,exist_ok=True)
    onnx.save(model,out)
    code=(FC/'stage_a_20261031/validated/A4/lib1.c').read_text(encoding='utf-8')
    assert '((float)((int32_t)p0[ax1])) * 3.906250e-03f' in code
    assert 'T_cast[ax1] = ((uint8_t)((v__2) > (0.000000e+00f)' in code
    report=dict(ok=True,source_sha256=sha(src),candidate_sha256=sha(out),changes=changes,
                active_weights_and_quantization_unchanged=True,zero_point=0,zero_real_value=0,
                zero_new_channels_proof='zero integer weights and zero integer bias -> zero accumulator -> scale * 0 -> floor(0) -> unsigned code 0 -> real 0',
                baseline_shape=[16,29,16,16,4],candidate_shape=[16,32,16,16,4],
                baseline_macs=1248,candidate_macs=1344)
    dump(HERE/'results/model_construction.json',report)
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
