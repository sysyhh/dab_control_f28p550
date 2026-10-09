//#############################################################################
//
// FILE:   dab_types.h
//
// TITLE:  Type definitions and configuration macros for DAB Converter on F28P550
//
//#############################################################################

#ifndef DAB_TYPES_H_
#define DAB_TYPES_H_

#include <stdint.h>
#include <stdbool.h>
#include "driverlib.h"
#include "device.h"
#include "dab_board_config.h"

//=============================================================================
// DAB Operating Parameters & Constants
//=============================================================================
#define DAB_BASE_TBPRD          2500U           // 150MHz / (2 * 2500) = 30kHz (Up-down mode) // 功率 PWM 基准；变周期 T=0.5～2 对应 60～15 kHz。
#define DAB_DEADBAND_RED_FED    50U             // Deadband counts (~333ns @ 150MHz)

#define DAB_CTRL_FREQ_HZ        10000U          // Control loop execution frequency: 10kHz
#define DAB_CTRL_TBPRD          7500U           // EPWM5 up-down: 150MHz / (2 * 7500) = 10kHz // 实际控制节拍由此计数上限决定，只改频率说明常量不会改变硬件。

#define DAB_SOFT_CNT_MAX        1000U           // Soft-start counter maximum // 软启动累计新装载进度 1000 次；正常约 100 ms，并非盲目计时启动。
#define DAB_ERR_LIMIT           40.0f           // Error saturation limit
#define DAB_INT_LIMIT           0.15f           // Match the PI output range
#define DAB_DUTY_MAX            0.15f           // Max PI duty limit (0.15)

//=============================================================================
// Reference calibration: must be checked on the actual F28P550 sampling board
//=============================================================================
#define BUCK_VOUT_P_SCALE       0.0615f
#define BUCK_VOUT_P_BIAS        0.6465f

#define BUCK_VOUT_N_SCALE       0.0303f
#define BUCK_VOUT_N_BIAS        0.2903f

#define BUCK_IL_COEF            DAB_IL_SCALE
#define BUCK_IL_BIAS            DAB_IL_OFFSET
#define BUCK_IOUT_COEF          DAB_IOUT_SCALE
#define BUCK_IOUT_BIAS          DAB_IOUT_OFFSET

//=============================================================================
// State Machine Enumeration
//=============================================================================
typedef enum
{
    DAB_STATE_INIT = 0,
    DAB_STATE_STANDBY,
    DAB_STATE_SOFT_START,
    DAB_STATE_RUN,
    DAB_STATE_FAULT // 故障锁存，人工清除后只回待机，不直接运行。
} Dab_State_e;

//=============================================================================
// Protection Flags Union
//=============================================================================
typedef struct
{
    uint16_t PSFB_Fault_Flag     : 1;  // Bit 0: Primary bridge fault
    uint16_t Tep_Flag            : 1;  // Bit 1: Over-temperature
    uint16_t Iout_Open_Flag      : 1;  // Bit 2: Output open
    uint16_t Iout_Short_Flag     : 1;  // Bit 3: Short-circuit
    uint16_t Iout_OCP_Flag       : 1;  // Bit 4: Output over-current
    uint16_t Vout_OVP_Flag       : 1;  // Bit 5: Output over-voltage
    uint16_t Vin_OVP_Flag        : 1;  // Bit 6: Input over-voltage
    uint16_t Vin_UVP_Flag        : 1;  // Bit 7: Input under-voltage
    uint16_t Work_Flag           : 1;  // Bit 8: Working status
    uint16_t H_OCP_Flag          : 1;  // Bit 9: Hardware comparator trip
    uint16_t L_OCP_Flag          : 1;  // Bit 10: Inductor over-current
    uint16_t OVP_Flag            : 1;  // Bit 11: General over-voltage
    uint16_t UVP_Flag            : 1;  // Bit 12: General under-voltage
    uint16_t Stop_Flag           : 1;  // Bit 13: Stop status
    uint16_t Reserved            : 2;  // Bit 14-15
} Dab_ProtectBits_t;
// 部分字段预留但未实现检测；真实软件门限、外部故障和恢复规则以 dab_protect.c 为准。

typedef union
{
    uint16_t all;
    Dab_ProtectBits_t bit;
} Dab_ProtectFlags_t;

//=============================================================================
// Sensing Data Structure
//=============================================================================
typedef struct
{
    // Raw ADC readings
    uint16_t vout_p_raw;
    uint16_t vout_n_raw;
    uint16_t iout_raw;
    uint16_t il_raw;
    uint16_t vin_raw; // 当前没有 Vin SOC，该字段不能当作真实输入电压采样。

    // Instantaneous physical values
    float vout_p;
    float vout_n;
    float iout;
    float il;
    float vin;

    // Filtered / moving average values
    float vout_p_ave;
    float vout_n_ave;
    float il_ave;
    float vin_ave;
} Dab_Sensing_t;
// raw 是 12 位 ADC 原始计数；瞬时量用于保护；平均量用于当前电压反馈和显示。
// 字段仍保留最后有效值，运行可信度应同时检查 DAB_ADC_isReady。

//=============================================================================
// Modulation & PWM Parameters
//=============================================================================
typedef struct
{
    float D1;               // Primary internal phase shift
    float D1_pha;           // 1.0 - D1
    float D0;               // Primary-to-secondary phase shift
    float D2;               // Secondary internal phase shift
    float D2_pha;           // 1.0 - D2
    float T_gain;           // Switching period scaling (variable frequency)
    float F_duty;           // Closed-loop PI correction term // PI 相移修正量，默认开环为零，不是开关管实际占空比。

    uint32_t tbprd_var;     // Dynamic period register value
} Dab_PwmParams_t;

//=============================================================================
// PI Controller Structure
//=============================================================================
typedef struct
{
    float kp;
    float ki; // 每次离散控制的积分增量系数，改变控制频率须重新设计。
    float ref;
    float fed;
    float err;
    float integral;
    float out;
} Dab_PiController_t;

#endif // DAB_TYPES_H_
