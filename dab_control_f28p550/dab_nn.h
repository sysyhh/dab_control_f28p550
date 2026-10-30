//#############################################################################
//
// FILE:   dab_nn.h
//
// TITLE:  Embedded Neural Network Interface for DAB Converter on F28P550
//         Supports dual-mode: FPU baseline (RAM-accelerated) and On-Chip NPU.
//
//#############################################################################

#ifndef DAB_NN_H_
#define DAB_NN_H_

#include <stdint.h>
#include "dab_types.h"
#include "dab_npu_trace.h"

//=============================================================================
// Acceleration Mode Selector
// Uncomment DAB_USE_HARDWARE_NPU when using the compiled TI NPU model (mod.a)
//=============================================================================
//#define DAB_USE_HARDWARE_NPU
// 默认保留 FPU 基准；CPU1_LAUNCHXL_NPU_FLASH 使用 DAB16 专用库，输入 16 项、输出 4 项 FLOAT32。
#ifdef DAB_NPU_DAB16_MODEL
#ifndef DAB_USE_HARDWARE_NPU
#error "DAB16 model requires DAB_USE_HARDWARE_NPU"
#endif
#include "model/generated/npu/dab_npu_contract.h"
#if (DAB_NPU_RUNTIME_INPUT_DIM != 16U && DAB_NPU_RUNTIME_INPUT_DIM != 4U) || DAB_NPU_RUNTIME_OUTPUT_DIM != 4U
#error "NPU model dimensions changed; review the adapter"
#endif
#endif

// Model Matrix Dimensions (3 -> 29 -> 12 -> 6 -> 4)
#define DAB_NN_INPUT_DIM        3
#define DAB_NN_LAYER1_OUT       29
#define DAB_NN_LAYER2_OUT       12
#define DAB_NN_LAYER3_OUT       6
#define DAB_NN_OUTPUT_DIM       4

// Output index semantics:
// output[0] = D1 (Primary internal phase shift)
// output[1] = D0 (Primary-to-secondary phase shift)
// output[2] = D2 (Secondary internal phase shift)
// output[3] = T  (Period gain for variable-frequency control)
#define DAB_NN_IDX_D1           0 // 原边桥内相移，控制映射先除以 T。
#define DAB_NN_IDX_D0           1 // 原副边桥间相移，顺序不能和 D2 互换。
#define DAB_NN_IDX_D2           2 // 副边桥内相移，允许 FLOAT 数值小负容差。
#define DAB_NN_IDX_T            3 // 周期比例；T 越大，开关频率越低。

//=============================================================================
// Public Functions
//=============================================================================
void DAB_NN_init(void);
// Background service only: never wait for NPU inside the control ISR.
void DAB_NN_service(float vin_volts); // 仅后台调用，输入变化后推理；NPU 忙时保留缓冲区不重复启动。
bool DAB_NN_getOutput(float output_results[DAB_NN_OUTPUT_DIM]); // 取最新完整缓存，返回 false 时不能使用输出数组。
bool DAB_NN_hasFault(void);
// Safe from the control ISR: timeout does not depend on foreground progress.
bool DAB_NN_checkDeadline(void); // 控制中断也可检查超时，晚完成不解除异常，需要排查后复位。
extern volatile uint32_t g_nnInferenceCount;
extern volatile uint32_t g_nnTimeoutCount;
extern volatile float g_nnLastOutput[DAB_NN_OUTPUT_DIM]; // 调试只读；不要通过 CCS 修改，运行代码请使用 getOutput。
extern volatile float g_nnBenchmarkOutput[DAB_NN_OUTPUT_DIM]; // 有限测试最后一次有效输出；普通推理不得覆盖。
extern volatile uint16_t g_nnBenchmarkOutputValid;

// Timer2 以 SYSCLK 向下计数；所有 Tick 差值均按 uint32_t 处理回绕。
typedef struct {
    uint32_t samples, lastTicks, minTicks, maxTicks;
    uint64_t totalTicks; // 64 位累加，避免多次测量后 32 位总计数溢出。
    float meanUs; // 在计时区间外换算；原始 Tick 保留，不自动扣除读取开销。
} Dab_NnTimeStats_t;

