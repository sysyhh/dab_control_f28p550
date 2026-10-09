//#############################################################################
//
// FILE:   dab_telemetry.c
//
// TITLE:  VOFA+ Serial Telemetry Communication Interface for DAB on F28P550
//
//#############################################################################

#include "dab_telemetry.h"

// VOFA+ JustFloat 固定尾标：00 00 80 7F，用于帧对齐，不是发送的故障数值。
static const uint16_t s_vofaTail[4] = { 0x00, 0x00, 0x80, 0x7F };
#define TX_FRAME_OCTETS 16U // 三项 float 各 4 个线路字节，加 4 字节尾标；不是 C28x 的 sizeof 帧长度。
#define TX_QUEUE_FRAMES 4U // 最多缓存四帧，满时丢弃新整帧，避免遥测阻塞控制后台。
static uint16_t s_frames[TX_QUEUE_FRAMES][TX_FRAME_OCTETS];
static uint16_t s_head, s_tail, s_queued, s_offset; // 分别为读帧索引、写帧索引、当前队列数、帧内已发送的字节位置。
static uint32_t s_frameTick;
volatile uint32_t g_telemetryDroppedFrames, g_telemetryTimeoutCount;

void DAB_Telemetry_init(uint32_t baud_rate)
{
    s_head = s_tail = s_queued = s_offset = 0U;
    g_telemetryDroppedFrames = g_telemetryTimeoutCount = 0U;
    // Pinmux for LaunchPad SCIA (GPIO28 RX, GPIO29 TX)
    GPIO_setAnalogMode(DEVICE_GPIO_PIN_SCIRXDA, GPIO_ANALOG_DISABLED); // GPIO28 为模拟复用脚，SCIA 接收必须明确选择数字模式。
    GPIO_setPinConfig(DEVICE_GPIO_CFG_SCIRXDA);
    GPIO_setDirectionMode(DEVICE_GPIO_PIN_SCIRXDA, GPIO_DIR_MODE_IN);
    GPIO_setPadConfig(DEVICE_GPIO_PIN_SCIRXDA, GPIO_PIN_TYPE_STD);
    GPIO_setQualificationMode(DEVICE_GPIO_PIN_SCIRXDA, GPIO_QUAL_ASYNC); // 串口接收使用异步引脚输入，但当前应用没有接收控制命令处理。

    GPIO_setPinConfig(DEVICE_GPIO_CFG_SCITXDA);
    GPIO_setDirectionMode(DEVICE_GPIO_PIN_SCITXDA, GPIO_DIR_MODE_OUT);
    GPIO_setPadConfig(DEVICE_GPIO_PIN_SCITXDA, GPIO_PIN_TYPE_STD);
    GPIO_setQualificationMode(DEVICE_GPIO_PIN_SCITXDA, GPIO_QUAL_ASYNC);

    // Initialize SCIA
    SCI_setConfig(SCIA_BASE, DEVICE_LSPCLK_FREQ, baud_rate,
                  (SCI_CONFIG_WLEN_8 | SCI_CONFIG_STOP_ONE | SCI_CONFIG_PAR_NONE));
    // SCI_setConfig truncates the divider; SCI_setBaud rounds to the nearest.
    // At 37.5 MHz / 115200 this selects BRR=40 instead of 39.
    SCI_setBaud(SCIA_BASE, DEVICE_LSPCLK_FREQ, baud_rate); // 取最近整数分频；37.5 MHz、请求 115200 时实际约 114329 baud。

    SCI_resetChannels(SCIA_BASE);
    SCI_resetRxFIFO(SCIA_BASE);
    SCI_resetTxFIFO(SCIA_BASE);
    SCI_clearInterruptStatus(SCIA_BASE, SCI_INT_TXFF | SCI_INT_RXFF);
    SCI_enableFIFO(SCIA_BASE);
    SCI_enableModule(SCIA_BASE);
}

static void encodeFloat(uint16_t *dst, float value)
{
    union { float f; uint32_t bits; } encoded;
    uint16_t i;
    encoded.f = value; // 按 float 原始位模式取出 uint32_t，不作数值转整数。
    // C28x CHAR_BIT=16: sizeof(float)=2 addressable words, but the wire
    // format still needs FOUR 8-bit octets. Extract them explicitly.
    for (i = 0U; i < 4U; i++)
    {
        dst[i] = (uint16_t)((encoded.bits >> (i * 8U)) & 0xFFU); // 从低到高拆出 4 个 8 位线路字节；C28x 的 char 本身是 16 位。
    }
}

bool DAB_Telemetry_sendVOFA(float ch1, float ch2, float ch3)
{
    uint16_t i;
    if (s_queued == TX_QUEUE_FRAMES) { g_telemetryDroppedFrames++; return false; } // 队列满时整体拒绝新帧并计数，不能只插入半帧。
    encodeFloat(&s_frames[s_tail][0], ch1);
    encodeFloat(&s_frames[s_tail][4], ch2);
    encodeFloat(&s_frames[s_tail][8], ch3);
    for (i = 0U; i < 4U; i++) s_frames[s_tail][12U + i] = s_vofaTail[i];
    if (s_queued == 0U) s_frameTick = CPUTimer_getTimerCount(CPUTIMER2_BASE); // 新成为活动帧时开始计时，发送堵塞超过 20 ms 就恢复队列。
    s_tail = (s_tail + 1U) % TX_QUEUE_FRAMES;
    s_queued++;
    return true;
}

void DAB_Telemetry_service(void)
{
    uint16_t sent = 0U;
    if (s_queued == 0U) return;
    if ((uint32_t)(s_frameTick - CPUTimer_getTimerCount(CPUTIMER2_BASE)) >
        (DEVICE_SYSCLK_FREQ / 1000000UL) * DAB_TELEMETRY_FRAME_TIMEOUT_US)
    {
        // Reinitialize a stalled transmitter; discard entire software queue.
        // A partially sent wire frame is diagnostic loss, never a control command.
        SCI_resetTxFIFO(SCIA_BASE); // 超时清硬件待发数据；已在电线上发出的半帧无法撤回，由后续尾标恢复对齐。
        g_telemetryTimeoutCount++;
        g_telemetryDroppedFrames += s_queued; // 超时丢弃全部剩余队列，包括未发送完的活动帧。
        s_head = s_tail = s_queued = s_offset = 0U;
        return;
    }
    while (s_queued != 0U && sent < TX_FRAME_OCTETS &&
           SCI_getTxFIFOStatus(SCIA_BASE) != SCI_FIFO_TX16)
    {
        SCI_writeCharNonBlocking(SCIA_BASE, s_frames[s_head][s_offset++]); // 先确认 FIFO 未满后写一个字节，不等待串口发送完成。
        sent++;
        if (s_offset == TX_FRAME_OCTETS) // 完整帧放入 FIFO 才切换下一帧，一次服务仍最多处理 16 个字节。
        {
            s_offset = 0U;
            s_head = (s_head + 1U) % TX_QUEUE_FRAMES;
            s_queued--;
            s_frameTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        }
    }
}
