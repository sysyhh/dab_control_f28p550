#include "dab_pwm.h"
#include "dab_control.h"
#include "dab_adc.h"
#include "dab_protect.h"
#include "dab_nn.h"
#include "dab_math.h"

#if defined(__TI_COMPILER_VERSION__) && defined(DEBUG)
// 保留 Driverlib 的地址检查，但在本文件展开，避免实时写入反复跳到 Flash 检查。
#pragma FUNC_ALWAYS_INLINE(EPWM_isBaseValid)
#endif

typedef struct
{
    uint16_t period, cmpA2, cmpB2, cmpA4, cmpB4, phase34;
    uint32_t sequence; // 参数包版本号，区分刚计算、已提交和已观察到装载的版本。
    Dab_PwmParams_t params;
} DAB_PwmPacket;
static volatile DAB_PwmPacket s_pending; // EPWM1 控制中断产生完整请求，等待 EPWM7 中断提交。
static DAB_PwmPacket s_staged; // 已经写入寄存器并发出装载请求的参数，等待后续零点确认。
static bool s_waitingLoad; // 前一包未确认装载前不再写下一包，避免覆盖同一装载事务。
static uint32_t s_nextSequence, s_pendingTick, s_stagedTick;
static volatile bool s_pendingReady, s_enableRequested, s_releaseAtZero, s_enabled;
volatile uint32_t g_pwmLateCommitCount = 0U;
volatile Dab_PwmWindowDiag_t g_pwmWindowDiag;
volatile uint32_t g_pwmUpdateTimeoutCount, g_pwmAppliedSequence, g_controlHeartbeat;
volatile uint32_t g_controlLastTick;
volatile Dab_PwmParams_t g_pwmAppliedParams;
static const uint32_t s_bases[4] = {DAB_PWM_LEG1_BASE, DAB_PWM_LEG2_BASE, DAB_PWM_LEG3_BASE, DAB_PWM_LEG4_BASE};

void DAB_PWM_resetWindowDiag(void)
{
    g_pwmWindowDiag.stage = 0U;
    g_pwmWindowDiag.entryCounter = g_pwmWindowDiag.failCounter = 0U;
    g_pwmWindowDiag.failDirection = 0U;
    g_pwmWindowDiag.entryTick = g_pwmWindowDiag.failTick = 0U;
}

