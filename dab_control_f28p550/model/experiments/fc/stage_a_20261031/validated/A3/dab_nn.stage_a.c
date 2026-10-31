#include "fc_stage_a_input.h"
//#############################################################################
//
// FILE:   dab_nn.c
//
// TITLE:  DAB Neural Network Inference Implementation for F28P550
//         Supports dual-mode: FPU Baseline (RAM-resident) & Hardware NPU (TVM)
//
//#############################################################################

#include "dab_nn.h"
#include <string.h>
#include "dab_math.h"

#ifdef DAB_USE_HARDWARE_NPU
#ifdef DAB_NPU_FC_INT8
#include "model/generated/fc_int8/tvmgen_default.h"
#elif defined(DAB_NPU_FC_INT4)
#include "model/generated/fc_int4/tvmgen_default.h"
#elif defined(DAB_NPU_DAB16_MODEL)
#include "model/generated/npu/tvmgen_default.h"
#else
#ifndef DAB_NPU_FLOAT_IO_CONFIRMED
#error "Verify the DAB generated model has float32 input[3] and output[4] before enabling NPU"
#endif
#include "model/tvmgen_default.h"
#endif
#if defined(__TI_COMPILER_VERSION__) && defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_RAM_RUNTIME
extern uint16_t DabNpuLoadStart, DabNpuLoadSize, DabNpuRunStart;
#if DAB_NPU_RAM_CONSTANTS
extern uint16_t DabNpuConstLoadStart, DabNpuConstLoadSize, DabNpuConstRunStart;
#endif
#endif
#endif

// Intermediate buffers
#ifdef DAB_NPU_GENERATED_MODEL
#pragma DATA_ALIGN(s_input, 16)
#pragma DATA_SECTION(s_input, "ramgs1")
static uint16_t s_input[8] = {0x00e0U, 0x0012U, 0, 0, 0, 0, 0, 0};
#if DAB_NPU_DETAIL_PROFILE
static uint32_t s_stageInputTicks;
#endif // NPU 模型输入宽度由生成契约给出，完成前不得改写。
#else
static float s_input[DAB_NN_INPUT_DIM]; // FPU 使用原始三项归一化输入。
#endif
#ifndef DAB_USE_HARDWARE_NPU
static float s_layer1[DAB_NN_LAYER1_OUT];
static float s_layer2[DAB_NN_LAYER2_OUT];
static float s_layer3[DAB_NN_LAYER3_OUT];
#endif
static float s_output[DAB_NN_OUTPUT_DIM];
volatile float g_nnLastOutput[DAB_NN_OUTPUT_DIM]; // CCS 只读观察：D1、D0、D2、T；有效性由 getOutput 判断。
volatile float g_nnBenchmarkOutput[DAB_NN_OUTPUT_DIM];
volatile uint16_t g_nnBenchmarkOutputValid;
static volatile bool s_valid, s_fault;
static float s_lastVin;
static bool s_hasInput;
volatile uint32_t g_nnInferenceCount = 0U;
volatile uint32_t g_nnTimeoutCount = 0U;
#ifdef DAB_USE_HARDWARE_NPU
static volatile bool s_busy; // 真实 NPU 分支一次只允许一个运算在途，超时后不自动重试。
static volatile uint32_t s_started;
// Keep descriptors alive too: an asynchronous runtime may retain their address.
static struct tvmgen_default_inputs s_npuInputs = { (void *)s_input };
static struct tvmgen_default_outputs s_npuOutputs = { (void *)s_output };
#endif

// 统计仅由后台更新；完成 ISR 钩子只保存时间戳，避免扩大实时中断负担。
volatile Dab_NnTiming_t g_nnTiming;
volatile Dab_NpuDetail_t g_nnNpuDetail;
#ifdef DAB_USE_HARDWARE_NPU
static volatile uint32_t s_traceStart[DAB_NPU_TRACE_SLOTS], s_traceTicks[DAB_NPU_TRACE_SLOTS];
static volatile uint16_t s_traceCalls[DAB_NPU_TRACE_SLOTS];
static volatile bool s_traceOpen[DAB_NPU_TRACE_SLOTS];
#endif
volatile uint32_t g_nnTimingSequence;
volatile bool g_nnTimingResetRequested, g_nnTimingResetAccepted;
volatile bool g_nnBenchmarkRequested, g_nnBenchmarkCancelRequested;
volatile uint32_t g_nnBenchmarkIterations = 1000U, g_nnBenchmarkWarmup = 10U;
volatile float g_nnBenchmarkVin = DAB_NOMINAL_VIN;
volatile Dab_NnBenchmarkState_e g_nnBenchmarkState;
volatile uint32_t g_nnBenchmarkCompleted, g_nnBenchmarkWarmupCompleted;
volatile uint16_t g_nnBenchmarkRejectReason;
#if DAB_NN_AUTO_BENCHMARK
#pragma DATA_SECTION(g_nnBenchmarkE2eTicks, "ramgs0")
volatile uint32_t g_nnBenchmarkE2eTicks[DAB_NN_BENCH_TICK_CAP];
#endif
static uint32_t s_jobBeginTick, s_jobPrepTick, s_jobRunTick, s_jobReturnTick;
static bool s_profileActive, s_benchJob, s_benchCancel;
static uint32_t s_benchIterations, s_benchWarmup;
static float s_benchVin;
#ifdef DAB_USE_HARDWARE_NPU
static volatile bool s_npuDoneStamped;
static volatile uint32_t s_npuDoneTick;
static volatile uint32_t s_isrEnterTick, s_isrTicks, s_isrMaxTicks;
static volatile uint16_t s_isrCount, s_isrLayerCount[5];
#endif

