"""Check that an NNC upgrade retains this model's four hardware layer definitions."""
import argparse
import hashlib
import json
import re
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def layer_data(folder):
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',(folder/'lib2.c').read_text(encoding='utf-8'),flags=re.S)
    arrays={name:[int(x.strip(),0) for x in body.split(',') if x.strip()]
            for name,body in re.findall(r'static const uint32_t (PWCONV_\w+)\[\]\s*=\s*\{(.*?)\};',code,re.S)}
    functions=re.findall(r'TVM_DLL int32_t (tvmgen_default_ti_npu_convolve1x1NHWC_\d+)\([^\n]+\) \{(.*?)(?=TVM_DLL int32_t|\Z)',code,re.S)
    layers={}
    for name,body in functions:
        mmr,params,ins=re.findall(r'sizeof\((PWCONV_\w+)\)/sizeof',body)
        layers[name]={'configuration':arrays[mmr],'parameters':arrays[params],'instructions':ins}
    assert len(layers)==4 and len(arrays)==8
    return layers

def instructions(root,name):
    code=(root/'3rdparty/tinie-api/hard/ins_asm'/(name+'.h')).read_text(encoding='utf-8')
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
    body=re.search(re.escape(name)+r'\[\]\s*=\s*\{(.*?)\};',code,re.S)
    assert body, name
    return [int(x.strip(),0) for x in body[1].split(',') if x.strip()]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--baseline-tvm',type=Path,required=True)
    parser.add_argument('--candidate-tvm',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    baseline=json.loads((args.baseline/'manifest.json').read_text())
    candidate=json.loads((args.candidate/'manifest.json').read_text())
    for folder,manifest in ((args.baseline,baseline),(args.candidate,candidate)):
        for key,name in (('library_sha256','mod.a'),('runtime_sha256','lib1.c'),('kernel_sha256','lib2.c'),('driver_sha256','dab_tinie_c28.c')):
            assert sha(folder/name)==manifest[key],name
    for key in ('model_sha256','input_shape','output_shape','io_dtype','hardware_stages'):
        assert baseline[key]==candidate[key],key
    old,new=layer_data(args.baseline),layer_data(args.candidate)
    assert old==new, 'Hardware layer parameters/configuration/instruction selection changed'
    tables=sorted(set(layer['instructions'] for layer in new.values()))
    sizes={}
    for name in tables:
        a,b=instructions(args.baseline_tvm,name),instructions(args.candidate_tvm,name)
        assert a==b, name
        sizes[name]=len(b)
    # lib0 的量化比例和取整偏置按字段核对；声明顺序不影响比较。
    scalars=lambda folder:dict(re.findall(r'\.(\w+)\s*=\s*\{\s*([^\s}]+)',(folder/'lib0.c').read_text()))
    assert scalars(args.baseline)==scalars(args.candidate)
    result={'ok':True,'baseline_nnc':baseline['ti_mcu_nnc'],'candidate_nnc':candidate['ti_mcu_nnc'],
            'same_model_sha256':candidate['model_sha256'],'four_layer_definitions_identical':True,
            'instruction_data_identical':True,'instruction_uint32_counts':sizes,
            'quantization_scalar_constants_identical':True,
            'scope':'static definitions; does not replace whole-range hardware output acceptance'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
