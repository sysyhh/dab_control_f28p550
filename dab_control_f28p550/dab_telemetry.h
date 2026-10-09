//#############################################################################
//
// FILE:   dab_telemetry.h
//
// TITLE:  VOFA+ Serial Telemetry Communication Interface for DAB on F28P550
//
//#############################################################################

#ifndef DAB_TELEMETRY_H_
#define DAB_TELEMETRY_H_

#include "dab_types.h"

//=============================================================================
// Function Prototypes
//=============================================================================
void DAB_Telemetry_init(uint32_t baud_rate); // 配置 SCIA 8N1 和最近整数分频，当前只有遥测发送功能。

// Enqueue one complete 16-octet frame; drop newest when the finite queue is full.
bool DAB_Telemetry_sendVOFA(float ch1, float ch2, float ch3); // 三项 float+尾标共 16 线路字节；队列满丢新整帧并返回 false。
// Foreground only: bounded work, never waits for FIFO space.
void DAB_Telemetry_service(void); // 仅主循环调用，每次最多 16 字节，FIFO 满即返回，超过期限清队列。
extern volatile uint32_t g_telemetryDroppedFrames, g_telemetryTimeoutCount;

#endif // DAB_TELEMETRY_H_
