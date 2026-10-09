#include "dab_control.h"
#include "dab_pwm.h"
#include "dab_adc.h"
#include "dab_nn.h"
#include "dab_protect.h"
#include "dab_math.h"

volatile Dab_State_e g_dabState = DAB_STATE_INIT;
volatile Dab_PwmParams_t g_pwmParams; // 最新计算/请求参数；实际装载进度应另看 g_pwmAppliedParams 和序号。
volatile Dab_PiController_t g_piCtrl;
// CCS watch-window commands. Rejected requests are consumed; inspect state.
volatile bool g_startRequested = false;
volatile bool g_stopRequested = false;
static uint32_t s_softCnt; // 仅随新装载进度增加，正常约 100 ms；调用控制函数并不必然推进。
static uint32_t s_lastAppliedSequence;
volatile Dab_FaultRecord_t g_firstFault;
volatile uint16_t g_startRejectReason;

void DAB_Control_resetFaultRecord(void)
{
    DAB_PWM_resetWindowDiag(); // 同时清除窗口现场，避免人工恢复后把两次故障记录混在一起。
    g_firstFault.reason = DAB_FAULT_NONE;
    g_firstFault.state = DAB_STATE_INIT;
    g_firstFault.tick = g_firstFault.adcFrame = g_firstFault.pwmSequence = 0U;
    g_firstFault.ilRaw = g_firstFault.voutRaw = 0U;
}

void DAB_Control_init(void)
{
    g_dabState = DAB_STATE_STANDBY;
    g_piCtrl.kp = 0.00005f; g_piCtrl.ki = 0.0001f; g_piCtrl.ref = 40.0f; // 参考为输出电压；ki 是每次控制调用的增量系数，默认开环不保证稳到 40 V。
    g_piCtrl.fed = g_piCtrl.err = g_piCtrl.integral = g_piCtrl.out = 0.0f;
    g_pwmParams.D1 = g_pwmParams.D2 = 1.0f; // 软启动从桥内相移参数 1 开始；D1/D2 不是单管常规占空比。
    g_pwmParams.D1_pha = g_pwmParams.D2_pha = g_pwmParams.D0 = 0.0f;
    g_pwmParams.T_gain = 1.0f; g_pwmParams.F_duty = 0.0f;
    g_pwmParams.tbprd_var = DAB_BASE_TBPRD;
    s_softCnt = 0U;
    s_lastAppliedSequence = 0U;
    g_startRejectReason = 0U;
    DAB_Control_resetFaultRecord();
    g_startRequested = g_stopRequested = false;
}

void DAB_Control_setRef(float ref_val)
{
    bool masked;
    if (!DAB_isFinite(ref_val)) return;
    masked = Interrupt_disableGlobal();
    g_piCtrl.ref = DAB_clamp(ref_val, 0.0f, 60.0f); // 接受有限的 0～60 V 参考；保护仍按瞬时采样检查。
    if (!masked) Interrupt_enableGlobal();
}