static void clearTiming(void)
{
    uint32_t begin;
    g_nnTimingSequence++;
    memset((void *)&g_nnTiming, 0, sizeof(g_nnTiming));
    memset((void *)&g_nnNpuDetail, 0, sizeof(g_nnNpuDetail));
#if defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_DETAIL_PROFILE
    g_nnNpuDetail.instrumented = true;
#endif
    g_nnTiming.timerHz = DEVICE_SYSCLK_FREQ;
    g_nnTiming.revision = 2U;
#ifdef DAB_USE_HARDWARE_NPU
    g_nnTiming.backend = 1U;
#endif
    begin = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    g_nnTiming.timerReadOverheadTicks = begin - CPUTimer_getTimerCount(CPUTIMER2_BASE);
    g_nnTimingSequence++;
}

bool DAB_NN_resetTiming(void)
{
    if (s_profileActive || DAB_NN_isBenchmarkActive()) return false;
#ifdef DAB_USE_HARDWARE_NPU
    if (s_busy) return false;
#endif
    clearTiming();
    return true;
}

static void addTime(volatile Dab_NnTimeStats_t *stats, uint32_t ticks)
{
    if (stats->samples == 0xFFFFFFFFUL) return; // 样本计数饱和后冻结，避免平均值与总和失配。
    if (stats->samples == 0U || ticks < stats->minTicks) stats->minTicks = ticks;
    if (stats->samples == 0U || ticks > stats->maxTicks) stats->maxTicks = ticks;
    stats->lastTicks = ticks;
    stats->totalTicks += ticks;
    stats->samples++;
    stats->meanUs = ((float)stats->totalTicks / (float)stats->samples) /
                    ((float)DEVICE_SYSCLK_FREQ / 1000000.0f);
}

static void snapshotBenchmarkOutput(void)
{
    uint16_t i;
    for (i = 0U; i < DAB_NN_OUTPUT_DIM; i++)
        g_nnBenchmarkOutput[i] = s_output[i];
    g_nnBenchmarkOutputValid = 1U;
}

static void finishProfile(bool valid, uint32_t observedTick, uint32_t publishedTick)
{
#if defined(DAB_USE_HARDWARE_NPU) && defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_DETAIL_PROFILE
    uint16_t slot;
#endif
#ifdef DAB_USE_HARDWARE_NPU
    uint16_t layer;
#endif
    bool warmup = s_benchJob && g_nnBenchmarkWarmupCompleted < s_benchWarmup;
    g_nnTimingSequence++;
    if ((!valid || !s_valid) && !g_nnTiming.frozen) g_nnTiming.rejectedOutputs++;
    if (valid && !warmup && !g_nnTiming.frozen)
    {
        addTime(&g_nnTiming.prepare, s_jobBeginTick - s_jobPrepTick);
#ifdef DAB_USE_HARDWARE_NPU
        addTime(&g_nnTiming.npuSubmit, s_jobRunTick - s_jobReturnTick);
        addTime(&g_nnTiming.npuObserved, s_jobRunTick - observedTick);
        if (s_npuDoneStamped)
            addTime(&g_nnTiming.npuCompletion, s_jobRunTick - s_npuDoneTick);
        addTime(&g_nnTiming.npuIsr, s_isrTicks);
        g_nnTiming.npuIsrInvocations += s_isrCount;
        if (s_isrMaxTicks > g_nnTiming.npuIsrMaxSingleTicks)
            g_nnTiming.npuIsrMaxSingleTicks = s_isrMaxTicks;
        g_nnTiming.npuIsrLastCount = s_isrCount;
        for (layer = 0U; layer < 5U; layer++)
            g_nnTiming.npuIsrLastLayerCount[layer] = s_isrLayerCount[layer];
#if defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_DETAIL_PROFILE
        for (slot=0U; slot<DAB_NPU_TRACE_SLOTS; slot++)
        {
            g_nnNpuDetail.lastCalls[slot] = s_traceCalls[slot];
            if (s_traceCalls[slot]) addTime(&g_nnNpuDetail.stage[slot], s_traceTicks[slot]);
        }
#endif
#else
        addTime(&g_nnTiming.fpuForward, s_jobRunTick - s_jobReturnTick);
#endif
        addTime(&g_nnTiming.publish, observedTick - publishedTick);
        addTime(&g_nnTiming.endToEnd, s_jobBeginTick - publishedTick);
        if (s_benchJob)
        {
            snapshotBenchmarkOutput();
#if DAB_NN_AUTO_BENCHMARK
            if (g_nnBenchmarkCompleted < DAB_NN_BENCH_TICK_CAP)
                g_nnBenchmarkE2eTicks[g_nnBenchmarkCompleted] = s_jobBeginTick - publishedTick;
#endif
        }
    }
    s_profileActive = false;
    if (s_benchJob)
    {
        s_benchJob = false;
        if (!valid) g_nnBenchmarkState = DAB_NN_BENCH_FAILED;
        else
        {
            if (warmup) g_nnBenchmarkWarmupCompleted++;
            else g_nnBenchmarkCompleted++;
            if (s_benchCancel) g_nnBenchmarkState = DAB_NN_BENCH_CANCELLED;
            else if (g_nnBenchmarkCompleted == s_benchIterations)
                g_nnBenchmarkState = DAB_NN_BENCH_DONE;
        }
        if (!DAB_NN_isBenchmarkActive()) g_nnTiming.frozen = true;
    }
    g_nnTimingSequence++;
}

