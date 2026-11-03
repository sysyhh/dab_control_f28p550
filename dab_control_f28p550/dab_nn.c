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
static float s_input[DAB_NPU_RUNTIME_INPUT_DIM]; // NPU 模型输入宽度由生成契约给出，完成前不得改写。
#else
static float s_input[DAB_NN_INPUT_DIM]; // FPU 使用原始三项归一化输入。
#endif
#ifndef DAB_USE_HARDWARE_NPU
static float s_layer1[DAB_NN_LAYER1_OUT];
static float s_layer2[DAB_NN_LAYER2_OUT];
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

// Network weights and biases (open-source placeholder: 3 -> 8 -> 8 -> 4)
// Replace with trained weights and biases exported from your model pipeline.
#ifndef DAB_USE_HARDWARE_NPU
static const float s_w1[DAB_NN_LAYER1_OUT * DAB_NN_INPUT_DIM] = { 0.0f };
static const float s_b1[DAB_NN_LAYER1_OUT] = { 0.0f };

static const float s_w2[DAB_NN_LAYER2_OUT * DAB_NN_LAYER1_OUT] = { 0.0f };
static const float s_b2[DAB_NN_LAYER2_OUT] = { 0.0f };

static const float s_w3[DAB_NN_OUTPUT_DIM * DAB_NN_LAYER2_OUT] = { 0.0f };
// Safe nominal output bias placeholder: [D1=1.0, D0=0.0, D2=1.0, T=1.0]
static const float s_b3[DAB_NN_OUTPUT_DIM] = { 1.0f, 0.0f, 1.0f, 1.0f };

#pragma CODE_SECTION(DAB_NN_inference_FPU, ".TI.ramfunc")

//=============================================================================
// Fast RAM-resident FPU software forward inference implementation
//=============================================================================
static void DAB_NN_inference_FPU(const float in[DAB_NN_INPUT_DIM], float out[DAB_NN_OUTPUT_DIM])
{
    int i, j;

    // Layer 1: 3 -> 8 with ReLU
    for (i = 0; i < DAB_NN_LAYER1_OUT; i++)
    {
        float sum = s_b1[i];
        int col_offset = i * DAB_NN_INPUT_DIM; // 按输出神经元逐行排列权重，先加偏置，再累加本行各输入。
        sum += in[0] * s_w1[col_offset + 0];
        sum += in[1] * s_w1[col_offset + 1];
        sum += in[2] * s_w1[col_offset + 2];
        s_layer1[i] = (sum > 0.0f) ? sum : 0.0f; // ReLU：负值置零。
    }

    // Layer 2: 8 -> 8 with ReLU
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

    // Layer 3: 8 -> 4 (Linear output layer)
    for (i = 0; i < DAB_NN_OUTPUT_DIM; i++)
    {
        float sum = s_b3[i];
        int col_offset = i * DAB_NN_LAYER2_OUT;
        for (j = 0; j < DAB_NN_LAYER2_OUT; j++)
        {
            sum += s_layer2[j] * s_w3[col_offset + j];
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
#ifndef DAB_USE_HARDWARE_NPU
    memset(s_layer1, 0, sizeof(s_layer1));
    memset(s_layer2, 0, sizeof(s_layer2));
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
    // Three-input feature normalization using configurable macros.
    s_profileActive = true;
    s_jobBeginTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
#ifdef DAB_NPU_FC_MODEL
    memset(s_input, 0, sizeof(s_input));
    s_input[0] = DAB_NN_INPUT0_CONST; // 原生三维输入；多出的硬件对齐通道严格补零。
    s_input[1] = vin_volts / DAB_NN_VIN_NORM_SCALE;
    s_input[2] = DAB_NN_INPUT2_CONST;
#else
    s_input[0] = DAB_NN_INPUT0_CONST;
    s_input[1] = vin_volts / DAB_NN_VIN_NORM_SCALE;
    s_input[2] = DAB_NN_INPUT2_CONST;
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
        if (s_fault)
        { finishProfile(false, s_started, s_started); return; }
        status = tvmgen_default_run(&s_npuInputs, &s_npuOutputs); // 启动 NPU 模型；返回码异常则锁定失效。
        s_jobReturnTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        if (status != 0)
        {
            s_fault = true; s_valid = false;
            finishProfile(false, s_jobReturnTick, s_jobReturnTick);
        }
    }
#else
    s_jobRunTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    DAB_NN_inference_FPU(s_input, s_output); // 默认软件基准在主循环运算。
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