static void configLeg(uint32_t base)
{
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZA, EPWM_TZ_ACTION_LOW); // 发生 Trip 时 A/B 都强制低；实际驱动关断极性须按原理图确认。
    EPWM_setTripZoneAction(base, EPWM_TZ_ACTION_EVENT_TZB, EPWM_TZ_ACTION_LOW);
    EPWM_enableTripZoneSignals(base, EPWM_TZ_SIGNAL_OSHT1); // 使能低有效 TZ1 一次性锁存关断，来源是 GPIO60 的 Input XBAR1。
    EPWM_forceTripZoneEvent(base, EPWM_TZ_FORCE_EVENT_OST); // 初始化先强制软件关断，避免引脚配置期间出现开关输出。
    EPWM_setPeriodLoadMode(base, EPWM_PERIOD_DIRECT_LOAD); // 计数尚未启动时先直接写入初始活动值，之后才改为 Shadow。
    EPWM_setTimeBasePeriod(base, DAB_BASE_TBPRD);
    EPWM_setTimeBaseCounter(base, 0U);
    EPWM_setTimeBaseCounterMode(base, EPWM_COUNTER_MODE_UP_DOWN); // 上下计数：fsw=150 MHz/(2×TBPRD)，基准 2500 对应 30 kHz。
    EPWM_setClockPrescaler(base, EPWM_CLOCK_DIVIDER_1, EPWM_HSCLOCK_DIVIDER_1);
    EPWM_disableCounterCompareShadowLoadMode(base, EPWM_COUNTER_COMPARE_A);
    EPWM_disableCounterCompareShadowLoadMode(base, EPWM_COUNTER_COMPARE_B);
    EPWM_setCounterCompareValue(base, EPWM_COUNTER_COMPARE_A, DAB_BASE_TBPRD);
    EPWM_setCounterCompareValue(base, EPWM_COUNTER_COMPARE_B, 0U);
    EPWM_setPeriodLoadMode(base, EPWM_PERIOD_SHADOW_LOAD); // 运行期写新周期先暂存，等共同装载边界再生效。
    EPWM_setCounterCompareShadowLoadMode(base, EPWM_COUNTER_COMPARE_A, EPWM_COMP_LOAD_ON_CNTR_ZERO);
    EPWM_setCounterCompareShadowLoadMode(base, EPWM_COUNTER_COMPARE_B, EPWM_COMP_LOAD_ON_CNTR_ZERO);
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_HIGH, EPWM_AQ_OUTPUT_ON_TIMEBASE_DOWN_CMPA); // 下降计数到 CMPA 时 A 置高，上升到 CMPB 时置低，比较位置实现桥内相移。
    EPWM_setActionQualifierAction(base, EPWM_AQ_OUTPUT_A, EPWM_AQ_OUTPUT_LOW, EPWM_AQ_OUTPUT_ON_TIMEBASE_UP_CMPB);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_RED, true);
    EPWM_setDeadBandDelayMode(base, EPWM_DB_FED, true);
    EPWM_setDeadBandDelayPolarity(base, EPWM_DB_FED, EPWM_DB_POLARITY_ACTIVE_LOW); // 由 A 形成带死区的互补 B；50 计数名义约 333 ns，须实测驱动波形。
    EPWM_setRisingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setFallingEdgeDeadBandDelayInput(base, EPWM_DB_INPUT_EPWMA);
    EPWM_setRisingEdgeDelayCount(base, DAB_DEADBAND_RED_FED);
    EPWM_setFallingEdgeDelayCount(base, DAB_DEADBAND_RED_FED);
    EPWM_enableGlobalLoadRegisters(base, EPWM_GL_REGISTER_TBPRD_TBPRDHR |
                                        EPWM_GL_REGISTER_CMPA_CMPAHR | EPWM_GL_REGISTER_CMPB_CMPBHR);
    EPWM_setGlobalLoadEventPrescale(base, 1U); // 每次指定装载事件均可触发，避免分频导致首包多等周期。
    EPWM_enableGlobalLoadOneShotMode(base); // 先写完全部参数，再单次请求装载；不是写寄存器就立即生效。
    EPWM_setGlobalLoadTrigger(base, base == DAB_PWM_LEG1_BASE ?
                             EPWM_GL_LOAD_PULSE_CNTR_ZERO : EPWM_GL_LOAD_PULSE_SYNC);
                             // 主周期/比较值在 ZERO 装载，从外设在主 SYNC 装载；TBPHS 另由同步相位载入控制。
    EPWM_enableGlobalLoad(base);
}

