"""Measure original copier before EINT: LS3/GS1 -> GS0/known NPU PARAMS."""
import json
import shutil
import statistics
import sys
from common_c import *
from run_stage_c import prepare,recompile,debug_cli


def main(fast=False):
    protect();p=prepare('AUDIT_FAST' if fast else 'AUDIT');lib=p/'model/generated/fc_int8'
    result=HERE/'results/transfer_fast' if fast else HERE/'results';result.mkdir(exist_ok=True)
    driver=(BASE/'dab_tinie_c28.c').read_text(encoding='utf-8')
    driver+='''
#pragma CODE_SECTION(DAB_C_writeBaseline,".dab_npu_ramfunc")
void DAB_C_writeBaseline(volatile uint32_t *dst,uint32_t n,const uint32_t *src){TINIE_mem_write(dst,n,src);}
'''
    if fast:
        from parameter_candidate import patch
        driver=patch(driver).replace('{TINIE_mem_write(dst,n,src);}','{DAB_C_mem_write_fast(dst,n,src);}')
    (lib/'dab_tinie_c28.c').write_text(driver,encoding='utf-8')
    kernel=(BASE/'lib2.c').read_text(encoding='utf-8')
    kernel+='\nconst uint32_t* DAB_C_paramSource(uint16_t layer,uint32_t* n){switch(layer){\n'
    for l in mapping(BASE)['layers']:
        name=l['parameters'][0];kernel+=f'case {l["layer"]}: *n=sizeof({name})/sizeof({name}[0]);return {name};\n'
    kernel+='default:*n=0;return 0;}}\n'
    (lib/'lib2.c').write_text(kernel,encoding='utf-8')
    hdr='''#include <stdint.h>
extern void DAB_C_writeBaseline(volatile uint32_t*,uint32_t,const uint32_t*);
extern const uint32_t* DAB_C_paramSource(uint16_t,uint32_t*);
#pragma DATA_SECTION(g_cTransferTicks,"ramgs0")
volatile uint32_t g_cTransferTicks[16][128];
#pragma DATA_SECTION(g_cAuditZeroTicks,"ramgs0")
volatile uint32_t g_cAuditZeroTicks[128];
#pragma DATA_SECTION(s_cAuditDst,"ramgs0")
static volatile uint32_t s_cAuditDst[512];
#pragma DATA_SECTION(s_cAuditSrc,"ramgs1")
static uint32_t s_cAuditSrc[208];
volatile uint32_t g_cAuditDone,g_cAuditErrors,g_cAuditN[4],g_cAuditSourceAddr[4];
volatile uint16_t g_cAuditBeforeEint;
#pragma CODE_SECTION(DAB_C_runTransferAudit,".TI.ramfunc")
void DAB_C_runTransferAudit(void){
    uint16_t layer,source,target,sample,slot;
    uint32_t n,i,begin;
    const uint32_t *original,*src;
    volatile uint32_t *dst;
    bool masked=Interrupt_disableGlobal();g_cAuditBeforeEint=masked?1U:0U;
    if(!masked)g_cAuditErrors++;
    for(layer=0;layer<4U;++layer){
        original=DAB_C_paramSource(layer,&n);
        g_cAuditN[layer]=n;g_cAuditSourceAddr[layer]=(uint32_t)original;
        for(i=0;i<n;++i)s_cAuditSrc[i]=original[i];
        for(source=0;source<2U;++source)for(target=0;target<2U;++target){
            src=source?s_cAuditSrc:original;
            dst=target?(uint32_t*)0x55800UL:s_cAuditDst;
            slot=source*8U+target*4U+layer;
            for(sample=0;sample<128U;++sample){
                begin=CPUTimer_getTimerCount(CPUTIMER2_BASE);
                DAB_C_writeBaseline(dst,n,src);
                g_cTransferTicks[slot][sample]=begin-CPUTimer_getTimerCount(CPUTIMER2_BASE);
                for(i=0;i<n;++i)if(dst[i*2U]!=src[i])g_cAuditErrors++;
            }
        }
    }
    for(sample=0;sample<128U;++sample){
        begin=CPUTimer_getTimerCount(CPUTIMER2_BASE);
        DAB_C_writeBaseline(s_cAuditDst,0,s_cAuditSrc);
        g_cAuditZeroTicks[sample]=begin-CPUTimer_getTimerCount(CPUTIMER2_BASE);
    }
    g_cAuditDone=1;
    if(!masked)Interrupt_enableGlobal();
}
'''
    (p/'transfer_audit_c.h').write_text(hdr,encoding='utf-8')
    app=(BASE/'dab_nn.stage_b.c').read_text(encoding='utf-8')+'\n#include "transfer_audit_c.h"\n'
    (p/'dab_nn.c').write_text(app,encoding='utf-8')
    main=(APP/'dab_main.c').read_text(encoding='utf-8')
    marker='    DAB_PWM_init();'
    assert main.count(marker)==1
    # Place after PWM OST initialization and before the original EINT.
    lines=main.splitlines();line=next(i for i,s in enumerate(lines) if marker in s)
    lines.insert(line+1,'    DAB_C_runTransferAudit();')
    (p/'dab_main.c').write_text('extern void DAB_C_runTransferAudit(void);\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    recompile(p)
    worker=(ROOT/'tools/c2000_debug/debug_worker.js').read_text(encoding='utf-8').replace('    if (request.read_e2e_ticks) {','''
    result.transfer_ticks=session.memory.read(session.symbols.getAddress('g_cTransferTicks'),4096,16);
    result.zero_ticks=session.memory.read(session.symbols.getAddress('g_cAuditZeroTicks'),256,16);
    if (request.read_e2e_ticks) {''')
    (HERE/'capture_worker.js').write_text(worker,encoding='utf-8');cli=debug_cli(capture=True)
    cmd=[sys.executable,cli,'--run-test','--rebuild-nn','--nn-auto-benchmark','--project',p,'--build-dir',BUILD,
         '--samples','1','--run-ms','1500','--timeout-ms','60000','--verify-npu-const']
    expressions=['g_cAuditDone','g_cAuditErrors','g_cAuditBeforeEint','g_nnBenchmarkState','g_nnBenchmarkCompleted','g_nnTimeoutCount','g_dabState','g_startRequested']
    expressions += [f'g_cAuditN[{i}]' for i in range(4)]+[f'g_cAuditSourceAddr[{i}]' for i in range(4)]+[f'g_nnBenchmarkOutput[{i}]' for i in range(4)]
    for e in expressions:cmd+=['--expr',e]
    raw=json.loads(run(cmd,timeout=240));dump(result/'transfer_audit_raw.json',raw)
    v=raw['variables'];assert raw['ok'] and v['g_cAuditDone']==v['g_cAuditBeforeEint']==1 and v['g_cAuditErrors']==0
    assert v['g_nnBenchmarkState']==2 and v['g_nnBenchmarkCompleted']==1000 and v['g_nnTimeoutCount']==v['g_startRequested']==0 and v['g_dabState']==1
    assert [v[f'g_nnBenchmarkOutput[{i}]'] for i in range(4)]==[.453125,.25,0,1]
    assert all(raw['registers'][k]&4 for k in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
    words=raw['transfer_ticks'];ticks=[words[i]|words[i+1]<<16 for i in range(0,len(words),2)];rows=[]
    for source in range(2):
        for target in range(2):
            for layer in range(4):
                slot=source*8+target*4+layer;t=ticks[slot*128:(slot+1)*128];n=v[f'g_cAuditN[{layer}]']
                rows.append(dict(source='GS1' if source else 'LS3',target='NPU_PARAMS' if target else 'GS0',layer=layer,
                  uint32_count=n,source_word_address=v[f'g_cAuditSourceAddr[{layer}]'] if not source else None,
                  min_ticks=min(t),mean_ticks=statistics.mean(t),max_ticks=max(t),min_cycles_per_uint32=min(t)/n,raw_ticks=t))
    dump(result/'transfer_audit.json',dict(ok=True,interrupts_masked=True,samples_each=128,modeled_transfer_width=32,
         logical_parameter_bytes=2024,NPU_word_base='0x55800',NPU_word_stride=4,rows=rows,
         zero_ticks=[raw['zero_ticks'][i]|raw['zero_ticks'][i+1]<<16 for i in range(0,256,2)],
         scope='same baseline routine, exact four parameter sizes, destination and source changed independently; not an inference speed score'))
    dest=HERE/('assembly/audit_fast' if fast else 'assembly/audit');dest.mkdir(exist_ok=True)
    for f in lib.glob('*.asm'):shutil.copy2(f,dest/f.name)
    shutil.copy2(raw['out'],result/'transfer_audit.out');print(json.dumps(dict(ok=True,rows=[{k:r[k] for k in ('source','target','uint32_count','min_ticks','min_cycles_per_uint32')} for r in rows])))
    protect()


if __name__=='__main__':main('--fast' in sys.argv)