bool DAB_Control_start(void)
{
    float outputs[DAB_NN_OUTPUT_DIM];
    bool accepted = false;
    bool masked = Interrupt_disableGlobal();
#if defined(DAB_NPU_DAB16_MODEL) && !DAB_NPU_POWER_CONTROL_APPROVED
    if (true) g_startRejectReason = 7U; // 当前 INT8 候选模型仅供核对与计时，不能用板确认宏绕过精度验收。
#else
    if (!DAB_BOARD_CONFIG_CONFIRMED) g_startRejectReason = 1U; // 未核对接线和硬件时拒绝功率输出；默认宏为 0。
#endif
    else if (DAB_NN_isBenchmarkActive()) g_startRejectReason = 6U; // 耗时测试期间拒绝启动功率输出。
    else if (g_dabState != DAB_STATE_STANDBY) g_startRejectReason = 2U; // 只允许待机启动，不能从 FAULT 直接跳到运行。
    else if (!DAB_ADC_isReady()) g_startRejectReason = 3U; // 要求连续 50 帧有效且数据足够新，累计历史帧数本身不够。
    else if (!DAB_NN_checkDeadline() || !DAB_NN_getOutput(outputs)) g_startRejectReason = 4U; // 必须已有完整有效 NN 结果，NPU 超时也不能放行。
    else if (DAB_Protect_checkFault()) g_startRejectReason = 5U; // 外部故障或软件锁存尚未解除时拒绝启动。
    else
    {
        g_startRejectReason = 0U;
        s_softCnt = 0U;
        s_lastAppliedSequence = g_pwmAppliedSequence;
        g_piCtrl.integral = g_piCtrl.out = 0.0f;
        g_dabState = DAB_STATE_SOFT_START;
        DAB_PWM_enable(); // request only: release after the first packet loads // 只提出使能请求，首个完整包经过装载事件且保护复核后才清 OST。
        accepted = true;
    }
    if (!masked) Interrupt_enableGlobal();
    return accepted;
}

void DAB_Control_stop(void)
{
    bool masked = Interrupt_disableGlobal();
    DAB_PWM_disable(); // 立即强制四桥软件关断；停止/故障不等待下一次普通参数更新。
    // A stop command must not erase a latched fault.
    if (g_dabState != DAB_STATE_FAULT) g_dabState = DAB_STATE_STANDBY; // 正常停机回待机，故障停机仍保留 FAULT 与首次故障。
    g_piCtrl.integral = g_piCtrl.out = 0.0f;
    s_softCnt = 0U;
    if (!masked) Interrupt_enableGlobal();
}

#pragma CODE_SECTION(DAB_Control_fault, ".TI.ramfunc")
void DAB_Control_fault(void)
{
    DAB_Control_faultReason(g_protectFlags.bit.H_OCP_Flag ? DAB_FAULT_HARDWARE : DAB_FAULT_LIMIT);
}

#pragma CODE_SECTION(DAB_Control_faultReason, ".TI.ramfunc")
void DAB_Control_faultReason(Dab_FaultReason_e reason)
{
    if (g_firstFault.reason == DAB_FAULT_NONE)
    {
        g_firstFault.state = g_dabState;
        g_firstFault.tick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        g_firstFault.adcFrame = g_adcFrameCount;
        g_firstFault.pwmSequence = g_pwmAppliedSequence;
        g_firstFault.ilRaw = g_sensing.il_raw;
        g_firstFault.voutRaw = g_sensing.vout_n_raw;
        g_firstFault.reason = reason; // 最后发布原因，保留最先触发的现场，不被后续异常覆盖。
    }
    DAB_PWM_disable();
    g_protectFlags.bit.Stop_Flag = 1U;
    g_dabState = DAB_STATE_FAULT;
    g_piCtrl.integral = g_piCtrl.out = 0.0f;
}