// ISR 中只记原始时间；求平均在任务完成后由后台统一进行。
#pragma CODE_SECTION(DAB_NN_traceBegin, ".TI.ramfunc")
void DAB_NN_traceBegin(uint16_t slot)
{
#ifdef DAB_USE_HARDWARE_NPU
    if (slot >= DAB_NPU_TRACE_SLOTS || !s_busy) return;
    if (s_traceOpen[slot]) g_nnNpuDetail.invalidPairs++;
    s_traceStart[slot] = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    s_traceOpen[slot] = true;
#endif
}

#pragma CODE_SECTION(DAB_NN_traceEnd, ".TI.ramfunc")
void DAB_NN_traceEnd(uint16_t slot)
{
#ifdef DAB_USE_HARDWARE_NPU
    if (slot >= DAB_NPU_TRACE_SLOTS || !s_busy) return;
    if (!s_traceOpen[slot]) { g_nnNpuDetail.invalidPairs++; return; }
    s_traceTicks[slot] += s_traceStart[slot] - CPUTimer_getTimerCount(CPUTIMER2_BASE);
    s_traceCalls[slot]++;
    s_traceOpen[slot] = false;
#endif
}

#pragma CODE_SECTION(DAB_NN_noteNpuCompletion, ".TI.ramfunc")
void DAB_NN_noteNpuCompletion(void)
{
#ifdef DAB_USE_HARDWARE_NPU
    if (s_busy && !s_npuDoneStamped)
    {
        s_npuDoneTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        s_npuDoneStamped = true; // 完成 ISR 应在调用本钩子之后才发布 finished。
    }
#endif
}

#ifdef DAB_USE_HARDWARE_NPU
static void resetIsrStats(void)
{
    uint16_t layer;
    s_isrTicks = s_isrMaxTicks = 0U;
    s_isrCount = 0U;
    for (layer = 0U; layer < 5U; layer++) s_isrLayerCount[layer] = 0U;
}
#endif

#pragma CODE_SECTION(DAB_NN_isrEnter, ".TI.ramfunc")
void DAB_NN_isrEnter(void)
{
#ifdef DAB_USE_HARDWARE_NPU
    s_isrEnterTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
#endif
}

#pragma CODE_SECTION(DAB_NN_isrExit, ".TI.ramfunc")
void DAB_NN_isrExit(uint16_t layer)
{
#ifdef DAB_USE_HARDWARE_NPU
    uint32_t ticks = s_isrEnterTick - CPUTimer_getTimerCount(CPUTIMER2_BASE);
    s_isrTicks += ticks;
    if (s_isrCount == 0U || ticks > s_isrMaxTicks) s_isrMaxTicks = ticks;
    if (s_isrCount != 0xFFFFU) s_isrCount++;
    if (layer < 5U && s_isrLayerCount[layer] != 0xFFFFU) s_isrLayerCount[layer]++;
#else
    (void)layer;
#endif
}

// Network weights and biases
#ifndef DAB_USE_HARDWARE_NPU
static const float s_w1[87] = {
    -0.059094455, -0.674842894, 0.0534533, 0.611398518, 0.569107533, -0.623762131,
    0.684330106, 1.377245903, -0.669560492, 0.035934869, -0.047007423, -0.026668731,
    -0.219270572, -1.24047935, 0.221520513, 0.48532927, 0.660480142, -0.467695147,
    0.582158089, 0.8037166, -0.594887078, -0.023364807, -0.434696347, 0.009178801,
    0.045528967, -0.049350176, -0.036985841, 0.043838173, -0.056574799, -0.047232669,
    -0.059813358, -0.396697313, 0.072364435, -0.088355295, -0.773362756, 0.084037058,
    -0.074468695, -0.399034411, 0.062600434, 0.614585996, 1.514019489, -0.618685722,
    -0.294187039, -1.219188333, 0.289027005, 0.605158031, 0.873853803, -0.597366154,
    -0.081251487, -0.704959869, 0.086456574, 0.032288939, -0.068609104, -0.032333173,
    -0.009739437, -0.330261976, 0.006051856, 0.491088957, 0.684060872, -0.464955896,
    0.741538405, 1.294440031, -0.752439857, -0.160173401, -0.815430164, 0.13108553,
    0.26046145, 0.270690203, -0.281262755, 0.261468828, 0.352833748, -0.268625766,
    -0.031593841, -0.854537606, 0.032834705, -0.051002067, -0.618216872, 0.05851458,
    -0.010851994, -0.343936384, 0.004288957, -0.086199939, -0.408141583, 0.07659515,
    0.514550924, 0.767210305, -0.495845288
};

static const float s_b1[29] = {
    0.139336109, -0.510013163, -0.565491378, 0.055593807, 0.315970957, -0.371510059,
    -0.485158205, 0.128061891, 0.053239431, 0.049560383, 0.164564431, 0.200206578,
    0.169863969, -0.512467682, 0.388652295, -0.506963253, 0.193583935, 0.051112562,
    0.111376494, -0.385832846, -0.650059104, 0.247377083, -0.173887104, -0.176496357,
    0.122943997, 0.144298434, 0.101956338, 0.175973192, -0.405357659
};

