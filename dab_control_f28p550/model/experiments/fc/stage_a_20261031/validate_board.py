"""Separate, untimed board sweep: raw packed layer images and float output bits."""
import argparse
import json
from pathlib import Path
import struct
import sys
import numpy as np
from patch_stage_a import application, transform
from run_stage_a import HERE, ROOT, APP, BASE, BUILD, VARIANTS, prepare, recompile_library, run, dump, make_debug_cli

CAP=190


def prepare_capture(variant):
    project=prepare(variant,capture=True)
    header=f'''#ifndef FC_CAPTURE_H
#define FC_CAPTURE_H
#include <stdint.h>
extern volatile uint32_t g_nnBenchmarkCompleted;
#pragma DATA_SECTION(g_fcFrames, "ramgs0")
volatile uint16_t g_fcFrames[{CAP}][33];
#pragma DATA_SECTION(g_fcInputs, "ramgs0")
volatile uint16_t g_fcInputs[{CAP}][8];
#pragma DATA_SECTION(g_fcFloats, "ramgs1")
volatile float g_fcFloats[{CAP}][4];
static void FC_capture(uint16_t layer, uint16_t *source) {{
    const uint16_t n[4]={{15,8,8,2}}, offset[4]={{0,15,23,31}};
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;
    if(row >= {CAP}) return;
    for(uint16_t i=0;i<n[layer];++i) g_fcFrames[row][offset[layer]+i]=source[i];
    if(layer==0) g_fcFrames[row][14]&=255U;
}}
static void FC_captureInput(uint16_t *source) {{
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;
    if(row >= {CAP}) return;
    for(uint16_t i=0;i<8;++i) g_fcInputs[row][i]=source[i];
}}
static void FC_captureOutput(float *source) {{
    uint16_t row=(uint16_t)g_nnBenchmarkCompleted;
    if(row >= {CAP}) return;
    for(uint16_t i=0;i<4;++i) g_fcFloats[row][i]=source[i];
}}
#endif
'''
    (project/'fc_capture.h').write_text(header,encoding='utf-8')
    lib=project/'model/generated/fc_int8'
    code='#include "fc_capture.h"\n'+transform((BASE/'lib1.c').read_text(encoding='utf-8'),variant)
    for layer in range(1,5):
        if variant in ('A2','A4'):
            src={1:'&global_workspace_0_var[32]',2:'&global_workspace_0_var[0]',
                 3:'&global_workspace_0_var[32]',4:'&global_workspace_0_var[16]'}[layer]
        else:
            src={1:'sid_3_let',2:'sid_7_let',3:'sid_11_let',4:'sid_15_let'}[layer]
        code=code.replace(f'case {layer}:',f'case {layer}:\n  FC_capture({layer-1}U,(uint16_t*){src});',1)
    src='features_buffer_var' if variant in ('A3','A4') else 'sid_2_let'
    line='  tvmgen_default_ti_npu_fullyConnectedNHWC_0('
    code=code.replace(line,f'  FC_captureInput((uint16_t*){src});\n'+line,1)
    code=code.replace('  DAB_NN_noteNpuCompletion();','  FC_captureOutput(output_buffer_var);\n  DAB_NN_noteNpuCompletion();',1)
    (lib/'lib1.c').write_text(code,encoding='utf-8')
    code=application((APP/'dab_nn.c').read_text(encoding='utf-8'),variant in ('A3','A4'))
    code='#include "fc_sweep_points.h"\n'+code
    code=code.replace('g_nnBenchmarkIterations = 1000U; g_nnBenchmarkWarmup = 10U;',
                      'g_nnBenchmarkIterations = FC_POINT_COUNT; g_nnBenchmarkWarmup = 0U;')
    code=code.replace('serviceInference(s_benchVin, true);','serviceInference(g_fcVins[g_nnBenchmarkCompleted < FC_POINT_COUNT ? g_nnBenchmarkCompleted : FC_POINT_COUNT-1], true);')
    (project/'dab_nn.c').write_text(code,encoding='utf-8')
    header=(project/'dab_nn.h').read_text(encoding='utf-8').replace('#define DAB_NN_BENCH_TICK_CAP 1000U','#define DAB_NN_BENCH_TICK_CAP 1U')
    (project/'dab_nn.h').write_text(header,encoding='utf-8')
    return project


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',choices=VARIANTS)
    args=parser.parse_args()
    assert json.loads((HERE/'results/host_verification.json').read_text())['ok']
    variants=(args.variant,) if args.variant else VARIANTS
    probes=list(np.float32(np.arange(501)/10+90))
    for q in range(42,65):
        edge=np.float32(140*(q-.5)/64)
        probes += [np.nextafter(edge,np.float32(-np.inf)),edge,np.nextafter(edge,np.float32(np.inf))]
    assert len(probes)==570 and min(probes)>=90 and max(probes)<=140
    worker=(ROOT/'tools/c2000_debug/debug_worker.js').read_text(encoding='utf-8')
    worker=worker.replace('    if (request.read_e2e_ticks) {',f'''
    result.fc_capture={{}};
    for(const [name,count] of [['g_fcFrames',{CAP}*33],['g_fcInputs',{CAP}*8],['g_fcFloats',{CAP}*8]]) {{
        const address=session.symbols.getAddress(name);
        result.fc_capture[name]=session.memory.read(address,count,16);
    }}
    if (request.read_e2e_ticks) {{''')
    (HERE/'capture_worker.js').write_text(worker,encoding='utf-8')
    cli=make_debug_cli(capture=True)
    for variant in variants:
        project=prepare_capture(variant)
        records=[]
        for batch in range(3):
            subset=probes[batch*CAP:(batch+1)*CAP]
            points='#define FC_POINT_COUNT '+str(len(subset))+'U\nstatic const float g_fcVins[FC_POINT_COUNT] = {'
            points+=','.join(float(v).hex()+'f' for v in subset)+'};\n'
            (project/'fc_sweep_points.h').write_text(points,encoding='utf-8')
            recompile_library(project)
            cmd=[sys.executable,cli,'--run-test','--rebuild-nn','--nn-auto-benchmark','--project',project,
                 '--build-dir',BUILD,'--run-ms','1500','--samples','1','--timeout-ms','60000','--verify-npu-const']
            for expr in ('g_nnBenchmarkState','g_nnBenchmarkCompleted','g_nnTimeoutCount','g_dabState',
                         'g_startRequested','g_protectFlags.all'):
                cmd+=['--expr',expr]
            raw=json.loads(run(cmd,timeout=240))
            dump(HERE/f'results/capture/{variant}_{batch}.json',raw)
            values=raw['variables']
            assert raw['ok'] and values['g_nnBenchmarkState']==2
            assert values['g_nnBenchmarkCompleted']==len(subset) and values['g_nnTimeoutCount']==0
            assert values['g_dabState']==1 and values['g_startRequested']==values['g_protectFlags.all']==0
            assert all(raw['registers'][k]&4 for k in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
            frames=np.array(raw['fc_capture']['g_fcFrames'],dtype=np.uint16).reshape(CAP,33)
            inputs=np.array(raw['fc_capture']['g_fcInputs'],dtype=np.uint16).reshape(CAP,8)
            floats=np.array(raw['fc_capture']['g_fcFloats'],dtype=np.uint16).reshape(CAP,8)
            for i,vin in enumerate(subset):
                records.append({'vin':float(vin),'input':inputs[i].tolist(),'layer_packed':frames[i].tolist(),
                                'output_bits':floats[i].tolist()})
            print(f'{variant} capture batch {batch+1}: {len(subset)} points passed',flush=True)
        dump(HERE/f'results/capture/{variant}.json',{'ok':True,'points':records})
        if variant!='Baseline':
            baseline=json.loads((HERE/'results/capture/Baseline.json').read_text(encoding='utf-8'))
            assert baseline['points']==records,variant+' raw layer mismatch'
    available={v:json.loads((HERE/f'results/capture/{v}.json').read_text(encoding='utf-8'))
               for v in VARIANTS if (HERE/f'results/capture/{v}.json').exists()}
    dump(HERE/'results/board_correctness.json',{'ok':len(available)==5 and all(available[v]['points']==available['Baseline']['points'] for v in available),
          'variants':list(available),'points_per_variant':570,'official_points':501,'adjacent_boundary_probes':69,
          'comparison':'exact packed input, all four raw layer images, all final float bits; padding masked only at unused byte 29'})


if __name__=='__main__':
    main()