#pragma CODE_SECTION(DAB_Control_step, ".TI.ramfunc")
void DAB_Control_step(void)
{
    float outputs[DAB_NN_OUTPUT_DIM], ramp, target, error, integral, duty, invT;
    Dab_PwmParams_t params;
    if (DAB_Protect_checkFault()) { DAB_Control_fault(); return; }
    if (g_dabState != DAB_STATE_SOFT_START && g_dabState != DAB_STATE_RUN) return; // 待机只检测保护，不产生新的运行参数。
    if (!DAB_ADC_isReady()) { DAB_Control_faultReason(DAB_FAULT_ADC); return; }
    if (!DAB_PWM_checkDeadline()) return; // 参数提交或装载停滞时已进入故障，不能继续沿用旧波形。
    if (!DAB_NN_checkDeadline() || !DAB_NN_getOutput(outputs) ||
        !DAB_isFinite(g_sensing.vout_n_ave) || !DAB_isFinite(g_piCtrl.ref) ||
        !DAB_isFinite(g_piCtrl.kp) || !DAB_isFinite(g_piCtrl.ki) ||
        !DAB_isFinite(g_piCtrl.integral))
    { DAB_Control_faultReason(DAB_FAULT_NN); return; }
    ramp = (float)s_softCnt / (float)DAB_SOFT_CNT_MAX; // 渐变比例为 0～1，同时平滑参考、相移和开关周期。
    target = DAB_clamp(g_piCtrl.ref, 0.0f, 60.0f) * ramp;
    error = DAB_clamp(target - g_sensing.vout_n_ave, -DAB_ERR_LIMIT, DAB_ERR_LIMIT); // 反馈使用 50 点平均电压，误差限为 ±40；滤波延迟需纳入闭环设计。
    integral = g_piCtrl.integral;
#if DAB_CONTROL_MODE == DAB_MODE_NN_CLOSED_LOOP
    duty = DAB_piStep(error, g_piCtrl.kp, g_piCtrl.ki, &integral, DAB_DUTY_MAX); // 闭环修正 0～0.15，包含积分边界处理；当前没有反向功率控制设计。
#else
    duty = 0.0f; integral = 0.0f; // 默认开环保持旧程序最终 F_duty=0 行为，ref 只参与渐变误差显示。
#endif
    g_piCtrl.fed = g_sensing.vout_n_ave; g_piCtrl.err = error;
    g_piCtrl.integral = integral; g_piCtrl.out = duty;
    invT = 1.0f / outputs[DAB_NN_IDX_T];
    // D1/D2 从 1 过渡到归一化相移减 PI，D0 从 0 过渡到归一化相移加 PI。
    // 0.001/0.999 是当前数值边界，实际允许脉宽、相移和变化速度仍需功率板验证。 // NN 相移先除以 T 归一化，再加入 PI 修正；T 已在结果发布时检查范围。
    params.D1 = (1.0f - ramp) + ramp * DAB_clamp(outputs[DAB_NN_IDX_D1] * invT - duty, 0.001f, 0.999f);
    params.D2 = (1.0f - ramp) + ramp * DAB_clamp(outputs[DAB_NN_IDX_D2] * invT - duty, 0.001f, 0.999f);
    params.D0 = ramp * DAB_clamp(outputs[DAB_NN_IDX_D0] * invT + duty, 0.0f, 0.999f); // 桥间相移随软启动增加，PI 对 D0 的修正方向与 D1/D2 相反。
    params.D1_pha = 1.0f - params.D1; params.D2_pha = 1.0f - params.D2; // 互补比较位置，与另一比较值合成桥内相移波形。
    params.T_gain = 1.0f + ramp * (outputs[DAB_NN_IDX_T] - 1.0f); // 从基准周期渐变到模型周期，T 越大，开关频率越低。
    params.F_duty = duty;
    params.tbprd_var = (uint32_t)(params.T_gain * (float)DAB_BASE_TBPRD); // 以基准 2500 个计数换算整数周期，保留原来的截断行为。
    if (!DAB_PWM_updateModulation(&params)) { DAB_Control_faultReason(DAB_FAULT_MODULATION); return; }
    g_pwmParams = params; // 这是请求值；寄存器由另一个 ePWM 中断提交，不能把它当作已生效值。
    if (DAB_PWM_isEnabled() && g_pwmAppliedSequence != s_lastAppliedSequence && s_softCnt < DAB_SOFT_CNT_MAX)
    { s_softCnt++; s_lastAppliedSequence = g_pwmAppliedSequence; } // 只在输出已启用且观察到新装载序号时推进，更新停滞不产生虚假 RUN。
    if (s_softCnt == DAB_SOFT_CNT_MAX) g_dabState = DAB_STATE_RUN; // 这里只表示渐变完成，不证明电压闭环、效率或实际波形已验收。
}