static const float s_w2[348] = {
    -0.9709993, -0.505118191, -1.72480011, -0.007361599, 1.467722774, -0.788094819,
    -1.021416426, 0.145849541, -0.019245585, -0.027206574, 0.212243274, -1.255699158,
    0.220259249, -0.466780782, -3.290388107, -0.885790765, 0.693052232, -0.002714192,
    0.061324917, -0.921185851, -8.376428604, 0.895643234, -0.286041617, -0.450373471,
    -0.99992758, 0.503941596, 0.133619577, 0.230707049, -0.418921918, 0.223657548,
    -0.353868812, -0.346973866, -0.003022184, 2.017218828, -0.42951116, -0.749309599,
    0.146860719, -0.015468967, -0.037982475, 0.125425145, 0.388471305, 0.153220966,
    -1.961657524, 1.488842368, -1.493662, 0.476727217, -0.030707074, 0.028132696,
    -0.491069525, -0.363961548, 0.876582801, -0.137721643, -0.197996929, 0.407052338,
    0.309903175, 0.037322581, 0.146401212, -0.418854624, -0.087402195, 0.109753244,
    0.16299881, -0.004406804, -0.190345898, -0.016324438, -0.034348544, -0.012934263,
    -0.013076484, -0.005428093, -0.060925778, -0.084301546, -0.034271926, -0.22911948,
    -0.050753493, -0.234223664, -0.217054725, 0.00430368, 0.084509999, -0.094702013,
    0.023844391, -0.18925041, 0.014262134, 0.013472646, -0.163547814, -0.097295314,
    -0.075600982, -0.040727869, 0.141400293, 0.379200757, -0.397008628, -0.573219717,
    -0.036492892, 1.557077408, -0.585257888, -0.572645366, 0.204630017, -0.028229436,
    -0.051503103, 0.207238793, 0.638765872, 0.246362448, -0.836313486, 3.235683918,
    -0.605444551, 0.394102126, -0.062401902, 0.003406757, -0.552743852, -0.538389444,
    0.731597006, -0.21170108, -0.282433659, 0.6645087, 0.179748312, 0.149418563,
    0.250077724, -0.443487406, -0.117772274, 0.696971059, 1.183869004, 0.042620432,
    -0.315093875, 0.593739629, 0.964390814, -0.049431141, 0.02110975, 0.024572104,
    -0.087475479, -0.132432804, -0.073150463, 0.839472055, 0.052387308, 0.849465132,
    -0.350677341, 0.026991041, 0.109646216, 0.64450103, 1.594296336, -0.560560226,
    0.071740232, 0.069493584, -0.169829503, -0.332137793, -0.057666276, -0.068640262,
    1.294832706, 0.052311052, 0.021161908, 0.185566753, 0.003233962, 1.330452204,
    -0.111817561, -0.314525306, 0.031788565, 0.001270083, -0.008085489, -0.007557767,
    0.101174861, 0.017701577, -3.442802191, -0.680836976, -1.318202853, 0.65691942,
    -0.009794649, 0.072965235, -0.343920201, -0.019088514, 0.868993819, -0.074196525,
    -0.087945193, -0.044190489, 0.38988322, -0.04420355, 0.01736672, 0.064750589,
    0.602353156, -0.506409049, -0.165423512, -0.047676101, 1.44052577, -0.573151529,
    -1.123203516, 0.266977131, -0.047302626, -0.041934736, 0.276711643, 0.896816373,
    0.266870201, -7.790977955, 3.303937674, -0.74111712, 0.493296593, -0.069412343,
    -0.040978394, -0.561255872, -0.693288326, 0.831259489, -0.184606805, -0.253933489,
    0.832554162, 0.200986221, 0.229763195, 0.294197321, -0.625658453, -0.010515264,
    -0.0196112, -0.11413087, -0.009281099, 0.1511565, -0.22859095, -0.284617275,
    -0.007007143, -0.008735619, -0.007512947, -0.008826433, 0.008449742, -0.028332734,
    -0.350231558, 0.080053844, -0.363938481, -0.072702408, -0.015565057, 0.098484807,
    -0.305141032, -0.145863429, -0.153033525, -0.010494177, -0.02772476, -0.115484744,
    -0.148522228, -0.06056856, -0.016684443, 0.033545218, -0.11088153, -0.120264187,
    -0.110536292, -0.1085556, -0.079454973, -0.131829157, -0.103081666, -0.109469444,
    -0.083360963, -0.097530447, -0.113418251, -0.094795309, -0.104023606, -0.106701247,
    -0.103642881, -0.092467926, -0.103000537, -0.101901747, -0.101349056, -0.109657973,
    -0.108695842, -0.091480315, -0.098929852, -0.091937453, -0.100932911, -0.102610558,
    -0.118121825, -0.102790438, -0.120696433, -0.121403061, 0.835874915, 1.512109518,
    0.012984428, 0.083512977, 0.415229112, 0.621262729, -0.05065915, 0.029375477,
    0.02574084, -0.066772908, -0.134371668, -0.07345546, 1.094773293, 0.014017298,
    0.665554762, -0.412304044, 0.018604994, 0.105853505, 0.435835034, 2.087508678,
    -0.549889743, 0.076267727, 0.06530115, -0.17321606, -0.212897941, -0.088616289,
    -0.071295224, 1.129566908, -0.124420263, -0.125838548, -0.128592625, -0.126737028,
    -0.113550834, -0.127448663, -0.134810269, -0.120799065, -0.1268076, -0.109449662,
    -0.125539184, -0.110832289, -0.13253127, -0.120640181, -0.137385294, -0.115379766,
    -0.129101813, -0.114161246, -0.124524049, -0.134456247, -0.153822958, -0.112901822,
    -0.13363333, -0.142009258, -0.131333321, -0.112291977, -0.138823569, -0.117671646,
    -0.125513151, -0.094935596, -0.117378987, -0.109334312, -0.124625012, -0.112938359,
    -0.132035136, -0.113423392, -0.118968993, -0.107991241, -0.109511524, -0.112280346,
    -0.12138842, -0.124992177, -0.113265887, -0.122703113, -0.10954906, -0.118473068,
    -0.111170717, -0.096763998, -0.117297024, -0.107092842, -0.100866646, -0.112963803,
    -0.127175525, -0.128359646, -0.097855426, -0.125539765, -0.100797817, -0.122741364
};

