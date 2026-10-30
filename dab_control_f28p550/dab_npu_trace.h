/* NPU 分段编号；仅详细计时库调用，普通库编译时移除调用。 */
#ifndef DAB_NPU_TRACE_H_
#define DAB_NPU_TRACE_H_
#include <stdint.h>
enum {
    DAB_NPU_INPUT=0, DAB_NPU_PACK, DAB_NPU_UNPACK, DAB_NPU_CONVERT,
    DAB_NPU_PARAMS, DAB_NPU_INS, DAB_NPU_REGISTERS,
    DAB_NPU_WAIT0, DAB_NPU_WAIT1, DAB_NPU_WAIT2, DAB_NPU_WAIT3,
    DAB_NPU_OUTPUT, DAB_NPU_TRACE_SLOTS
};
void DAB_NN_traceBegin(uint16_t slot);
void DAB_NN_traceEnd(uint16_t slot);
/* NPU 完成中断入口/出口；只记 CPU 执行，不含 TINIE_start 之后的硬件等待。 */
void DAB_NN_isrEnter(void);
void DAB_NN_isrExit(uint16_t layer);
#endif