void DAB_PWM_init(void)
{
    uint16_t i;
    const uint32_t pins[8] = {DAB_PWM1A_CONFIG, DAB_PWM1B_CONFIG,
        DAB_PWM2A_CONFIG, DAB_PWM2B_CONFIG, DAB_PWM3A_CONFIG, DAB_PWM3B_CONFIG,
        DAB_PWM4A_CONFIG, DAB_PWM4B_CONFIG};
    const uint32_t gpios[8] = {DAB_PWM1A_GPIO, DAB_PWM1B_GPIO,
        DAB_PWM2A_GPIO, DAB_PWM2B_GPIO, DAB_PWM3A_GPIO, DAB_PWM3B_GPIO,
        DAB_PWM4A_GPIO, DAB_PWM4B_GPIO};
    s_pendingReady = s_enableRequested = s_releaseAtZero = s_enabled = false;
    s_waitingLoad = false; // 初始化或软件取消等待；已经发出的硬件一次装载不能靠写零撤回。
    s_nextSequence = g_pwmAppliedSequence = g_pwmUpdateTimeoutCount = g_controlHeartbeat = 0U;
    g_pwmAppliedParams = g_pwmParams;
    g_controlLastTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    g_pwmLateCommitCount = 0U;
    DAB_PWM_resetWindowDiag();
    // Caller holds TBCLKSYNC disabled throughout peripheral setup.
    SysCtl_resetPeripheral(DAB_PWM_LEG1_RESET);
    SysCtl_resetPeripheral(DAB_PWM_LEG2_RESET);
    SysCtl_resetPeripheral(DAB_PWM_LEG3_RESET);
    SysCtl_resetPeripheral(DAB_PWM_LEG4_RESET);
    SysCtl_resetPeripheral(DAB_CTRL_EPWM_RESET); // 清掉旧 SOCA、Global Load 和中断配置，RAM 重载也从确定状态初始化。
    EPWM_forceTripZoneEvent(EPWM2_BASE, EPWM_TZ_FORCE_EVENT_OST);
    EPWM_forceTripZoneEvent(EPWM3_BASE, EPWM_TZ_FORCE_EVENT_OST);
    EPWM_forceTripZoneEvent(EPWM6_BASE, EPWM_TZ_FORCE_EVENT_OST);
    EPWM_setTimeBaseCounterMode(EPWM2_BASE, EPWM_COUNTER_MODE_STOP_FREEZE);
    EPWM_setTimeBaseCounterMode(EPWM3_BASE, EPWM_COUNTER_MODE_STOP_FREEZE);
    EPWM_setTimeBaseCounterMode(EPWM6_BASE, EPWM_COUNTER_MODE_STOP_FREEZE);
    for (i = 0U; i < 4U; i++) configLeg(s_bases[i]);
    {
        const uint32_t retired[10] = {0U,1U,2U,3U,4U,5U,10U,11U,22U,23U};
        const uint32_t retiredCfg[10] = {GPIO_0_GPIO0,GPIO_1_GPIO1,GPIO_2_GPIO2,GPIO_3_GPIO3,
            GPIO_4_GPIO4,GPIO_5_GPIO5,GPIO_10_GPIO10,GPIO_11_GPIO11,GPIO_22_GPIO22,GPIO_23_GPIO23};
        for (i = 0U; i < 10U; i++)
        {
            GPIO_setDirectionMode(retired[i], GPIO_DIR_MODE_IN);
            GPIO_setPadConfig(retired[i], GPIO_PIN_TYPE_STD); // 不将旧驱动线拉高。
            GPIO_setPinConfig(retiredCfg[i]); // 先设输入，再退出旧 PWM 复用。
        }
    }
    EPWM_disablePhaseShiftLoad(DAB_PWM_LEG1_BASE);
    EPWM_setSyncInPulseSource(DAB_PWM_LEG1_BASE, EPWM_SYNC_IN_PULSE_SRC_DISABLE);
    EPWM_enableSyncOutPulseSource(DAB_PWM_LEG1_BASE, EPWM_SYNC_OUT_PULSE_ON_CNTR_ZERO); // EPWM7 零点为共同同步源，EPWM4/5/10 直接选它，不经过逐级同步链。
    for (i = 1U; i < 4U; i++)
    {
        EPWM_setPhaseShift(s_bases[i], 0U);
        EPWM_enablePhaseShiftLoad(s_bases[i]);
        EPWM_setCountModeAfterSync(s_bases[i], i == 1U ?
                                  EPWM_COUNT_MODE_UP_AFTER_SYNC : EPWM_COUNT_MODE_DOWN_AFTER_SYNC);
                                  // 第二桥臂 EPWM4 同步后向上；逻辑桥臂3/4（EPWM5/10） 同步后向下，必须结合该方向理解 D0 的实际移相。
        EPWM_setSyncInPulseSource(s_bases[i], DAB_PWM_MASTER_SYNC_SOURCE);
        EPWM_disableSyncOutPulseSource(s_bases[i], EPWM_SYNC_OUT_PULSE_ON_ALL);
        EPWM_setupEPWMLinks(s_bases[i], DAB_PWM_MASTER_LINK, EPWM_LINK_GLDCTL2); // 关联 GLDCTL2，请求主装载时同时关联从外设的一次性装载请求。
    }
    EPWM_setInterruptSource(DAB_PWM_LEG1_BASE, EPWM_INT_TBCTR_PERIOD); // 通常在周期顶点提交，下降计数期间预留到下一零点的写入时间。
    EPWM_setInterruptEventCount(DAB_PWM_LEG1_BASE, 1U);
    EPWM_clearEventTriggerInterruptFlag(DAB_PWM_LEG1_BASE);
    EPWM_enableInterrupt(DAB_PWM_LEG1_BASE);
    // Reserve SOCB solely as an observable zero-event marker. No ADC SOC uses it.
    // GLDCTL2.OSHTLD always reads zero, so it cannot acknowledge a load.
    EPWM_setADCTriggerSource(DAB_PWM_LEG1_BASE, EPWM_SOC_B, EPWM_SOC_TBCTR_ZERO);
    EPWM_setADCTriggerEventPrescale(DAB_PWM_LEG1_BASE, EPWM_SOC_B, 1U);
    EPWM_clearADCTriggerFlag(DAB_PWM_LEG1_BASE, EPWM_SOC_B);
    EPWM_enableADCTrigger(DAB_PWM_LEG1_BASE, EPWM_SOC_B); // SOCB 仅作为可查询的零点事件标志；当前没有 ADC SOC 选择此触发。
    GPIO_setAnalogMode(DAB_PWM1A_GPIO, GPIO_ANALOG_DISABLED); // GPIO12 作为 EPWM7A，断开模拟功能。
    GPIO_setAnalogMode(DAB_PWM1B_GPIO, GPIO_ANALOG_DISABLED); // GPIO13 作为 EPWM7B。
    // Route pins only after each module is held in a software trip.
    for (i = 0U; i < 8U; i++)
    {
        GPIO_setPinConfig(pins[i]);
        GPIO_setPadConfig(gpios[i], GPIO_PIN_TYPE_STD);
        GPIO_setDirectionMode(gpios[i], GPIO_DIR_MODE_OUT);
    }
    GPIO_setPinConfig(DAB_DEBUG_PIN_CONFIG);
    GPIO_setPadConfig(DAB_DEBUG_GPIO, GPIO_PIN_TYPE_STD);
    GPIO_setDirectionMode(DAB_DEBUG_GPIO, GPIO_DIR_MODE_OUT);
    GPIO_writePin(DAB_DEBUG_GPIO, 0U);

    EPWM_setTimeBasePeriod(DAB_CTRL_EPWM_BASE, DAB_CTRL_TBPRD); // 独立 7500 计数的上下计数节拍，对应固定 10 kHz 控制。
    EPWM_setTimeBaseCounter(DAB_CTRL_EPWM_BASE, 0U);
    EPWM_setTimeBaseCounterMode(DAB_CTRL_EPWM_BASE, EPWM_COUNTER_MODE_UP_DOWN);
    EPWM_setClockPrescaler(DAB_CTRL_EPWM_BASE, EPWM_CLOCK_DIVIDER_1, EPWM_HSCLOCK_DIVIDER_1);
    EPWM_disablePhaseShiftLoad(DAB_CTRL_EPWM_BASE);
    EPWM_setSyncInPulseSource(DAB_CTRL_EPWM_BASE, EPWM_SYNC_IN_PULSE_SRC_DISABLE);
    EPWM_setADCTriggerSource(DAB_CTRL_EPWM_BASE, EPWM_SOC_A, EPWM_SOC_TBCTR_ZERO); // 零点启动采样，顶点中断读取；正常二者相隔约 50 μs。
    EPWM_setADCTriggerEventPrescale(DAB_CTRL_EPWM_BASE, EPWM_SOC_A, 1U);
    EPWM_enableADCTrigger(DAB_CTRL_EPWM_BASE, EPWM_SOC_A);
    EPWM_setInterruptSource(DAB_CTRL_EPWM_BASE, EPWM_INT_TBCTR_PERIOD);
    EPWM_setInterruptEventCount(DAB_CTRL_EPWM_BASE, 1U);
    EPWM_clearEventTriggerInterruptFlag(DAB_CTRL_EPWM_BASE);
    EPWM_enableInterrupt(DAB_CTRL_EPWM_BASE);
}