static const float s_b2[12] = {
    0.69114989, -0.160289437, -0.147988826, -0.046482287, -0.455300272, -0.056798205,
    0.20012413, -0.142078549, -0.011787405, -0.382172704, -0.026515475, -0.019595833
};

static const float s_w3[72] = {
    1.288911343, -1.145381808, -0.050793238, 0.191361591, -0.486123294, -0.607155681,
    -0.666375637, 0.088778995, 0.065417521, 1.583575726, 0.052961811, 0.057719689,
    1.134298921, -0.833152831, -0.062745586, 0.359309345, -2.120829821, -2.35049367,
    -0.704528809, 0.052488547, 0.056495231, 0.768143713, 0.039488744, 0.047232103,
    0.88057375, -1.24275136, 0.029504839, -1.028092623, 0.795403838, -0.640404522,
    -1.376152515, -0.1060917, -0.062963888, 0.355563939, -0.060545962, -0.05763071,
    1.279609561, -1.466987967, -0.063380472, -0.593964815, 0.698616803, -0.123122804,
    -1.855036139, 0.00975043, 0.118592866, 0.20055066, 0.125956967, 0.126530752,
    0.987691045, -1.028049588, -0.089149281, -0.439828932, -1.274476171, -0.201057389,
    -1.1721766, 0.001690489, 0.106716082, -0.093809858, 0.112116233, 0.10863883,
    1.111304164, -0.534420609, -0.065109566, -0.32639721, 0.899146199, 1.224976897,
    0.316769719, 0.011251768, 0.125885487, -0.192247063, 0.116646014, 0.125024691
};

static const float s_b3[6] = {
    -0.358082443, -0.682663083, -0.947808385, -0.26226604, -0.128243819, -0.119003601
};

static const float s_w4[24] = {
    1.008962512, -1.048211813, 1.953723311, 0.45300746, -0.639563322, -0.054633498,
    -0.028643375, -0.00725867, 0.789218009, 0.31713298, -0.976394594, 0.540090382,
    -0.123015158, 0.006560468, 0.941388845, 0.688924551, -0.967251062, 0.205305159,
    0.843887448, 0.612630606, 1.430577755, 0.283174425, -0.38076368, 0.188697949
};

static const float s_b4[4] = {
    0.176825449, 0.109336324, 0.039349314, 0.579241753
};
// 上方四层权重/偏置是原网络数值基准，共 582 项；本次只补说明，不修改任何模型参数。

#pragma CODE_SECTION(DAB_NN_inference_FPU, ".TI.ramfunc")

//=============================================================================
// Fast RAM-resident FPU software forward inference implementation
//=============================================================================
static void DAB_NN_inference_FPU(const float in[DAB_NN_INPUT_DIM], float out[DAB_NN_OUTPUT_DIM])
{
    int i, j;

    // Layer 1: 3 -> 29 with ReLU
    for (i = 0; i < DAB_NN_LAYER1_OUT; i++)
    {
        float sum = s_b1[i];
        int col_offset = i * DAB_NN_INPUT_DIM; // 按输出神经元逐行排列权重，先加偏置，再累加本行各输入。
        sum += in[0] * s_w1[col_offset + 0];
        sum += in[1] * s_w1[col_offset + 1];
        sum += in[2] * s_w1[col_offset + 2];
        s_layer1[i] = (sum > 0.0f) ? sum : 0.0f; // ReLU：负值置零；第二、第三层使用相同激活。
    }

    // Layer 2: 29 -> 12 with ReLU
    for (i = 0; i < DAB_NN_LAYER2_OUT; i++)
    {
        float sum = s_b2[i];
        int col_offset = i * DAB_NN_LAYER1_OUT;
        for (j = 0; j < DAB_NN_LAYER1_OUT; j++)
        {
            sum += s_layer1[j] * s_w2[col_offset + j];
        }
        s_layer2[i] = (sum > 0.0f) ? sum : 0.0f;
    }

    // Layer 3: 12 -> 6 with ReLU
    for (i = 0; i < DAB_NN_LAYER3_OUT; i++)
    {
        float sum = s_b3[i];
        int col_offset = i * DAB_NN_LAYER2_OUT;
        for (j = 0; j < DAB_NN_LAYER2_OUT; j++)
        {
            sum += s_layer2[j] * s_w3[col_offset + j];
        }
        s_layer3[i] = (sum > 0.0f) ? sum : 0.0f;
    }

    // Layer 4: 6 -> 4 (Linear output layer)
    for (i = 0; i < DAB_NN_OUTPUT_DIM; i++)
    {
        float sum = s_b4[i];
        int col_offset = i * DAB_NN_LAYER3_OUT;
        for (j = 0; j < DAB_NN_LAYER3_OUT; j++)
        {
            sum += s_layer3[j] * s_w4[col_offset + j];
        }
        out[i] = sum; // 最后一层不作 ReLU，输出顺序为 D1、D0、D2、T，小负值由后续容差检查处理。
    }
}

