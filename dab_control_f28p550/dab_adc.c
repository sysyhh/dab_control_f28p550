#include "dab_adc.h"
#include <string.h>

volatile Dab_Sensing_t g_sensing;
volatile uint32_t g_adcFrameCount = 0U;
volatile uint32_t g_adcInvalidFrameCount = 0U;
#define VOUT_WINDOW_SIZE 50U // 电压平均 50 点；10 kHz 下约 2.45 ms 延迟，闭环调参须考虑此延迟。
#define IL_WINDOW_SIZE 10U // 电感电流平均 10 点；过流判断使用瞬时值，不等待平均窗口。
static uint16_t s_voutP_buf[VOUT_WINDOW_SIZE], s_voutN_buf[VOUT_WINDOW_SIZE];
static uint16_t s_il_buf[IL_WINDOW_SIZE];
static uint32_t s_voutP_sum, s_voutN_sum, s_il_sum; // 对原始计数作整数累计，50×4095 最大为 204750，避免浮点长期加减漂移。
volatile uint16_t g_adcRecoveryFrameCount = 0U;
volatile uint32_t g_adcLastFrameTick = 0U;
static uint16_t s_idx_50, s_idx_10, s_count_50, s_count_10;
static volatile bool s_latestFrameValid;

static void configureADC(uint32_t base, ADC_Channel ch0, ADC_Channel ch1)
{
    ADC_setPrescaler(base, ADC_CLK_DIV_2_0); // 150 MHz SYSCLK 整数除 2，得到 75 MHz ADCCLK。
    ADC_setVREF(base, ADC_REFERENCE_INTERNAL, ADC_REFERENCE_3_3V); // 内部 3.3 V 参考；传感器系数仍需实板标定。
    ADC_setInterruptPulseMode(base, ADC_PULSE_END_OF_CONV); // 完成状态在结果可用后产生，避免读到尚未更新的结果。
    ADC_setSOCPriority(base, ADC_PRI_ALL_HIPRI); // 采用高优先级顺序，当前 SOC0 先于 SOC1；同一 ADC 的两通道不是同时采样。
    ADC_setupSOC(base, ADC_SOC_NUMBER0, DAB_CTRL_ADC_TRIGGER, ch0, 15U); // 零点 SOCA 触发第一通道，15 个 SYSCLK 采样窗口约 100 ns。
    ADC_setupSOC(base, ADC_SOC_NUMBER1, DAB_CTRL_ADC_TRIGGER, ch1, 15U); // 同一触发排入第二通道；窗口是否够长取决于实际模拟输入电路。
    // EOC1 means both channels in this ADC have completed.
    ADC_setInterruptSource(base, ADC_INT_NUMBER1, ADC_SOC_NUMBER1); // 检查 EOC1 即确认这个 ADC 的两项转换均已结束。
    ADC_enableContinuousMode(base, ADC_INT_NUMBER1); // SPRZ572B recovery // 按勘误启用连续完成模式，仍需检查并清除状态及溢出。
    ADC_clearInterruptStatus(base, ADC_INT_NUMBER1);
    ADC_clearInterruptOverflowStatus(base, ADC_INT_NUMBER1);
    ADC_enableInterrupt(base, ADC_INT_NUMBER1); // status only; no ADC PIE interrupt // 这里只启用可查询的完成状态，CPU 实际入口是 EPWM1 中断。
    ADC_enableConverter(base);
}

