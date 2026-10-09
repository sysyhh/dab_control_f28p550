/* Host fixture verifies the adapter and safety gates, not NPU execution speed. */
#include "driverlib.h"
#include "dab_nn.h"
#include "dab_control.h"
#include "model/generated/npu/tvmgen_default.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
volatile int32_t tvmgen_default_finished;
static float *input, *output;
static unsigned calls;
void TI_NPU_init(void) { calls=0; tvmgen_default_finished=0; }
int32_t tvmgen_default_run(struct tvmgen_default_inputs *in, struct tvmgen_default_outputs *out)
{
    unsigned i;
    input=(float *)in->features; output=(float *)out->output; calls++;
    for(i=0;i<16;i++) if(i!=1) assert(input[i]==0.0f);
    assert(fabsf(input[1]+1.0f)<1.e-6f); /* Vin=90, not the legacy Vin/140 */
#if DAB_NPU_DETAIL_PROFILE
    DAB_NN_traceBegin(DAB_NPU_INPUT); mockTimer-=100; DAB_NN_traceEnd(DAB_NPU_INPUT);
#endif
    mockTimer-=300;
    return 0;
}
static void complete(void)
{
    output[0]=.4375f;output[1]=.25f;output[2]=0;output[3]=1;
    DAB_NN_noteNpuCompletion();tvmgen_default_finished=1;
}
int main(void)
{
    float saved[16], result[4];
    Mock_reset();DAB_NN_init();DAB_Control_init();
    assert(!DAB_Control_start() && g_startRejectReason==7); /* even board=1, auto=1 */
    g_nnBenchmarkVin=89;g_nnBenchmarkRequested=true;
    assert(!DAB_NN_benchmarkService(true));
    assert(g_nnBenchmarkRejectReason==4 && calls==0 && !DAB_NN_hasFault());
    g_nnBenchmarkVin=141;g_nnBenchmarkRequested=true;DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkRejectReason==4 && calls==0);
    g_nnBenchmarkVin=90;g_nnBenchmarkIterations=2;g_nnBenchmarkWarmup=1;
    g_nnBenchmarkRequested=true;DAB_NN_benchmarkService(true);
    memcpy(saved,input,sizeof(saved));DAB_NN_service(140);
    assert(calls==1 && memcmp(saved,input,sizeof(saved))==0 && !DAB_NN_getOutput(result));
    mockTimer-=900;complete();DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkWarmupCompleted==1 && g_nnTiming.npuObserved.samples==0);
    DAB_NN_benchmarkService(true);mockTimer-=900;complete();DAB_NN_benchmarkService(true);
    DAB_NN_benchmarkService(true);mockTimer-=900;complete();DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkState==DAB_NN_BENCH_DONE && g_nnBenchmarkCompleted==2);
    assert(g_nnTiming.npuCompletion.samples==2 && g_nnTiming.fpuForward.samples==0);
#if DAB_NPU_DETAIL_PROFILE
    assert(g_nnNpuDetail.instrumented && g_nnNpuDetail.invalidPairs==0);
    assert(g_nnNpuDetail.stage[DAB_NPU_INPUT].samples==2 && g_nnNpuDetail.stage[DAB_NPU_INPUT].lastTicks==100);
    assert(g_nnNpuDetail.lastCalls[DAB_NPU_INPUT]==1);
#else
    assert(!g_nnNpuDetail.instrumented && g_nnNpuDetail.stage[DAB_NPU_INPUT].samples==0);
#endif
    assert(DAB_NN_getOutput(result) && result[0]==.4375f && g_nnLastOutput[3]==1);
    assert(!DAB_Control_start() && g_startRejectReason==7);
    Mock_reset();DAB_NN_init();DAB_NN_service(90);mockTimer-=150001;
    DAB_NN_service(90);assert(DAB_NN_hasFault() && g_nnTimeoutCount==1);
    complete();DAB_NN_service(90);assert(!DAB_NN_getOutput(result) && calls==1);
    Mock_reset();DAB_NN_init();DAB_NN_service(90);
    complete();output[2]=-.015625f;DAB_NN_service(90);
    assert(DAB_NN_hasFault() && !DAB_NN_getOutput(result)); /* no relaxed phase guard */
    puts("PASS DAB16 adapter: 16-float normalization, domain, asynchronous ownership, warmup/repeat, final-output timestamp, timeout lock, power gate");
    return 0;
}