//=============================================================================
#endif // FPU 权重、层缓存与前向函数只在 FPU 配置编译。

// Initialization
//=============================================================================
void DAB_NN_init(void)
{
    memset(s_input, 0, sizeof(s_input));
    s_input[0] = 0x00e0U;
    s_input[1] = 0x0012U;
#ifndef DAB_USE_HARDWARE_NPU
    memset(s_layer1, 0, sizeof(s_layer1));
    memset(s_layer2, 0, sizeof(s_layer2));
    memset(s_layer3, 0, sizeof(s_layer3));
#endif
    memset(s_output, 0, sizeof(s_output));
    s_valid = s_fault = s_hasInput = false;
    g_nnInferenceCount = g_nnTimeoutCount = 0U;
    s_profileActive = s_benchJob = s_benchCancel = false;
#if DAB_NN_AUTO_BENCHMARK
    g_nnBenchmarkRequested = true; g_nnBenchmarkCancelRequested = false; // 开启NN耗时测试
#else
    g_nnBenchmarkRequested = g_nnBenchmarkCancelRequested = false; // 关闭NN耗时测试
#endif
    g_nnBenchmarkIterations = 1000U; g_nnBenchmarkWarmup = 10U;
    g_nnBenchmarkVin = DAB_NOMINAL_VIN;
    g_nnBenchmarkState = DAB_NN_BENCH_IDLE;
    g_nnBenchmarkCompleted = g_nnBenchmarkWarmupCompleted = 0U;
    g_nnBenchmarkRejectReason = 0U;
    memset((void *)g_nnBenchmarkOutput, 0, sizeof(g_nnBenchmarkOutput));
    g_nnBenchmarkOutputValid = 0U;
#if DAB_NN_AUTO_BENCHMARK
    memset((void *)g_nnBenchmarkE2eTicks, 0, sizeof(g_nnBenchmarkE2eTicks));
#endif
    g_nnTimingResetRequested = g_nnTimingResetAccepted = false;
    g_nnTimingSequence = 0U;
    // Shared free-running time source for NPU timeout and background telemetry.
    CPUTimer_stopTimer(CPUTIMER2_BASE);
    CPUTimer_disableInterrupt(CPUTIMER2_BASE);
    CPUTimer_clearOverflowFlag(CPUTIMER2_BASE);
    CPUTimer_selectClockSource(CPUTIMER2_BASE, CPUTIMER_CLOCK_SOURCE_SYS,
                              CPUTIMER_CLOCK_PRESCALER_1);
    CPUTimer_setPreScaler(CPUTIMER2_BASE, 0U);
    CPUTimer_setPeriod(CPUTIMER2_BASE, 0xFFFFFFFFUL); // 150 MHz 向下计数公共时间源，约 28.63 s 回绕，短期限用无符号差值计算。
    CPUTimer_setEmulationMode(CPUTIMER2_BASE, CPUTIMER_EMULATIONMODE_RUNFREE); // 调试暂停时继续计数，恢复运行后可能出现数据过旧或超时。
    CPUTimer_reloadTimerCounter(CPUTIMER2_BASE);
    CPUTimer_startTimer(CPUTIMER2_BASE);
    clearTiming();
#ifdef DAB_USE_HARDWARE_NPU
    s_busy = false;
    s_npuDoneStamped = false;
#if defined(__TI_COMPILER_VERSION__) && defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_RAM_RUNTIME
    // C28 的 memcpy 长度按 16 位存储单元计；链接器符号的地址给出镜像长度。
    // 先完成复制再注册/启动 NPU，保证普通 Flash 上电启动同样有效。
    memcpy(&DabNpuRunStart, &DabNpuLoadStart, (size_t)&DabNpuLoadSize);
#if DAB_NPU_RAM_CONSTANTS
    // 常量只在初始化时复制一次；四层仍逐次装载到 NPU 自身的参数/指令存储区。
    memcpy(&DabNpuConstRunStart, &DabNpuConstLoadStart, (size_t)&DabNpuConstLoadSize);
#endif
#endif
    TI_NPU_init(); // 仅真实模型分支初始化硬件；需要 DAB 专用头文件、模型库及完成通知。
#endif
}

