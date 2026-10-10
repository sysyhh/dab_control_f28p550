"""Recompute the review from archived board results and the delivered 2.1.1 library; no board writes."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'dab_control_f28p550'
DOCS=APP/'docs'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    def check_archived(verification):
        paths=[]
        for item in verification['reports']:
            summary=ROOT/item['summary']
            report=read(summary)
            assert report['ok'] and len(report['runs'])==item['batches']
            assert [run['timing']['endToEnd']['meanUs'] for run in report['runs']]==item['end_to_end_mean_us']
            for index,run in enumerate(report['runs'],1):
                assert all(run['checks'].values())
                raw=read(summary.parent/f'run_{index}.json')
                assert raw['ok'] and raw['out_sha256']==run['out_sha256']
            paths.append(summary)
        return paths
    p5=read(ROOT/'tools/c2000_debug/p5_benchmark_verification.json')
    p6=read(ROOT/'tools/c2000_debug/p6_benchmark_verification.json')
    check_archived(p5)
    check_archived(p6)
    by_label={item['label']:read(ROOT/item['summary']) for item in p6['reports']}
    release,profile,final=by_label['p6_nnc211_release'],by_label['p6_nnc211_profile'],by_label['p6_nnc211_final']
    fpu_path=ROOT/'tools/c2000_debug/benchmarks/20261009_225422_fpu_flash/summary.json'
    fpu=read(fpu_path)
    assert fpu['ok']
    for index,run in enumerate(fpu['runs'],1):
        assert all(run['checks'].values())
        raw=read(fpu_path.parent/f'run_{index}.json')
        assert raw['ok'] and raw['out_sha256']==run['out_sha256']
    kernel=APP/'model/generated/npu/lib2.c'
    runtime=APP/'model/generated/npu/lib1.c'
    manifest=read(APP/'model/generated/npu/manifest.json')
    assert sha(kernel)==manifest['kernel_sha256'] and sha(runtime)==manifest['runtime_sha256']
    assert manifest['ti_mcu_nnc']=='2.1.1' and manifest['detail_profile'] is False
    assert manifest['library_sha256']==final['model_manifest']['library_sha256']==p6['final_library_sha256']
    assert release['runs'][0]['out_sha256']==final['runs'][0]['out_sha256']==p6['restored_firmware_sha256']
    assert sha(APP/'model/generated/npu/mod.a')==manifest['library_sha256']
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',kernel.read_text(encoding='utf-8'),flags=re.S)
    arrays={name:[int(x.strip(),0) for x in values.split(',') if x.strip()]
            for name,values in re.findall(r'static const uint32_t (PWCONV_\w+)\[\]\s*=\s*\{(.*?)\};',text,re.S)}
    bodies=dict(re.findall(r'TVM_DLL int32_t (tvmgen_default_ti_npu_convolve1x1NHWC_\d+)\([^\n]+\) \{(.*?)(?=TVM_DLL int32_t|\Z)',text,re.S))
    layers=[]
    for index in range(4):
        body=bodies[f'tvmgen_default_ti_npu_convolve1x1NHWC_{index}']
        mmr,params,ins=re.findall(r'sizeof\((PWCONV_\w+)\)/sizeof',body)
        layers.append({'index':index,'parameter_uint32_count':len(arrays[params]),
                       'configuration_uint32_count':len(arrays[mmr]),'instruction_table':ins})
    assert len(arrays)==8 and len(set(layer['instruction_table'] for layer in layers))==2
    assert len(set(layer['instruction_table'] for layer in layers[:3]))==1
    ordinary=release['runs'][0]['timing']
    detail=profile['runs'][0]['detail']
    assert detail['instrumented']==1 and final['runs'][0]['detail']['instrumented']==0
    assert detail['lastCalls']==[1,4,1,0,4,4,4,1,1,1,1,1] and detail['stage'][11]['samples']==1000
    cpu=fpu['runs'][0]['timing']
    stages={name:stage['meanUs'] for name,stage in zip(detail['stage_names'],detail['stage'])}
    out=runtime.read_text(encoding='utf-8')
    assert re.search(r'(?:T_multiply|T_reshape)\[ax3\][^\n]*1\.562500e-02f',out)
    shapes={}
    for node in ast.parse((APP/'tools/expand_and_quantize_npu.py').read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('SHAPES','NPU_SHAPES'):
            shapes[node.targets[0].id]=ast.literal_eval(node.value)
    original=[shapes['SHAPES'][0][0]]+[item[1] for item in shapes['SHAPES']]
    padded=[shapes['NPU_SHAPES'][0][0]]+[item[1] for item in shapes['NPU_SHAPES']]
    macs=lambda shape:sum(a*b for a,b in zip(shape,shape[1:]))
    assert sum(int(n) for n in re.findall(r'static const float s_w\d\[(\d+)\]',(APP/'dab_nn.c').read_text(encoding='utf-8')))==macs(original)
    # 下面是矩阵形状的计算量，并非 NPU 指令数；零权重不据此假定自动跳过。
    offline=read(APP/'model/narrow_4x32x12x8x4_offline.json')
    assert offline['compiled'] is True and offline['board_loaded'] is False and offline['power_control_approved'] is False
    assert offline['float_vs_dab_nn_max_abs_vin_20_140_step_0_1']==[0,0,0,0]
    assert offline['quantization']['invalid_output_vin']==[92.2,92.3,92.4,92.5]
    assert offline['quantization']['max_abs_distance_to_1_64_grid']==[0,0,0,0]
    assert offline['compiler']['pwconv_offloaded']==4 and offline['compiler']['pwconv_cpu_fallback']==0
    p5_release=read(ROOT/p5['reports'][0]['summary'])
    p5_profile=read(ROOT/p5['reports'][1]['summary'])
    p5_ordinary=p5_release['runs'][0]['timing']
    p5_stages={name:stage['meanUs'] for name,stage in zip(p5_profile['runs'][0]['detail']['stage_names'],p5_profile['runs'][0]['detail']['stage'])}
    data={'date':'2026-10-10','p5_reference_commit':'b04537d','delivered_ti_mcu_nnc':'2.1.1',
          'board_retested_for_nnc_2_1_1':True,
          'manifest_sha256':sha(APP/'model/generated/npu/manifest.json'),
          'evidence':['tools/c2000_debug/p6_benchmark_verification.json','tools/c2000_debug/p5_benchmark_verification.json',fpu_path.relative_to(ROOT).as_posix()],
          'float_network':original,'npu_network':padded,
          'matrix_multiply_accumulates':{'float':macs(original),'npu_padded':macs(padded),'ratio':macs(padded)/macs(original)},
          'layers':layers,'parameter_uint32_writes_per_inference':sum(layer['parameter_uint32_count'] for layer in layers),
          'ordinary_mean_us':{'fpu_forward':cpu['fpuForward']['meanUs'],'fpu_end_to_end':cpu['endToEnd']['meanUs'],
                               'npu_completion':ordinary['npuCompletion']['meanUs'],'npu_end_to_end':ordinary['endToEnd']['meanUs']},
          'ordinary_min_us':{name:ordinary[name]['minTicks']/150 for name in ('npuSubmit','npuCompletion','endToEnd')},
          'profile_stage_mean_us':stages,
          'profile_end_to_end_us':profile['runs'][0]['timing']['endToEnd']['meanUs'],
          'profile_extra_end_to_end_us':profile['runs'][0]['timing']['endToEnd']['meanUs']-ordinary['endToEnd']['meanUs'],
          'profile_load_sum_us':stages['parameters']+stages['instructions'],
          'profile_wait_sum_us':sum(stages[f'layer{i}Wait'] for i in range(4)),
          'profile_load_fraction':(stages['parameters']+stages['instructions'])/profile['runs'][0]['timing']['endToEnd']['meanUs'],
          'reduction_needed_to_match_current_fpu_fraction':1-cpu['endToEnd']['meanUs']/ordinary['endToEnd']['meanUs'],
          'p5_archived_ordinary_end_to_end_us':p5_ordinary['endToEnd']['meanUs'],
          'p5_archived_profile_stage_mean_us':p5_stages,
          'nnc_2_1_1_end_to_end_reduction_versus_p5':1-ordinary['endToEnd']['meanUs']/p5_ordinary['endToEnd']['meanUs'],
          'output_quantization_step':1/64,'period_count_step_at_base_2500':2500/64,
          'arithmetic_padding_candidate_only':{'shape':[4,32,12,8,4],'macs':macs([4,32,12,8,4]),
                                               'report':'dab_control_f28p550/model/narrow_4x32x12x8x4_offline.json',
                                               'float_equivalent':True,'npu_layers_offloaded':4,
                                               'output_grid':'1/64','hardware_measured':False},
          'limitations':['profile timing includes instrumentation and interrupts',
                         'profile stages cannot be subtracted from ordinary timing to predict a lower bound',
                         'minimum timing is not bare hardware timing',
                         'Vin=90 hardware checks do not establish whole-range accuracy',
                         'narrow padding candidate compiled offline only; quantization error and 1/64 output grid remain']}
    (DOCS/'NPU_reflection_evidence_20261010.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(data,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
