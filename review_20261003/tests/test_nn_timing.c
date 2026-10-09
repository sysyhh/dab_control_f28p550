#define main original_application_test_main
#include "test_application.c"
#undef main
extern uint32_t mockTimerReadCost;

static void request(uint32_t iterations, uint32_t warmup)
{
    g_nnBenchmarkIterations=iterations;g_nnBenchmarkWarmup=warmup;
    g_nnBenchmarkVin=90.0f;g_nnBenchmarkRequested=true;
}
int main(void)
{
    unsigned int i;
    testNN(); // 121 independent original-expression reference vectors.
    Mock_reset();DAB_NN_init();mockTimerReadCost=10;
    DAB_NN_service(90.0f);
    assert(g_nnTiming.backend==0 && g_nnTiming.fpuForward.samples==1);
    assert(g_nnTiming.prepare.lastTicks==10 && g_nnTiming.fpuForward.lastTicks==10);
    assert(g_nnTiming.publish.lastTicks==10 && g_nnTiming.endToEnd.lastTicks==40);
    assert(fabsf(g_nnTiming.fpuForward.meanUs-10.0f/150.0f)<1e-6f);
    DAB_NN_service(90.0f);assert(g_nnTiming.fpuForward.samples==1); // Cache hit is not inference.
    assert(DAB_NN_resetTiming() && g_nnTiming.timerReadOverheadTicks==10);
    mockTimer=5;DAB_NN_service(91.0f);
    assert(g_nnTiming.fpuForward.lastTicks==10 && g_nnTiming.endToEnd.lastTicks==40);
    DAB_NN_service(92.0f);assert(g_nnTiming.fpuForward.totalTicks==20);
    assert(g_nnTiming.fpuForward.minTicks==10 && g_nnTiming.fpuForward.maxTicks==10);
    assert(g_nnTimingSequence%2==0);

    request(3,2);
    assert(!DAB_NN_benchmarkService(false));
    assert(g_nnBenchmarkState==DAB_NN_BENCH_REJECTED && g_nnBenchmarkRejectReason==2);
    request(3,2);assert(DAB_NN_benchmarkService(true));
    assert(DAB_NN_isBenchmarkActive() && g_nnBenchmarkWarmupCompleted==1);
    assert(g_nnTiming.fpuForward.samples==0 && !DAB_NN_resetTiming());
    for(i=0;i<4;i++) assert(DAB_NN_benchmarkService(true));
    assert(g_nnBenchmarkState==DAB_NN_BENCH_DONE);
    assert(g_nnBenchmarkWarmupCompleted==2 && g_nnBenchmarkCompleted==3);
    assert(g_nnTiming.fpuForward.samples==3 && g_nnTiming.endToEnd.samples==3);
    assert(g_nnTiming.fpuForward.totalTicks==30 && !DAB_NN_benchmarkService(true));
    assert(g_nnTiming.frozen);DAB_NN_service(100);
    assert(g_nnTiming.fpuForward.samples==3 && g_nnTiming.fpuForward.totalTicks==30);
    request(0,0);DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkRejectReason==4 && g_nnBenchmarkState==DAB_NN_BENCH_REJECTED);
    request(5,0);DAB_NN_benchmarkService(true);
    g_nnBenchmarkCancelRequested=true;DAB_NN_benchmarkService(true);
    assert(g_nnBenchmarkState==DAB_NN_BENCH_CANCELLED && g_nnBenchmarkCompleted==1);

    // A legitimate standby start must be refused while timing test owns NN.
    ready();request(5,0);assert(DAB_NN_benchmarkService(true));
    assert(!DAB_Control_start() && g_startRejectReason==6 && !DAB_PWM_isEnabled());
    g_nnBenchmarkCancelRequested=true;DAB_NN_benchmarkService(true);
    assert(DAB_Control_start());DAB_Control_stop();
    // 64-bit total survives the 32-bit boundary; count saturation freezes it.
    Mock_reset();DAB_NN_init();mockTimerReadCost=10;
    g_nnTiming.fpuForward.samples=1;g_nnTiming.fpuForward.totalTicks=0xFFFFFFFFULL;
    g_nnTiming.fpuForward.minTicks=10;DAB_NN_service(90.0f);
    assert(g_nnTiming.fpuForward.totalTicks==0x100000009ULL);
    g_nnTiming.fpuForward.samples=0xFFFFFFFFUL;
    DAB_NN_service(91.0f);assert(g_nnTiming.fpuForward.totalTicks==0x100000009ULL);
    puts("PASS NN timing: reference outputs, boundaries, cache, timer wrap, statistics, warmup, finite repeat, cancel, power-start exclusion");
    return 0;
}