static bool publishOutput(void)
{
    uint16_t i;
    bool masked;
    bool legal = DAB_nnOutputValid(s_output);
    if (s_fault) { s_valid = false; return false; } // 已有锁定异常不允许晚完成恢复为有效。
    if (!legal)
    {
        if (!s_benchJob)
        {
            s_fault = true;
            s_valid = false;
            return false; // 控制路径仍拒绝非法输出；隔离计时才允许继续采样。
        }
        s_valid = false;
    }
    else s_valid = true;
    masked = Interrupt_disableGlobal();
    for (i = 0U; i < DAB_NN_OUTPUT_DIM; i++) g_nnLastOutput[i] = s_output[i]; // 短暂关中断拷贝整套结果，避免控制取到两个版本拼成的四个量。
    g_nnInferenceCount++;
    if (!masked) Interrupt_enableGlobal();
    return true;
}

#pragma CODE_SECTION(DAB_NN_checkDeadline, ".TI.ramfunc")
bool DAB_NN_checkDeadline(void)
{
#ifdef DAB_USE_HARDWARE_NPU
    bool masked = Interrupt_disableGlobal();
    if (!s_fault && s_busy &&
        (uint32_t)(s_started - CPUTimer_getTimerCount(CPUTIMER2_BASE)) >
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_NPU_TIMEOUT_US)
    {
        g_nnTimeoutCount++; // 主循环和控制中断均可调用期限检查，超时只计一次并锁定故障。
        s_fault = true;
        s_valid = false; // 超时使旧结果也失效，未完成的输入/输出缓冲区仍由在途运算持有。
        // Keep the outstanding buffers owned, even if a late completion arrives.
    }
    if (!masked) Interrupt_enableGlobal();
#endif
    return !s_fault;
}

// Run from main with interrupts enabled. Input/output buffers are owned by
// this service and cannot be reused while an NPU operation is outstanding.
static void serviceInference(float vin_volts, bool force)
{
    float delta;
    uint32_t observedTick;
    bool valid;
    if (!DAB_NN_checkDeadline())
    {
        if (s_profileActive)
        {
            observedTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
            finishProfile(false, observedTick, observedTick);
        }
        return; // 超时任务不计入成功耗时，仍锁定且不复用 NPU 缓冲区。
    }
    if (!DAB_isFinite(vin_volts))
    { s_fault = true; s_valid = false; return; } // Vin 必须有限；真实训练范围仍需原始训练说明。
    if (vin_volts < 0.0f) vin_volts = 0.1f; // 零点附近标定可能为负，钳到 0，不锁网络故障。
#ifdef DAB_NPU_GENERATED_MODEL
    if (vin_volts < DAB_NPU_MIN_VIN || vin_volts > DAB_NPU_MAX_VIN)
    { s_fault = true; s_valid = false; return; } // 候选模型只在 90～140 V 做过量化与离线检查。
#endif
#ifdef DAB_USE_HARDWARE_NPU
    if (s_busy)
    {
        if (tvmgen_default_finished)
        {
            observedTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
            s_busy = false;
            valid = publishOutput();
            finishProfile(valid, observedTick, CPUTimer_getTimerCount(CPUTIMER2_BASE));
        } // 只有完成且未先超时才尝试发布，等待阶段不修改下一次输入。
        return;
    }
#endif
    delta = vin_volts - s_lastVin;
    if (!force && s_hasInput && delta < DAB_NN_REFRESH_DELTA_V && delta > -DAB_NN_REFRESH_DELTA_V) return; // Vin 变化不足 0.1 V 时复用缓存；当前 Vin 固定 90 V，通常只推理一次。
    s_lastVin = vin_volts;
    s_hasInput = true;
    // Preserve the original three-input normalization. The meaning/domain of
    // the constant inputs still requires the original training specification.
    s_profileActive = true;
    s_jobBeginTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
#ifdef DAB_NPU_FC_MODEL
#if DAB_NPU_DETAIL_PROFILE
    s_stageInputTicks = CPUTimer_getTimerCount(CPUTIMER2_BASE);
#endif
    DAB_FC_preparePackedInput(vin_volts, s_input);
#if DAB_NPU_DETAIL_PROFILE
    s_stageInputTicks -= CPUTimer_getTimerCount(CPUTIMER2_BASE);
#endif
#elif defined(DAB_NPU_DAB16_MODEL)
    memset(s_input, 0, sizeof(s_input));
    s_input[1] = vin_volts / 25.0f - 4.6f; // 两项常量已折入第一层，Vin 居中缩放；其余输入保持为零。
#else
    s_input[0] = -0.5f; // 保留原始常量归一化输入，具体物理意义不能从当前代码确认。
    s_input[1] = vin_volts / 140.0f; // Vin 按 140 V 归一化，不表示已知完整训练域为 0～140 V。
    s_input[2] = 0.285714f; // 第二个常量输入仍需训练资料解释，不随输出参考或负载自动更新。
#endif
    s_jobPrepTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
#ifdef DAB_USE_HARDWARE_NPU
    {
        int32_t status;
#if defined(DAB_NPU_GENERATED_MODEL) && DAB_NPU_DETAIL_PROFILE
        memset((void *)s_traceTicks, 0, sizeof(s_traceTicks));
        memset((void *)s_traceCalls, 0, sizeof(s_traceCalls));
        memset((void *)s_traceOpen, 0, sizeof(s_traceOpen));
#endif
        resetIsrStats();
        tvmgen_default_finished = 0;
        s_npuDoneStamped = false;
        s_started = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        s_jobRunTick = s_started;
        s_busy = true;
#if DAB_NPU_DETAIL_PROFILE
        s_traceTicks[DAB_NPU_INPUT] = s_stageInputTicks;
        s_traceCalls[DAB_NPU_INPUT] = 1U;
#endif
        if (s_fault)
        { finishProfile(false, s_started, s_started); return; }
        status = tvmgen_default_run(&s_npuInputs, &s_npuOutputs); // 启动真实 DAB 模型；返回码异常则锁定失效，不能换用电弧模型的库。
        s_jobReturnTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        if (status != 0)
        {
            s_fault = true; s_valid = false;
            finishProfile(false, s_jobReturnTick, s_jobReturnTick);
        }
    }
#else
    s_jobRunTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    DAB_NN_inference_FPU(s_input, s_output); // 默认软件基准在主循环运算，权重保持与 F28335 原程序一致。
    s_jobReturnTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    valid = publishOutput();
    finishProfile(valid, s_jobReturnTick, CPUTimer_getTimerCount(CPUTIMER2_BASE));
#endif
}