void DAB_ADC_init(void)
{
    memset((void *)&g_sensing, 0, sizeof(g_sensing));
    memset(s_voutP_buf, 0, sizeof(s_voutP_buf));
    memset(s_voutN_buf, 0, sizeof(s_voutN_buf));
    memset(s_il_buf, 0, sizeof(s_il_buf));
    s_voutP_sum = s_voutN_sum = s_il_sum = 0U;
    s_idx_50 = s_idx_10 = s_count_50 = s_count_10 = 0U;
    g_adcFrameCount = g_adcInvalidFrameCount = 0U;
    s_latestFrameValid = false;
    g_adcRecoveryFrameCount = 0U; g_adcLastFrameTick = 0U; // 初始化连续有效帧资格和最近读取时刻。
    g_sensing.vin = g_sensing.vin_ave = DAB_NOMINAL_VIN; // 当前 Vin 固定为 90 V，没有 Vin 采样通道，不能据此判断真实输入欠压。
    GPIO_setAnalogMode(DAB_VOUT_P_ANALOG_GPIO, GPIO_ANALOG_ENABLED);
    GPIO_setAnalogMode(DAB_VOUT_N_ANALOG_GPIO, GPIO_ANALOG_ENABLED);
    GPIO_setAnalogMode(DAB_IOUT_ANALOG_GPIO, GPIO_ANALOG_ENABLED);
    GPIO_setAnalogMode(DAB_IL_ANALOG_GPIO, GPIO_ANALOG_ENABLED); // B0/B1 保持模拟模式，避免 RAM 重载前残留数字配置。
    configureADC(ADCA_BASE, DAB_VOUT_P_CHANNEL, DAB_VOUT_N_CHANNEL); // A 的 SOC0/1 分别采 VP/VN，当前 ADCINA4/5，集中在 J7。
    configureADC(ADCB_BASE, DAB_IOUT_CHANNEL, DAB_IL_CHANNEL); // B 的 SOC0/1 分别采 IO/IL，默认 ADCINB0/1。
    // Revision 0 requires all converter power enabled, including unused ADCs.
    if (SysCtl_getDeviceRevision() == 0U) // 早期 revision 0 按勘误给全部 ADC 转换器上电，不增加实际采样通道。
    { ADC_enableConverter(ADCC_BASE); ADC_enableConverter(ADCD_BASE); ADC_enableConverter(ADCE_BASE); }
    // F28P55x internal reference settling requirement: 5 ms.
    DEVICE_DELAY_US(5000U); // 内部参考稳定等待 5 ms，之后才开始接收转换结果。
}

#pragma CODE_SECTION(DAB_ADC_isReady, ".TI.ramfunc")
bool DAB_ADC_isReady(void)
{
    bool ready, masked = Interrupt_disableGlobal();
    ready = s_latestFrameValid && g_adcRecoveryFrameCount == VOUT_WINDOW_SIZE &&
        (uint32_t)(g_adcLastFrameTick - CPUTimer_getTimerCount(CPUTIMER2_BASE)) <=
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_ADC_MAX_AGE_US;
    if (!masked) Interrupt_enableGlobal();
    return ready; // 仅最新有效、连续 50 帧正常且读取时间未过旧时才允许启动或继续控制。
}

#pragma CODE_SECTION(rejectFrame, ".TI.ramfunc")
static bool rejectFrame(void)
{
    s_latestFrameValid = false;
    g_adcRecoveryFrameCount = 0U; // 无效帧打断连续恢复资格，下一次有效帧从头累计。
    s_idx_50 = s_idx_10 = s_count_50 = s_count_10 = 0U;
    s_voutP_sum = s_voutN_sum = s_il_sum = 0U;
    g_adcInvalidFrameCount++; // 保留异常次数及最后显示值，但已拒绝的数据不用于允许启动。
    return false;
}

#pragma CODE_SECTION(clearADCFlags, ".TI.ramfunc")
static bool clearADCFlags(void)
{
    bool overflowA, overflowB;
    ADC_clearInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1);
    overflowA = ADC_getInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1); // 清完成标志后再查竞争溢出；若发生则再次清完成标志。
    if (overflowA)
        ADC_clearInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1);
    ADC_clearInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1);
    ADC_clearInterruptStatus(ADCB_BASE, ADC_INT_NUMBER1);
    overflowB = ADC_getInterruptOverflowStatus(ADCB_BASE, ADC_INT_NUMBER1);
    if (overflowB)
        ADC_clearInterruptStatus(ADCB_BASE, ADC_INT_NUMBER1);
    ADC_clearInterruptOverflowStatus(ADCB_BASE, ADC_INT_NUMBER1);
    return overflowA || overflowB; // 清标志期间发现竞争也必须拒绝本帧，不能当作可信新数据。
}

