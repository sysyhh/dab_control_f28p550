#include "dab_protect.h"
#include "dab_adc.h"
#include "dab_control.h"
#include "dab_pwm.h"
#include "dab_nn.h"
#include "dab_math.h"

volatile Dab_ProtectFlags_t g_protectFlags;
#define THRESHOLD_VOUT_OVP 400.0f // 输出电压瞬时值达到 80 V 判故障；准确性依赖实际标定。
#define THRESHOLD_IL_OCP 45.0f // 电感电流 ±25 A 软件门限，采样间尖峰仍需连续硬件保护。
#define THRESHOLD_VIN_UVP 0.0f // DAB_HAS_VIN_SENSING 为 1 时，用瞬时原边电压判断输入欠压。
static bool s_recoveryCandidate;
static uint32_t s_recoveryTick;

void DAB_Protect_init(void)
{
    g_protectFlags.all = 0U;
    s_recoveryCandidate = false;
    GPIO_setPinConfig(DAB_HW_TRIP_PIN_CONFIG);
    GPIO_setPadConfig(DAB_HW_TRIP_GPIO, GPIO_PIN_TYPE_PULLUP);
    GPIO_setDirectionMode(DAB_HW_TRIP_GPIO, GPIO_DIR_MODE_IN);
    GPIO_setQualificationMode(DAB_HW_TRIP_GPIO, GPIO_QUAL_ASYNC); // 故障输入不等 CPU 采样滤波，异步进入硬件关断路径。
    // TZ1 is active low. Route directly, independent of CPU interrupt latency.
    XBAR_setInputPin(INPUTXBAR_BASE, XBAR_INPUT1, DAB_HW_TRIP_GPIO); // GPIO60 低电平送 TZ1，四桥关断动作在 PWM 初始化中配置。
}

#pragma CODE_SECTION(sensingFault, ".TI.ramfunc")
static bool sensingFault(void)
{
    return !DAB_isFinite(g_sensing.vout_n) || !DAB_isFinite(g_sensing.il) ||
           g_sensing.vout_n >= THRESHOLD_VOUT_OVP ||
           g_sensing.il >= THRESHOLD_IL_OCP || g_sensing.il <= -THRESHOLD_IL_OCP;
}

#pragma CODE_SECTION(DAB_Protect_checkFault, ".TI.ramfunc")
bool DAB_Protect_checkFault(void)
{
    bool hardwareFault = DAB_PWM_hardwareFault(); // 检查引脚当前低电平及旧脉冲留下的来源锁存；H_OCP 不是已配置的片内 CMPSS。
    if (hardwareFault)
    { g_protectFlags.bit.H_OCP_Flag = 1U; g_protectFlags.bit.Stop_Flag = 1U; }
    if (g_adcFrameCount != 0U) // 至少发布过有效帧才按物理值检查门限；运行是否足够新另由 ADC 就绪判断。
    {
        if (!DAB_isFinite(g_sensing.vout_n) || g_sensing.vout_n >= THRESHOLD_VOUT_OVP)
        { g_protectFlags.bit.Vout_OVP_Flag = 1U; g_protectFlags.bit.Stop_Flag = 1U; }
        if (!DAB_isFinite(g_sensing.il) || g_sensing.il >= THRESHOLD_IL_OCP || g_sensing.il <= -THRESHOLD_IL_OCP)
        { g_protectFlags.bit.L_OCP_Flag = 1U; g_protectFlags.bit.Stop_Flag = 1U; }
// #if DAB_HAS_VIN_SENSING
//         if (!DAB_isFinite(g_sensing.vin) || g_sensing.vin < THRESHOLD_VIN_UVP)
//         { g_protectFlags.bit.Vin_UVP_Flag = 1U; g_protectFlags.bit.Stop_Flag = 1U; }
// #endif
    }
    // 恢复期间软件关断和首次记录始终保留；输出已关闭时可重置来源锁存，重新监测短故障脉冲。
    if (GPIO_readPin(DAB_HW_TRIP_GPIO) == 0U || sensingFault() || !DAB_ADC_isReady())
        s_recoveryCandidate = false;
    else if (hardwareFault)
    {
        s_recoveryCandidate = false;
        // Software OST, Stop_Flag and first-fault record remain latched.
        // Re-arm the source latch while off so a new short pulse restarts
        // the recovery interval instead of hiding behind an old source flag.
        if (g_dabState == DAB_STATE_FAULT && DAB_PWM_clearHardwareFault())
        { s_recoveryTick = CPUTimer_getTimerCount(CPUTIMER2_BASE); s_recoveryCandidate = true; }
    }
    else if (!s_recoveryCandidate)
    { s_recoveryTick = CPUTimer_getTimerCount(CPUTIMER2_BASE); s_recoveryCandidate = true; }
    return g_protectFlags.bit.Stop_Flag != 0U; // 故障一旦锁存，即使瞬时量恢复也仍要求停机，直到人工清除成功。
}

bool DAB_Protect_clearFault(void)
{
    bool accepted = false;
    bool masked = Interrupt_disableGlobal();
    // Recheck now; a command cannot reuse a qualification from stale data.
    DAB_Protect_checkFault();
    // 清除请求当下重新检查，不能复用旧的正常资格。
    // 需要连续正常至少 5 ms、ADC 连续 50 帧且新鲜、PWM 停止、NN 健康、故障输入高。
    if (s_recoveryCandidate &&
        (uint32_t)(s_recoveryTick - CPUTimer_getTimerCount(CPUTIMER2_BASE)) >=
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_FAULT_RECOVERY_US &&
        !DAB_PWM_isEnabled() && g_dabState != DAB_STATE_RUN &&
        g_dabState != DAB_STATE_SOFT_START && DAB_ADC_isReady() &&
        !sensingFault() && !DAB_NN_hasFault() &&
        GPIO_readPin(DAB_HW_TRIP_GPIO) != 0U && DAB_PWM_clearHardwareFault())
    {
        g_protectFlags.all = 0U; // 仅所有恢复条件成立才清软件标志；不能在信号恢复的第一帧就清除。
        DAB_Control_resetFaultRecord();
        g_dabState = DAB_STATE_STANDBY; // 清除后回待机，保持关断；需要新的启动命令才能重新输出。
        accepted = true;
    }
    if (!masked) Interrupt_enableGlobal();
    return accepted;
}