#pragma CODE_SECTION(DAB_PWM_updateModulation, ".TI.ramfunc")
bool DAB_PWM_updateModulation(const Dab_PwmParams_t *params)
{
    DAB_PwmPacket packet;
    if (!DAB_isFinite(params->D1) || !DAB_isFinite(params->D2) ||
        !DAB_isFinite(params->D0) || !DAB_isFinite(params->D1_pha) ||
        !DAB_isFinite(params->D2_pha) || params->D1 < 0.0f || params->D1 > 1.0f ||
        params->D2 < 0.0f || params->D2 > 1.0f || params->D0 < 0.0f || params->D0 >= 1.0f ||
        params->D1_pha < 0.0f || params->D1_pha > 1.0f ||
        params->D2_pha < 0.0f || params->D2_pha > 1.0f ||
        params->tbprd_var < DAB_BASE_TBPRD / 2U || params->tbprd_var > DAB_BASE_TBPRD * 2U)
        return false;
    packet.period = (uint16_t)params->tbprd_var; // 已检查周期 1250～5000，转换为寄存器计数；对应 60～15 kHz。
    packet.cmpA2 = (uint16_t)(params->D1 * packet.period); // 第二桥臂 EPWM4 高电平起点；另一比较值来自 1−D1，D1 不是通常的单管占空比。
    packet.cmpB2 = (uint16_t)(params->D1_pha * packet.period);
    packet.cmpA4 = (uint16_t)(params->D2 * packet.period);
    packet.cmpB4 = (uint16_t)(params->D2_pha * packet.period);
    packet.phase34 = (uint16_t)(params->D0 * packet.period); // 逻辑桥臂3/4（EPWM5/10） 共用桥间相位计数，实际领先/滞后需结合同步方向和驱动波形确认。
    packet.params = *params;
    packet.sequence = ++s_nextSequence;
    // Producer and consumer are non-nested PIE group 3 ISRs.
    if (!s_pendingReady) s_pendingTick = CPUTimer_getTimerCount(CPUTIMER2_BASE); // 后来的参数覆盖请求时不重新计时，防止一直延后而永不超时。
    s_pending = packet;
    s_pendingReady = true; // 发布完整包；当前生产/消费均在不嵌套的 PIE group 3，改变并发方式须重新保护。
    return true;
}

