//#############################################################################
//
// FILE:   dab_adc.h
//
// TITLE:  Dual-ADC Sampling & Filtering Subsystem for DAB on F28P550
//
//#############################################################################

#ifndef DAB_ADC_H_
#define DAB_ADC_H_

#include "dab_types.h"

//=============================================================================
// Global Sensing Data Object
//=============================================================================
extern volatile Dab_Sensing_t g_sensing; // 最近有效帧的原始/物理/平均数值；是否可用还须查 isReady。
extern volatile uint32_t g_adcFrameCount; // 已接受有效帧总数，不等于最近连续有效帧数。
extern volatile uint32_t g_adcInvalidFrameCount; // 不完整、溢出、超期等异常计数。
extern volatile uint16_t g_adcRecoveryFrameCount; // 最近连续有效帧计数，上限 50，无效或中断过久清零。
extern volatile uint32_t g_adcLastFrameTick; // 最近有效读取结束的 Timer2 向下计数值，不是采样触发时间。

//=============================================================================
// Function Prototypes
//=============================================================================

// Initialize ADCA & ADCB with EPWM1 SOCA triggers
void DAB_ADC_init(void); // 配置 A/B 两个 ADC，各两路，由 EPWM1 零点触发。

// Read ADC results and update sliding average filters (called in dab_control_ISR)
bool DAB_ADC_read(void); // 控制中断调用；整帧校验通过才更新数据和滤波，失败返回 false。
bool DAB_ADC_isReady(void); // 连续 50 帧、最新有效且不超过 150 μs 才返回 true。

#endif // DAB_ADC_H_