#pragma CODE_SECTION(DAB_ADC_read, ".TI.ramfunc")
bool DAB_ADC_read(void)
{
    uint16_t vp, vn, io, il;
    if (g_adcRecoveryFrameCount != 0U &&
        (uint32_t)(g_adcLastFrameTick - CPUTimer_getTimerCount(CPUTIMER2_BASE)) >
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_ADC_MAX_AGE_US)
        rejectFrame(); // A gap breaks both filter history and recovery qualification.
    s_latestFrameValid = false;
    // SOCA is at EPWM1 zero, read at period (50 us later).
    if (!ADC_getInterruptStatus(ADCA_BASE, ADC_INT_NUMBER1) ||
        !ADC_getInterruptStatus(ADCB_BASE, ADC_INT_NUMBER1) ||
        ADC_getInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1) ||
        ADC_getInterruptOverflowStatus(ADCB_BASE, ADC_INT_NUMBER1) ||
        EPWM_getTimeBaseCounterDirection(DAB_CTRL_EPWM_BASE) != EPWM_TIME_BASE_STATUS_COUNT_DOWN ||
        EPWM_getTimeBaseCounterValue(DAB_CTRL_EPWM_BASE) < DAB_ADC_READ_GUARD_COUNTS)
    { clearADCFlags(); return rejectFrame(); }
    vp = ADC_readResult(ADCARESULT_BASE, ADC_SOC_NUMBER0); // 读取四项完整结果；前后都检查计数边界和溢出，避免跨下一次采样。
    vn = ADC_readResult(ADCARESULT_BASE, ADC_SOC_NUMBER1);
    io = ADC_readResult(ADCBRESULT_BASE, ADC_SOC_NUMBER0);
    il = ADC_readResult(ADCBRESULT_BASE, ADC_SOC_NUMBER1);
    // Reject a read crossing the next SOCA boundary as well.
    if (ADC_getInterruptOverflowStatus(ADCA_BASE, ADC_INT_NUMBER1) ||
        ADC_getInterruptOverflowStatus(ADCB_BASE, ADC_INT_NUMBER1) ||
        EPWM_getTimeBaseCounterDirection(DAB_CTRL_EPWM_BASE) != EPWM_TIME_BASE_STATUS_COUNT_DOWN ||
        EPWM_getTimeBaseCounterValue(DAB_CTRL_EPWM_BASE) < DAB_ADC_READ_GUARD_COUNTS)
    { clearADCFlags(); return rejectFrame(); }
    if (clearADCFlags()) return rejectFrame(); // 结果虽已读出，若清标志时又发现竞争，仍整体作废。
    g_sensing.vout_p_raw = vp; g_sensing.vout_n_raw = vn;
    g_sensing.iout_raw = io; g_sensing.il_raw = il;
    g_sensing.vout_p = BUCK_VOUT_P_SCALE * (float)vp - BUCK_VOUT_P_BIAS;
    g_sensing.vout_n = BUCK_VOUT_N_SCALE * (float)vn + BUCK_VOUT_N_BIAS; // VN 的偏置为相加，VP 为相减；保持原始标定符号，不能仅按变量名猜测。
    g_sensing.iout = BUCK_IOUT_COEF * (float)io - BUCK_IOUT_BIAS;
    g_sensing.il = BUCK_IL_COEF * (float)il - BUCK_IL_BIAS; // 保留瞬时电流供过流判断，尚未按当前采样板重新标定。
    if (s_count_50 == VOUT_WINDOW_SIZE) // 窗口满后先移除最旧样本，再加入新样本；未填满时按实际点数求平均。
    { s_voutP_sum -= s_voutP_buf[s_idx_50]; s_voutN_sum -= s_voutN_buf[s_idx_50]; }
    if (s_count_10 == IL_WINDOW_SIZE) s_il_sum -= s_il_buf[s_idx_10];
    s_voutP_sum += vp; s_voutN_sum += vn; s_il_sum += il;
    s_voutP_buf[s_idx_50] = vp; s_voutN_buf[s_idx_50] = vn; s_il_buf[s_idx_10] = il;
    if (s_count_50 < VOUT_WINDOW_SIZE) s_count_50++;
    if (s_count_10 < IL_WINDOW_SIZE) s_count_10++;
    g_sensing.vout_p_ave = BUCK_VOUT_P_SCALE * (float)s_voutP_sum *
        (s_count_50 == VOUT_WINDOW_SIZE ? 0.02f : 1.0f / (float)s_count_50) - BUCK_VOUT_P_BIAS;
    g_sensing.vout_n_ave = BUCK_VOUT_N_SCALE * (float)s_voutN_sum *
        (s_count_50 == VOUT_WINDOW_SIZE ? 0.02f : 1.0f / (float)s_count_50) + BUCK_VOUT_N_BIAS;
    g_sensing.il_ave = BUCK_IL_COEF * (float)s_il_sum *
        (s_count_10 == IL_WINDOW_SIZE ? 0.1f : 1.0f / (float)s_count_10) - BUCK_IL_BIAS;
    if (++s_idx_50 >= VOUT_WINDOW_SIZE) s_idx_50 = 0U;
    if (++s_idx_10 >= IL_WINDOW_SIZE) s_idx_10 = 0U;
    g_adcFrameCount++;
    if (g_adcRecoveryFrameCount < VOUT_WINDOW_SIZE) g_adcRecoveryFrameCount++;
    g_adcLastFrameTick = CPUTimer_getTimerCount(CPUTIMER2_BASE); // 记录读取结束时刻，不是实际模拟采样时刻；正常采样约早 50 μs。
    s_latestFrameValid = true;
    // 至此才发布本帧有效；任何失败路径都会清空历史和连续恢复计数。
    return true;
}