void DAB_PWM_enable(void) { if (DAB_BOARD_CONFIG_CONFIRMED) s_enableRequested = true; }
bool DAB_PWM_isEnabled(void) { return s_enabled; }

#pragma CODE_SECTION(DAB_PWM_disable, ".TI.ramfunc")
void DAB_PWM_disable(void)
{
    uint16_t i;
    for (i = 0U; i < 4U; i++) EPWM_forceTripZoneEvent(s_bases[i], EPWM_TZ_FORCE_EVENT_OST);
    s_enabled = s_enableRequested = s_releaseAtZero = s_pendingReady = false;
    s_waitingLoad = false;
    EPWM_setInterruptSource(DAB_PWM_LEG1_BASE, EPWM_INT_TBCTR_PERIOD);
}

#pragma CODE_SECTION(DAB_PWM_hardwareFault, ".TI.ramfunc")
bool DAB_PWM_hardwareFault(void)
{
    uint16_t i;
    if (GPIO_readPin(DAB_HW_TRIP_GPIO) == 0U) return true;
    for (i = 0U; i < 4U; i++)
        if (EPWM_getOneShotTripZoneFlagStatus(s_bases[i]) & EPWM_TZ_OST_FLAG_OST1) return true;
    return false;
}

bool DAB_PWM_clearHardwareFault(void)
{
    uint16_t i;
    if (s_enabled || s_enableRequested || GPIO_readPin(DAB_HW_TRIP_GPIO) == 0U) return false;
    // Keep the software trip asserted; clear only the external-source latch.
    for (i = 0U; i < 4U; i++) EPWM_clearOneShotTripZoneFlag(s_bases[i], EPWM_TZ_OST_FLAG_OST1); // 只清外部来源锁存，软件 OST 仍保持；输出关闭时才能重新监测新故障脉冲。
    return !DAB_PWM_hardwareFault();
}

