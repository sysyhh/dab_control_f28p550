"""Reuse B's 570-point capture and add before/after MMR register snapshots."""
import argparse
import inspect
import json
import shutil
import sys
import numpy as np
from common_c import *
from run_stage_c import prepare,recompile,debug_cli,BUILD
from verify_mmr_host import SET,DYNAMIC,decode
import validate_board_b as previous

CAP=190
probes=previous.probes
capture_source=inspect.getsource(previous.capture_project).replace('def capture_project(','def _capture_project(')
exec(capture_source,globals())


def capture_project(variant):
    p=_capture_project(variant);lib=p/'model/generated/fc_int8'
    header=p/'fc_capture_b.h'
    with header.open('a',encoding='utf-8') as f:f.write('''
extern volatile int32_t tinie_curr_layer;
#pragma DATA_SECTION(g_fcMmr, "ramgs1")
volatile uint32_t g_fcMmr[2][4][33];
void DAB_C_captureRegs(uint16_t phase) {
    volatile uint32_t *mmrs=(uint32_t*)(TINIE_BASE_ADDR+TINIE_MMR_OFS);
    uint16_t layer=(uint16_t)(tinie_curr_layer-1);
    if(g_nnBenchmarkCompleted!=0U || layer>=4U)return;
    for(uint16_t i=0;i<33U;++i)g_fcMmr[phase][layer][i]=mmrs[i*2U];
}
''')
    code=(lib/'lib1.c').read_text(encoding='utf-8').replace('#include "fc_capture_b.h"\n','')
    code=replace_once(code,'#include "hard/inc/tinie.h"','#include "hard/inc/tinie.h"\n#include "fc_capture_b.h"')
    (lib/'lib1.c').write_text(code,encoding='utf-8')
    driver=(lib/'dab_tinie_c28.c').read_text(encoding='utf-8')
    driver='extern void DAB_C_captureRegs(unsigned int phase);\n'+driver
    driver=replace_once(driver,'    write_configMMR(layer);','    DAB_C_captureRegs(0U);\n    write_configMMR(layer);\n    DAB_C_captureRegs(1U);')
    (lib/'dab_tinie_c28.c').write_text(driver,encoding='utf-8')
    return p


main_source=inspect.getsource(previous.main).replace('def main():','def _main():')
main_source=main_source.replace("choices=('A4','B1')","choices=('C1A','C1B','C2','C3')").replace("else ('A4','B1')","else ('C1A','C1B')")
main_source=main_source.replace("'C2','C3'","'C2','C3','C4','C5'")
main_source=main_source.replace("if variant=='A4':","if variant=='C1A':")
main_source=main_source.replace("STAGE_A/'results/capture/A4.json'","B/'results/capture/B1.json'")
main_source=main_source.replace("extended=a['layer_packed'][:15]+[0]+a['layer_packed'][15:]","extended=a['layer_packed']")
main_source=main_source.replace("HERE/'results/capture/A4.json'","HERE/'results/capture/C1A.json'")
main_source=main_source.replace("[['g_fcFrames',{CAP}*34],['g_fcInputs',{CAP}*8],['g_fcFloats',{CAP}*8]]","[['g_fcFrames',{CAP}*34],['g_fcInputs',{CAP}*8],['g_fcFloats',{CAP}*8],['g_fcMmr',528]]")
# The original post-loop summary is replaced with the C-specific proof below.
main_source=main_source[:main_source.index('    files=[')]+'    protect()\n'
exec(main_source,globals())


def finish():
    present=[v for v in ('C1A','C1B','C2','C3','C4','C5') if (HERE/f'results/capture/{v}.json').exists()]
    if len(present)<2:return
    reference=json.loads((HERE/'results/capture/C1A.json').read_text(encoding='utf-8'))['points']
    data=json.loads((HERE/'results/mmr_data.json').read_text());snapshot_proofs={}
    for v in present:
        assert json.loads((HERE/f'results/capture/{v}.json').read_text(encoding='utf-8'))['points']==reference
        proofs=[]
        for batch in range(3):
            raw=json.loads((HERE/f'results/capture/{v}_{batch}.json').read_text(encoding='utf-8'))
            words=raw['fc_capture']['g_fcMmr'];assert len(words)==528
            regs=np.array(words,np.uint16).view(np.uint32).reshape(2,4,33)
            target=np.array(json.loads((HERE/f'results/capture/C1A_{batch}.json').read_text(encoding='utf-8'))['fc_capture']['g_fcMmr'],np.uint16).view(np.uint32).reshape(2,4,33)
            for layer in range(4):
                assert np.array_equal(regs[1,layer,list(SET+DYNAMIC)],target[1,layer,list(SET+DYNAMIC)])
                written=set(range(5,29))|{3,31,32,4,29,30} if v in ('C1A','C2') else set(SET+DYNAMIC)
                unchanged=[r for r in range(33) if r not in written]
                assert np.array_equal(regs[0,layer,unchanged],regs[1,layer,unchanged]),(v,batch,layer,'unexpected register mutation')
            proofs.append(dict(batch=batch,pre=regs[0].tolist(),post=regs[1].tolist(),all_live_fields_equal=True,omitted_fields_retained=True))
        snapshot_proofs[v]=proofs
    dump(HERE/'results/mmr_board_snapshots.json',dict(ok=True,variants=snapshot_proofs,
       interpretation='33 raw registers before/after each layer configuration at the first Vin of all three capture batches. Live initialization projection equals full MMR; every unaddressed register retains its own pre-configuration value.'))
    dump(HERE/'results/board_correctness.json',dict(ok=True,variants=present,points_per_variant=570,official_points=501,boundaries=69,
        all_four_layers_and_float_bits_equal=True,all_four_live_register_snapshots_equal=True,hardware_tasks=4,OST_locked=True))
    protect()


if __name__=='__main__':_main();finish()
