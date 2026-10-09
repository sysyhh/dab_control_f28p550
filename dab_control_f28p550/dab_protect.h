//#############################################################################
//
// FILE:   dab_protect.h
//
// TITLE:  Fault Protection & Safe Trip Management for DAB on F28P550
//
//#############################################################################

#ifndef DAB_PROTECT_H_
#define DAB_PROTECT_H_

#include "dab_types.h"

//=============================================================================
// Global Protection State
//=============================================================================
extern volatile Dab_ProtectFlags_t g_protectFlags; // 标志名字不表示全部保护已实现，当前实际检测见 dab_protect.c。

//=============================================================================
// Function Prototypes
//=============================================================================
void DAB_Protect_init(void); // 建立低有效外部故障的 GPIO/XBAR 输入。

// Returns true if a latching fault condition is present
bool DAB_Protect_checkFault(void); // 检查门限和硬件锁存，同时维护正常恢复资格；故障保持停机。

// Clear only while stopped, with valid sensing and inactive fault input.
bool DAB_Protect_clearFault(void); // 正常至少 5 ms 且采样就绪等条件全部成立才人工清除，不自动启动。

#endif // DAB_PROTECT_H_