#pragma CODE_SECTION(commitWindow, ".TI.ramfunc")
static bool commitWindow(uint16_t minRemaining)
{
    bool ok = EPWM_getTimeBaseCounterDirection(DAB_PWM_LEG1_BASE) == EPWM_TIME_BASE_STATUS_COUNT_DOWN &&
              EPWM_getTimeBaseCounterValue(DAB_PWM_LEG1_BASE) > minRemaining;
              // 开始写入须同时保留写入预算和 600 计数边界；中途复核仍保留原 600 计数，不放宽保护。
#if DAB_PWM_WINDOW_GUARD
    return ok;
#else
    if (!ok) g_pwmLateCommitCount++; // 仍累计越界次数，但不暂缓、不报 PWM_WINDOW。
    return true;
#endif
}

#pragma CODE_SECTION(windowFault, ".TI.ramfunc")
static void windowFault(uint16_t stage, uint16_t entryCounter, uint32_t entryTick)
{
    // 仅故障时保存，stage 最后发布；故障后的读数比失败检查略晚，不是同一时刻快照。
    if (g_pwmWindowDiag.stage == 0U)
    {
        g_pwmWindowDiag.failCounter = EPWM_getTimeBaseCounterValue(DAB_PWM_LEG1_BASE);
        g_pwmWindowDiag.failDirection = EPWM_getTimeBaseCounterDirection(DAB_PWM_LEG1_BASE);
        g_pwmWindowDiag.failTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        g_pwmWindowDiag.entryCounter = entryCounter;
        g_pwmWindowDiag.entryTick = entryTick;
        g_pwmWindowDiag.stage = stage;
    }
    g_pwmLateCommitCount++;
    DAB_Control_faultReason(DAB_FAULT_PWM_WINDOW);
}

#pragma CODE_SECTION(observeLoad, ".TI.ramfunc")
static void observeLoad(void)
{
    if (s_waitingLoad && EPWM_getADCTriggerFlagStatus(DAB_PWM_LEG1_BASE, EPWM_SOC_B))
    {
        g_pwmAppliedParams = s_staged.params; // 只确认请求后出现的零点事件，不是活动寄存器回读，也不证明四桥实测波形。
        g_pwmAppliedSequence = s_staged.sequence;
        s_waitingLoad = false;
    }
}