void DAB_NN_service(float vin_volts)
{
    serviceInference(vin_volts, false);
}

bool DAB_NN_isBenchmarkActive(void)
{
    return g_nnBenchmarkState == DAB_NN_BENCH_RUNNING;
}

bool DAB_NN_benchmarkService(bool outputsStopped)
{
    if (g_nnTimingResetRequested)
    {
        g_nnTimingResetRequested = false;
        g_nnTimingResetAccepted = DAB_NN_resetTiming();
    }
    if (g_nnBenchmarkRequested)
    {
        g_nnBenchmarkRequested = false;
        g_nnBenchmarkRejectReason = 0U;
        if (DAB_NN_isBenchmarkActive()) g_nnBenchmarkRejectReason = 1U;
        else if (!outputsStopped) g_nnBenchmarkRejectReason = 2U;
        else if (s_fault || s_profileActive) g_nnBenchmarkRejectReason = 3U;
#ifdef DAB_USE_HARDWARE_NPU
        else if (s_busy) g_nnBenchmarkRejectReason = 3U;
#endif
        else if (g_nnBenchmarkIterations == 0U || g_nnBenchmarkIterations > 10000U ||
                 g_nnBenchmarkWarmup > 1000U || !DAB_isFinite(g_nnBenchmarkVin) ||
                 g_nnBenchmarkVin <= 0.0f) g_nnBenchmarkRejectReason = 4U;
#ifdef DAB_NPU_GENERATED_MODEL
        else if (g_nnBenchmarkVin < DAB_NPU_MIN_VIN || g_nnBenchmarkVin > DAB_NPU_MAX_VIN)
            g_nnBenchmarkRejectReason = 4U; // 越界只拒绝测试请求，不提交模型运算。
#endif
        if (g_nnBenchmarkRejectReason != 0U)
        {
            if (!DAB_NN_isBenchmarkActive()) g_nnBenchmarkState = DAB_NN_BENCH_REJECTED;
        }
        else
        {
            // 请求只读取一次配置，测试途中编辑配置不会改变正在执行的一组样本。
            s_benchIterations = g_nnBenchmarkIterations;
            s_benchWarmup = g_nnBenchmarkWarmup;
            s_benchVin = g_nnBenchmarkVin;
            g_nnBenchmarkCompleted = g_nnBenchmarkWarmupCompleted = 0U;
            s_benchCancel = s_benchJob = false;
            memset((void *)g_nnBenchmarkOutput, 0, sizeof(g_nnBenchmarkOutput));
            g_nnBenchmarkOutputValid = 0U;
#if DAB_NN_AUTO_BENCHMARK
            memset((void *)g_nnBenchmarkE2eTicks, 0, sizeof(g_nnBenchmarkE2eTicks));
#endif
            clearTiming();
            g_nnBenchmarkState = DAB_NN_BENCH_RUNNING;
        }
    }
    if (g_nnBenchmarkCancelRequested)
    {
        g_nnBenchmarkCancelRequested = false;
        if (DAB_NN_isBenchmarkActive()) s_benchCancel = true;
    }
    if (!DAB_NN_isBenchmarkActive()) return false;
    if (!outputsStopped) s_benchCancel = true;
    if (s_benchCancel && !s_benchJob)
    {
        g_nnTimingSequence++; g_nnTiming.frozen = true; g_nnTimingSequence++;
        g_nnBenchmarkState = DAB_NN_BENCH_CANCELLED; return true;
    }
    s_benchJob = true;
    serviceInference(s_benchVin, true); // 绕过 Vin 缓存，每次主循环最多一次前向；NPU 忙时只查询完成。
    if (s_fault) g_nnBenchmarkState = DAB_NN_BENCH_FAILED;
    return true;
}

#pragma CODE_SECTION(DAB_NN_getOutput, ".TI.ramfunc")
bool DAB_NN_getOutput(float output_results[DAB_NN_OUTPUT_DIM])
{
    uint16_t i;
    bool valid;
    bool masked = Interrupt_disableGlobal();
    valid = s_valid && !s_fault; // 只有已完成且未锁定异常的缓存可交给控制，读取本身不会发起新推理。
    if (valid)
        for (i = 0U; i < DAB_NN_OUTPUT_DIM; i++) output_results[i] = g_nnLastOutput[i];
    if (!masked) Interrupt_enableGlobal();
    return valid;
}

#pragma CODE_SECTION(DAB_NN_hasFault, ".TI.ramfunc")
bool DAB_NN_hasFault(void) { return s_fault; }