typedef struct {
    uint32_t timerHz, timerReadOverheadTicks;
    uint16_t backend; // 0：当前 FPU；1：真实 NPU 分支，不能用软件仿真冒充。
    uint16_t revision;
    bool frozen; // 有限测试结束后冻结结果；普通控制推理继续，但不覆盖这份统计。
    uint32_t rejectedOutputs;
    Dab_NnTimeStats_t prepare; // 所选模型的输入准备，不含 ADC 或采样滤波。
    Dab_NnTimeStats_t fpuForward; // FPU 前向调用区间，包含期间中断占用。
    Dab_NnTimeStats_t npuSubmit; // tvmgen_default_run 调用时间，含首层装载，不含后续 ISR。
    Dab_NnTimeStats_t npuObserved; // 提交至后台发现完成，包含轮询发现延迟。
    Dab_NnTimeStats_t npuCompletion; // 提交至完成 ISR 钩子；含硬件等待与层间 ISR。
    Dab_NnTimeStats_t npuIsr; // 每次推理全部完成 ISR 的 CPU 累计，不含 NPU 硬件等待。
    Dab_NnTimeStats_t publish; // 输出校验并发布到控制缓存。
    Dab_NnTimeStats_t endToEnd; // 输入准备开始至有效结果发布，统计更新不计入。
    uint32_t npuIsrInvocations; // 本批正式样本的 ISR 总次数。
    uint32_t npuIsrMaxSingleTicks; // 本批单次 ISR 最大 CPU 时间。
    uint16_t npuIsrLastCount; // 最近一次推理的 ISR 次数。
    uint16_t npuIsrLastLayerCount[5]; // 进入 ISR 时 tinie_curr_layer 的次数，0 应保持为 0。
} Dab_NnTiming_t;
extern volatile Dab_NnTiming_t g_nnTiming;
typedef struct {
    bool instrumented; // 由生成库的编译标记决定；false 时所有分段均无测量意义。
    uint32_t invalidPairs;
    uint16_t lastCalls[DAB_NPU_TRACE_SLOTS]; // PARAMS/INS 等每个模型任务通常调用四次。
    Dab_NnTimeStats_t stage[DAB_NPU_TRACE_SLOTS]; // 同一任务内同类步骤累加后记录一份样本。
} Dab_NpuDetail_t;
extern volatile Dab_NpuDetail_t g_nnNpuDetail;
extern volatile uint32_t g_nnTimingSequence; // 奇数表示正在更新；CCS 建议完成后暂停再读取。
extern volatile bool g_nnTimingResetRequested, g_nnTimingResetAccepted;
bool DAB_NN_resetTiming(void); // 仅后台且无在途任务/重复测试时允许清统计。
void DAB_NN_noteNpuCompletion(void); // 可选：真实完成 ISR 中、finished 发布前调用，仅记时，不等待。

typedef enum {
    DAB_NN_BENCH_IDLE=0, DAB_NN_BENCH_RUNNING, DAB_NN_BENCH_DONE,
    DAB_NN_BENCH_REJECTED, DAB_NN_BENCH_FAILED, DAB_NN_BENCH_CANCELLED
} Dab_NnBenchmarkState_e;
extern volatile bool g_nnBenchmarkRequested, g_nnBenchmarkCancelRequested;
extern volatile uint32_t g_nnBenchmarkIterations, g_nnBenchmarkWarmup;
extern volatile float g_nnBenchmarkVin;
extern volatile Dab_NnBenchmarkState_e g_nnBenchmarkState;
extern volatile uint32_t g_nnBenchmarkCompleted, g_nnBenchmarkWarmupCompleted;
extern volatile uint16_t g_nnBenchmarkRejectReason; // 0 无；1 正在测试；2 输出未停；3 NN 忙/故障；4 参数错误。
bool DAB_NN_isBenchmarkActive(void);
// 仅后台调用。true 表示本轮已由测试接管 NN 服务，主循环不再重复调用普通服务。
bool DAB_NN_benchmarkService(bool outputsStopped);

#endif // DAB_NN_H_