#pragma CODE_SECTION(DAB_PWM_checkDeadline, ".TI.ramfunc")
bool DAB_PWM_checkDeadline(void)
{
    uint32_t now = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    uint32_t limit = (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_PWM_UPDATE_TIMEOUT_US;
    if (s_enabled && (uint32_t)(g_controlLastTick - now) >
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_ADC_MAX_AGE_US)
    { DAB_Control_faultReason(DAB_FAULT_ADC); return false; }
    if ((s_pendingReady && (uint32_t)(s_pendingTick - now) > limit) ||
        (s_waitingLoad && (uint32_t)(s_stagedTick - now) > limit))
    {
        g_pwmUpdateTimeoutCount++; // 等待提交/装载超过 300 μs，记录后进入故障，不继续沿用旧参数。
        DAB_Control_faultReason(DAB_FAULT_PWM_TIMEOUT);
        return false;
    }
    observeLoad(); // 先判超时再接受事件，迟到的确认不能掩盖已经超期。
    return true;
}

#pragma CODE_SECTION(dab_pwm_commit_ISR, ".TI.ramfunc")
__interrupt void dab_pwm_commit_ISR(void)
{
    uint16_t i;
    DAB_PwmPacket packet;
    uint16_t entryCounter;
    uint32_t entryTick;
    if (DAB_PWM_hardwareFault())
    { g_protectFlags.bit.H_OCP_Flag = 1U; DAB_Control_faultReason(DAB_FAULT_HARDWARE); }
    if (!DAB_PWM_checkDeadline()) goto ack;
    if (s_releaseAtZero) // 仅首包启用阶段临时在零点进入，复核装载序号和全部启动条件后才释放。
    {
        // This zero event has loaded the complete first packet. Release only
        // after rechecking the software latch and the hardware source.
        if (!s_waitingLoad && g_pwmAppliedSequence == s_staged.sequence &&
            s_enableRequested && g_dabState == DAB_STATE_SOFT_START &&
            DAB_ADC_isReady() && !DAB_NN_hasFault() &&
            !DAB_Protect_checkFault())
        {
            for (i = 0U; i < 4U; i++) EPWM_clearTripZoneFlag(s_bases[i], EPWM_TZ_FLAG_OST);
            s_enabled = true; // 实际清除了软件 OST 后才标记使能，提出请求本身不算已输出。
            s_enableRequested = false;
        }
        else DAB_Control_fault();
        s_releaseAtZero = false;
        EPWM_setInterruptSource(DAB_PWM_LEG1_BASE, EPWM_INT_TBCTR_PERIOD);
    }
    else if (s_pendingReady && !s_waitingLoad)
    {
        if (!commitWindow(DAB_PWM_COMMIT_GUARD_COUNTS + DAB_PWM_STAGE_BUDGET_COUNTS))
            g_pwmLateCommitCount++; // 余量不足时尚未写任何参数，保留请求，等后续周期；总等待期限不变。
        else
        {
            entryTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
            entryCounter = EPWM_getTimeBaseCounterValue(DAB_PWM_LEG1_BASE);
            packet = s_pending;
            s_pendingReady = false;
            // TBPHS has no shadow register. Block slave phase loads during
            // staging, then arm all shadow registers for the master sync.
            // 使用常量外设地址，让编译器在编译时验证地址，保留检查并避免循环查表和运行期比较。
            EPWM_disablePhaseShiftLoad(DAB_PWM_LEG2_BASE);
            EPWM_disablePhaseShiftLoad(DAB_PWM_LEG3_BASE);
            EPWM_disablePhaseShiftLoad(DAB_PWM_LEG4_BASE); // TBPHS 无 Shadow，先阻止半套相位载入。
            EPWM_setTimeBasePeriod(DAB_PWM_LEG1_BASE, packet.period);
            EPWM_setTimeBasePeriod(DAB_PWM_LEG2_BASE, packet.period);
            EPWM_setTimeBasePeriod(DAB_PWM_LEG3_BASE, packet.period);
            EPWM_setTimeBasePeriod(DAB_PWM_LEG4_BASE, packet.period);
            EPWM_setCounterCompareValue(DAB_PWM_LEG1_BASE, EPWM_COUNTER_COMPARE_A, packet.period);
            EPWM_setCounterCompareValue(DAB_PWM_LEG1_BASE, EPWM_COUNTER_COMPARE_B, 0U);
            EPWM_setCounterCompareValue(DAB_PWM_LEG2_BASE, EPWM_COUNTER_COMPARE_A, packet.cmpA2);
            EPWM_setCounterCompareValue(DAB_PWM_LEG2_BASE, EPWM_COUNTER_COMPARE_B, packet.cmpB2);
            EPWM_setCounterCompareValue(DAB_PWM_LEG3_BASE, EPWM_COUNTER_COMPARE_A, packet.period);
            EPWM_setCounterCompareValue(DAB_PWM_LEG3_BASE, EPWM_COUNTER_COMPARE_B, 0U);
            EPWM_setCounterCompareValue(DAB_PWM_LEG4_BASE, EPWM_COUNTER_COMPARE_A, packet.cmpA4);
            EPWM_setCounterCompareValue(DAB_PWM_LEG4_BASE, EPWM_COUNTER_COMPARE_B, packet.cmpB4);
            EPWM_setPhaseShift(DAB_PWM_LEG3_BASE, packet.phase34);
            EPWM_setPhaseShift(DAB_PWM_LEG4_BASE, packet.phase34); // 两个副边桥臂相位一起准备；下方再次检查写入是否仍在允许窗口。
            if (!commitWindow(DAB_PWM_COMMIT_GUARD_COUNTS))
            {
                windowFault(1U, entryCounter, entryTick);
            }
            else
            {
                EPWM_enablePhaseShiftLoad(DAB_PWM_LEG2_BASE);
                EPWM_enablePhaseShiftLoad(DAB_PWM_LEG3_BASE);
                EPWM_enablePhaseShiftLoad(DAB_PWM_LEG4_BASE);
                // GLDCTL2 is linked from master EPWM7 to all slaves; arm LAST.
                if (!commitWindow(DAB_PWM_COMMIT_GUARD_COUNTS))
                { windowFault(2U, entryCounter, entryTick); }
                else
                {
                    s_staged = packet;
                    s_stagedTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
                    EPWM_clearADCTriggerFlag(DAB_PWM_LEG1_BASE, EPWM_SOC_B); // 先清旧零点记录，避免把请求之前的事件误认作本包装载。
                    if (!commitWindow(DAB_PWM_COMMIT_GUARD_COUNTS))
                    { windowFault(3U, entryCounter, entryTick); goto ack; }
                    EPWM_setGlobalLoadOneShotLatch(DAB_PWM_LEG1_BASE); // 全部写入并复核窗口之后最后发出装载请求；OSHTLD 始终读回零，不能拿来确认。
                    s_waitingLoad = true;
                    if (s_enableRequested)
                    {
                        s_releaseAtZero = true;
                        EPWM_setInterruptSource(DAB_PWM_LEG1_BASE, EPWM_INT_TBCTR_ZERO); // 第一次启用等到零点再复核并释放，之后恢复周期顶点提交。
                    }
                }
            }
        }
    }
ack:
    EPWM_clearEventTriggerInterruptFlag(DAB_PWM_LEG1_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3); // 清外设标志后再释放 group 3，允许本组下一次中断进入。
}

#pragma CODE_SECTION(dab_control_ISR, ".TI.ramfunc")
__interrupt void dab_control_ISR(void)
{
    bool valid;
    g_controlHeartbeat++;
    g_controlLastTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    DAB_NN_checkDeadline();
    GPIO_writePin(DAB_DEBUG_GPIO, 1U); // GPIO61 标记此后采样/控制代码段，之前的心跳及 NN 期限检查不在这个高电平宽度内。
    valid = DAB_ADC_read(); // 读取 A/B 完整结果；运行期一帧无效即请求关闭，而不是沿用旧采样继续。
    if (!valid && (g_dabState == DAB_STATE_RUN || g_dabState == DAB_STATE_SOFT_START))
        DAB_Control_faultReason(DAB_FAULT_ADC);
    else if (valid || DAB_PWM_hardwareFault())
        DAB_Control_step();
    GPIO_writePin(DAB_DEBUG_GPIO, 0U);
    EPWM_clearEventTriggerInterruptFlag(DAB_CTRL_EPWM_BASE);
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP3);
}
