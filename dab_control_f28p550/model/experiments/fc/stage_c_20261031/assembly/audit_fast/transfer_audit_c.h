#include <stdint.h>
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
