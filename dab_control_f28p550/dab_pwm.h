//#############################################################################
//
// FILE:   dab_pwm.h
//
// TITLE:  ePWM Multi-Phase Shift & Global Load Subsystem for DAB on F28P550
//
//#############################################################################

#ifndef DAB_PWM_H_
#define DAB_PWM_H_

#include "dab_types.h"

//=============================================================================
// Function Prototypes
//=============================================================================

// Initialize EPWM7/4/5/10 for DAB and EPWM1 for the control timer interrupt
void DAB_PWM_init(void);

// Stage a complete parameter set; the EPWM7 period ISR commits it.
bool DAB_PWM_updateModulation(const Dab_PwmParams_t *params);

// Enable PWM outputs
void DAB_PWM_enable(void); // 只提出使能请求，首次完整装载及保护复核后才解除 OST。

// Safe software shutdown (force trip outputs low)
void DAB_PWM_disable(void); // 强制四桥低电平并取消软件等待，硬件已发的装载请求可能仍发生。
bool DAB_PWM_isEnabled(void); // 表示软件 OST 已实际释放，不等于驱动或门极波形已验收。
bool DAB_PWM_hardwareFault(void); // 检查 GPIO60 或 TZ1 来源锁存，捕捉已经结束的短故障脉冲。
bool DAB_PWM_clearHardwareFault(void); // 仅输出关闭时清外部来源锁存，软件 OST 仍保持关断。
// 首次写入越界现场；初始化或人工成功清故障时同步清零。entryTick-failTick 为 Timer2 经过计数。
typedef struct
{
    uint16_t stage; // 0：无记录；1：参数写完后；2：相位载入恢复后；3：最终装载请求前。
    uint16_t entryCounter, failCounter;
    uint16_t failDirection; // TI 定义：0 向下，1 向上；与 failCounter 顺序读取。
    uint32_t entryTick, failTick; // Timer2 向下计数，150 MHz 时每 150 计数约 1 us。
} Dab_PwmWindowDiag_t;
extern volatile Dab_PwmWindowDiag_t g_pwmWindowDiag;
void DAB_PWM_resetWindowDiag(void); // 与首故障记录同步清零；调用方需保证初始化阶段或已屏蔽中断。
extern volatile uint32_t g_pwmLateCommitCount;
extern volatile uint32_t g_pwmUpdateTimeoutCount, g_pwmAppliedSequence;
extern volatile Dab_PwmParams_t g_pwmAppliedParams; // 最近观察到装载零点的参数，不是活动寄存器或门极波形回读。
extern volatile uint32_t g_controlHeartbeat;
extern volatile uint32_t g_controlLastTick;
// The acknowledgment observes EPWM7 zero after arming, not GLDCTL2 readback.
bool DAB_PWM_checkDeadline(void); // 控制/更新超期即故障，再观察装载事件，防止迟到确认掩盖超时。
__interrupt void dab_pwm_commit_ISR(void); // 在主 PWM 周期顶点提交，启动释放阶段临时处理零点。

// 10kHz Real-Time Control Interrupt Service Routine
__interrupt void dab_control_ISR(void); // EPWM1 周期顶点读取采样、检查保护并计算控制，固定 10 kHz。

#endif // DAB_PWM_H_
