"""Untimed A4/B1 real-board sweep, raw layers, explicit new-zero channels."""
import argparse
import json
import shutil
import sys
import numpy as np
from audit_stage_b import HERE,ROOT,APP,STAGE_A,dump,protect
from run_stage_b import prepare,recompile,debug_cli,run,BUILD

CAP=190


def probes():
    values=list(np.float32(np.arange(501)/10+90))
    for q in range(42,65):
        v=np.float32(140*(q-.5)/64)
        values += [np.nextafter(v,np.float32(-np.inf)),v,np.nextafter(v,np.float32(np.inf))]
    assert len(values)==570
    return values


def capture_project(variant):
    project=prepare(variant,capture=True)
    normal=HERE/'work'/variant/APP.name
    # Start from ordinary validated host graph, making this transformation idempotent.
    code=(normal/'model/generated/fc_int8/lib1.c').read_text(encoding='utf-8')
    code='#include "fc_capture_b.h"\n'+code
    sources={1:'&global_workspace_0_var[32]',2:'&global_workspace_0_var[0]',3:'&global_workspace_0_var[32]',4:'&global_workspace_0_var[16]'}
    for layer in range(1,5):code=code.replace(f'case {layer}:',f'case {layer}:\n  FC_capture({layer-1}U,(uint16_t*){sources[layer]});',1)
    code=code.replace('  tvmgen_default_ti_npu_fullyConnectedNHWC_0(',
        '  FC_captureInput(features_buffer_var);\n  tvmgen_default_ti_npu_fullyConnectedNHWC_0(',1)
    code=code.replace('  DAB_NN_noteNpuCompletion();','  FC_captureOutput(output_buffer_var);\n  DAB_NN_noteNpuCompletion();',1)
    (project/'model/generated/fc_int8/lib1.c').write_text(code,encoding='utf-8')
    header=f'''#include <stdint.h>
extern volatile uint32_t g_nnBenchmarkCompleted;
#pragma DATA_SECTION(g_fcFrames, "ramgs0")
volatile uint16_t g_fcFrames[{CAP}][34];
#pragma DATA_SECTION(g_fcInputs, "ramgs0")
volatile uint16_t g_fcInputs[{CAP}][8];
#pragma DATA_SECTION(g_fcFloats, "ramgs1")
volatile float g_fcFloats[{CAP}][4];
static void FC_capture(uint16_t layer,uint16_t *source) {{
    const uint16_t n[4]={{{15 if variant=='A4' else 16},8,8,2}},offset[4]={{0,16,24,32}};
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;if(row>={CAP})return;
    for(uint16_t i=0;i<n[layer];++i)g_fcFrames[row][offset[layer]+i]=source[i];
    {'if(layer==0){g_fcFrames[row][14]&=255U;g_fcFrames[row][15]=0;}' if variant=='A4' else ''}
}}
static void FC_captureInput(uint16_t *source) {{
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;if(row>={CAP})return;
    for(uint16_t i=0;i<8;++i)g_fcInputs[row][i]=source[i];
}}
static void FC_captureOutput(float *source) {{
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;if(row>={CAP})return;
    for(uint16_t i=0;i<4;++i)g_fcFloats[row][i]=source[i];
}}
'''
    (project/'fc_capture_b.h').write_text(header,encoding='utf-8')
    app=(normal/'dab_nn.c').read_text(encoding='utf-8')
    app='#include "fc_sweep_points.h"\n'+app
    app=app.replace('g_nnBenchmarkIterations = 1000U; g_nnBenchmarkWarmup = 10U;',
                    'g_nnBenchmarkIterations = FC_POINT_COUNT; g_nnBenchmarkWarmup = 0U;')
    app=app.replace('serviceInference(s_benchVin, true);',
        'serviceInference(g_fcVins[g_nnBenchmarkCompleted < FC_POINT_COUNT ? g_nnBenchmarkCompleted : FC_POINT_COUNT-1], true);')
    (project/'dab_nn.c').write_text(app,encoding='utf-8')
    hdr=(project/'dab_nn.h').read_text(encoding='utf-8').replace('#define DAB_NN_BENCH_TICK_CAP 1000U','#define DAB_NN_BENCH_TICK_CAP 1U')
    (project/'dab_nn.h').write_text(hdr,encoding='utf-8')
    return project


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=('A4','B1'));args=parser.parse_args()
    assert json.loads((HERE/'results/mapping_gate.json').read_text())['board_allowed']
    assert json.loads((HERE/'results/host_verification.json').read_text())['ok']
    assert json.loads((HERE/'results/cpu_graph_host.json').read_text())['ok']
    worker=(ROOT/'tools/c2000_debug/debug_worker.js').read_text(encoding='utf-8')
    worker=worker.replace('    if (request.read_e2e_ticks) {',f'''
    result.fc_capture={{}};
    for(const [name,count] of [['g_fcFrames',{CAP}*34],['g_fcInputs',{CAP}*8],['g_fcFloats',{CAP}*8]]) {{
        result.fc_capture[name]=session.memory.read(session.symbols.getAddress(name),count,16);
    }}
    if (request.read_e2e_ticks) {{''')
    (HERE/'capture_worker.js').write_text(worker,encoding='utf-8');cli=debug_cli(capture=True)
    variants=(args.variant,) if args.variant else ('A4','B1')
    for variant in variants:
        project=capture_project(variant);records=[]
        for batch in range(3):
            subset=probes()[batch*CAP:(batch+1)*CAP]
            header='#define FC_POINT_COUNT 190U\nstatic const float g_fcVins[190]={'+','.join(float(v).hex()+'f' for v in subset)+'};\n'
            (project/'fc_sweep_points.h').write_text(header,encoding='utf-8');recompile(project)
            expressions=['g_nnBenchmarkState','g_nnBenchmarkCompleted','g_nnTimeoutCount','g_dabState','g_startRequested',
                         'g_protectFlags.all','g_nnTiming.npuIsrInvocations','g_nnTiming.npuIsrLastCount']
            expressions += [f'g_nnTiming.npuIsrLastLayerCount[{i}]' for i in range(5)]
            cmd=[sys.executable,cli,'--run-test','--rebuild-nn','--nn-auto-benchmark','--project',project,'--build-dir',BUILD,
                 '--run-ms','1500','--samples','1','--timeout-ms','60000','--verify-npu-const']
            for expr in expressions:cmd += ['--expr',expr]
            raw=json.loads(run(cmd,timeout=240));target=HERE/'results/capture'/f'{variant}_{batch}.json';dump(target,raw)
            shutil.copy2(raw['out'],target.with_suffix('.out'))
            target.with_suffix('.points.h').write_text(header,encoding='utf-8')
            v=raw['variables'];tasks=5 if variant=='A4' else 4
            assert raw['ok'] and v['g_nnBenchmarkState']==2 and v['g_nnBenchmarkCompleted']==CAP
            assert v['g_nnTimeoutCount']==v['g_startRequested']==v['g_protectFlags.all']==0 and v['g_dabState']==1
            assert all(raw['registers'][x]&4 for x in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
            assert v['g_nnTiming.npuIsrInvocations']==CAP*tasks and v['g_nnTiming.npuIsrLastCount']==tasks
            assert [v[f'g_nnTiming.npuIsrLastLayerCount[{i}]'] for i in range(5)]==([0,2,1,1,1] if variant=='A4' else [0,1,1,1,1])
            frames=np.array(raw['fc_capture']['g_fcFrames'],np.uint16).reshape(CAP,34)
            inputs=np.array(raw['fc_capture']['g_fcInputs'],np.uint16).reshape(CAP,8)
            floats=np.array(raw['fc_capture']['g_fcFloats'],np.uint16).reshape(CAP,8)
            if variant=='B1':assert not np.any(frames[:,14]&0xff00) and not np.any(frames[:,15]),'new channels are not zero'
            for i,vin in enumerate(subset):records.append(dict(vin=float(vin),input=inputs[i].tolist(),layer_packed=frames[i].tolist(),output_bits=floats[i].tolist()))
            print(f'{variant} batch {batch+1}: 190 real-board points, {tasks} tasks, OST locked',flush=True)
        dump(HERE/f'results/capture/{variant}.json',dict(ok=True,points=records))
        if variant=='A4':
            old=json.loads((STAGE_A/'results/capture/A4.json').read_text(encoding='utf-8'))['points']
            for a,b in zip(old,records):
                extended=a['layer_packed'][:15]+[0]+a['layer_packed'][15:]
                assert a['vin']==b['vin'] and a['input']==b['input'] and a['output_bits']==b['output_bits'] and extended==b['layer_packed']
        else:
            ref=json.loads((HERE/'results/capture/A4.json').read_text(encoding='utf-8'))['points']
            assert ref==records,'candidate raw layer/output mismatch'
    files=[HERE/f'results/capture/{v}.json' for v in ('A4','B1')]
    if all(f.exists() for f in files):
        a,b=[json.loads(f.read_text(encoding='utf-8')) for f in files]
        assert a['points']==b['points']
        dump(HERE/'results/board_correctness.json',dict(ok=True,variants=['A4','B1'],points_per_variant=570,
            official_points=501,float32_boundary_probes=69,new_channels_29_30_31_exact_zero=True,
            valid_layer_elements_and_final_float_bits_equal=True,A4_matches_stage_A_golden=True,
            actual_hardware_tasks=dict(A4=5,B1=4)))
    protect()


if __name__=='__main__':main()
