#include "driverlib.h"
#include "dab_nn.h"
#include "tvmgen_default.h"
#include <assert.h>
#include <stdio.h>
extern uint32_t mockTimerReadCost;
volatile int32_t tvmgen_default_finished;
static float *outBuffer;
static unsigned int calls;
static int32_t status;
void TI_NPU_init(void) { tvmgen_default_finished=0;calls=0;status=0; }
int32_t tvmgen_default_run(struct tvmgen_default_inputs *in,struct tvmgen_default_outputs *out)
{
    (void)in;outBuffer=(float *)out->output;calls++;mockTimer-=300;
    return status;
}
static void complete(bool hook)
{
    outBuffer[0]=.45f;outBuffer[1]=.25f;outBuffer[2]=.001f;outBuffer[3]=1.0f;
    if(hook) DAB_NN_noteNpuCompletion();
    tvmgen_default_finished=1;
}
int main(void)
{
    uint32_t submit;
    Mock_reset();DAB_NN_init();mockTimerReadCost=10;
    DAB_NN_service(90);assert(calls==1 && g_nnTiming.npuObserved.samples==0);
    assert(!DAB_NN_resetTiming());mockTimer-=900;complete(true);
    mockTimer-=150;DAB_NN_service(90);
    assert(g_nnTiming.npuSubmit.samples==1 && g_nnTiming.npuSubmit.lastTicks==310);
    assert(g_nnTiming.npuObserved.lastTicks>g_nnTiming.npuCompletion.lastTicks);
    assert(g_nnTiming.npuCompletion.samples==1 && g_nnTiming.fpuForward.samples==0);
    submit=g_nnTiming.npuSubmit.lastTicks;
    DAB_NN_service(91);mockTimer-=900;complete(false);DAB_NN_service(91);
    assert(g_nnTiming.npuObserved.samples==2 && g_nnTiming.npuCompletion.samples==1);
    assert(g_nnTiming.npuSubmit.minTicks==submit && g_nnTiming.npuSubmit.maxTicks==submit);

    g_nnBenchmarkIterations=2;g_nnBenchmarkWarmup=1;g_nnBenchmarkRequested=true;
    assert(DAB_NN_benchmarkService(true));assert(!DAB_NN_resetTiming());
    mockTimer-=900;complete(true);DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkWarmupCompleted==1 && g_nnTiming.npuObserved.samples==0);
    DAB_NN_benchmarkService(true);mockTimer-=900;complete(true);DAB_NN_benchmarkService(true);
    DAB_NN_benchmarkService(true);mockTimer-=900;complete(true);DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkState==DAB_NN_BENCH_DONE && g_nnBenchmarkCompleted==2);
    assert(g_nnTiming.npuObserved.samples==2 && g_nnTiming.npuCompletion.samples==2);

    // Cancelling cannot reuse the outstanding accelerator buffers.
    g_nnBenchmarkIterations=3;g_nnBenchmarkWarmup=0;g_nnBenchmarkRequested=true;
    DAB_NN_benchmarkService(true);submit=calls;
    g_nnBenchmarkCancelRequested=true;DAB_NN_benchmarkService(true);
    assert(DAB_NN_isBenchmarkActive() && calls==submit);
    complete(false);DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkState==DAB_NN_BENCH_CANCELLED && calls==submit);

    Mock_reset();DAB_NN_init();g_nnBenchmarkIterations=1;g_nnBenchmarkWarmup=0;
    g_nnBenchmarkRequested=true;DAB_NN_benchmarkService(true);mockTimer-=150001;
    DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkState==DAB_NN_BENCH_FAILED && g_nnTimeoutCount==1);
    assert(g_nnTiming.npuObserved.samples==0 && g_nnTiming.rejectedOutputs==1);
    Mock_reset();DAB_NN_init();status=-1;DAB_NN_service(90);
    assert(g_nnTiming.npuObserved.samples==0 && g_nnTiming.rejectedOutputs==1);
    puts("PASS NPU timing fixture: submit versus finish, completion hook versus polling, warmup, finite repeat, cancellation ownership, timeout rejection");
    return 0;
}
