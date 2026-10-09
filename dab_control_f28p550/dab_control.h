//#############################################################################
//
// FILE:   dab_control.h
//
// TITLE:  Real-Time Control Loop, State Machine & PI Regulator for DAB on F28P550
//
//#############################################################################

#ifndef DAB_CONTROL_H_
#define DAB_CONTROL_H_

#include "dab_types.h"
typedef enum {
    DAB_FAULT_NONE = 0, DAB_FAULT_LIMIT, DAB_FAULT_HARDWARE,
    DAB_FAULT_ADC, DAB_FAULT_NN, DAB_FAULT_PWM_TIMEOUT,
    DAB_FAULT_PWM_WINDOW, DAB_FAULT_MODULATION
} Dab_FaultReason_e;
typedef struct {
    Dab_FaultReason_e reason;
    Dab_State_e state;
    uint32_t tick, adcFrame, pwmSequence;
    uint16_t ilRaw, voutRaw;
} Dab_FaultRecord_t;
extern volatile Dab_FaultRecord_t g_firstFault; // 首次故障现场，后续故障或普通停止不会覆盖。
// Rejection codes: 0 accepted, 1 board, 2 state, 3 ADC, 4 NN, 5 protection.
extern volatile uint16_t g_startRejectReason; // 0 接受、1 板未确认、2 状态、3 ADC、4 NN、5 保护、6 NN 测试中、7 NPU 候选精度未批准。

//=============================================================================
// Global Objects
//=============================================================================
extern volatile Dab_State_e g_dabState;
extern volatile Dab_PwmParams_t g_pwmParams;
extern volatile Dab_PiController_t g_piCtrl;
extern volatile bool g_startRequested;
extern volatile bool g_stopRequested;
extern volatile bool g_clearFaultRequested;

//=============================================================================
// Function Prototypes
//=============================================================================

// Initialize control state machine, PI parameters, and modulation parameters
void DAB_Control_init(void);

// Real-time control step executed inside 10kHz ISR
void DAB_Control_step(void); // 10 kHz 更新软启动、可选电压 PI 及 PWM 请求，不等待推理。

// 设置输出电压参考；当前控制反馈为 vout_n_ave，不是电流参考。
void DAB_Control_setRef(float ref_val);

// Start converter (enters soft-start -> run)
bool DAB_Control_start(void); // 只从待机批准启动；成功也要首包装载之后才真正释放 PWM。

// Stop converter (enters standby)
void DAB_Control_stop(void); // 立即软件关断，正常回待机，故障状态仍保持锁存。
void DAB_Control_fault(void);
void DAB_Control_faultReason(Dab_FaultReason_e reason);
void DAB_Control_resetFaultRecord(void); // 仅初始化或已批准清故障时重置记录，不能借此绕过恢复条件。

#endif // DAB_CONTROL_H_
