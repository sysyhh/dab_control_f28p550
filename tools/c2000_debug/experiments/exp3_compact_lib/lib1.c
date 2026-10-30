#pragma CODE_SECTION(dab_npu_copy_words, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tinie_sublayer_IRQHandler, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_IRQHandler, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_2, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_cast_multiply_reshape, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_reshape_multiply_add_floor_clip_cast_reshape, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_pack, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_pack_1, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_pack_2, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_pack_3, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_unpack, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_unpack_1, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_unpack_2, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_fused_tinie_c28_unpack_3, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default___tvm_main__, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_IRQHandlerHelper, ".dab_npu_ramfunc")
#define DAB_NPU_DETAIL_PROFILE 0
#include "dab_npu_trace.h"
extern void DAB_NN_noteNpuCompletion(void);
/*****************************************************************************/
/* Copyright (c) 2025 Texas Instruments Incorporated                         */
/* http://www.ti.com/                                                        */
/*                                                                           */
/*  Redistribution and  use in source  and binary forms, with  or without    */
/*  modification,  are permitted provided  that the  following conditions    */
/*  are met:                                                                 */
/*                                                                           */
/*     Redistributions  of source  code must  retain the  above copyright    */
/*     notice, this list of conditions and the following disclaimer.         */
/*                                                                           */
/*     Redistributions in binary form  must reproduce the above copyright    */
/*     notice, this  list of conditions  and the following  disclaimer in    */
/*     the  documentation  and/or   other  materials  provided  with  the    */
/*     distribution.                                                         */
/*                                                                           */
/*     Neither the  name of Texas Instruments Incorporated  nor the names    */
/*     of its  contributors may  be used to  endorse or  promote products    */
/*     derived  from   this  software  without   specific  prior  written    */
/*     permission.                                                           */
/*                                                                           */
/*  THIS SOFTWARE  IS PROVIDED BY THE COPYRIGHT  HOLDERS AND CONTRIBUTORS    */
/*  "AS IS"  AND ANY  EXPRESS OR IMPLIED  WARRANTIES, INCLUDING,  BUT NOT    */
/*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR    */
/*  A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT    */
/*  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,    */
/*  SPECIAL,  EXEMPLARY,  OR CONSEQUENTIAL  DAMAGES  (INCLUDING, BUT  NOT    */
/*  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,    */
/*  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY    */
/*  THEORY OF  LIABILITY, WHETHER IN CONTRACT, STRICT  LIABILITY, OR TORT    */
/*  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE    */
/*  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.     */
/*                                                                           */
/*****************************************************************************/
// tvm target: c -keys=arm_cpu,cpu -mcpu=cortex-m0plus
#include "tvm/runtime/contrib/tvm_tinie_c28.h"
#define TVM_EXPORTS
#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/c_backend_api.h"
#include <math.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif
#include "hard/inc/tinie.h"
volatile int32_t tinie_curr_layer __attribute__((weak));
volatile int32_t tinie_curr_sublayer __attribute__((weak));
volatile int32_t tinie_num_sublayers __attribute__((weak));
void (*tinie_sublayer_postproc)(void) __attribute__((weak));
volatile int32_t tvmgen_default_finished;
TVM_DLL int32_t dab_npu_copy_words(uint16_t* source, uint16_t* destination, uint16_t words) {
  /* C28 一个存储单元包含两个 8 位通道；保持原目标缓冲区，避免下一层输入和输出重叠。 */

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PACK);
#endif
  for (uint16_t i = 0; i < words; ++i) destination[i] = source[i];

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PACK);
#endif
  return 0;
}
void tvmgen_default_IRQHandlerHelper();
TINIE_layer_t* __attribute__((weak)) tinie_sublayers;
__attribute__((weak)) void tinie_sublayer_IRQHandler() {
  if (tinie_sublayer_postproc != NULL)  tinie_sublayer_postproc();

  TINIE_setup(&tinie_sublayers[tinie_curr_sublayer]);
  tinie_curr_sublayer += 1;
  TINIE_start();
  return;
}
__attribute__((interrupt)) void tvmgen_default_IRQHandler() {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_WAIT0 + tinie_curr_layer - 1);
#endif

  (void) tvmgen_default_IRQHandlerHelper();
}
#ifdef __cplusplus
} // extern "C"
#endif

#ifdef __cplusplus
extern "C" {
#endif
static float* features_buffer_var;
#ifdef __cplusplus
} // extern "C"
#endif

#ifdef __cplusplus
extern "C" {
#endif
static float* output_buffer_var;
#ifdef __cplusplus
} // extern "C"
#endif

#ifdef __cplusplus
extern "C" {
#endif
static uint8_t* global_const_workspace_0_var;
#ifdef __cplusplus
} // extern "C"
#endif

#ifdef __cplusplus
extern "C" {
#endif
static uint8_t* global_workspace_1_var;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_14_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_11_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_10_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_16_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_9_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_12_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_7_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_6_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_15_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_5_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_3_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_4_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_8_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_1_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_13_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_2_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_18_var, uint8_t* global_workspace_19_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_2(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_26_var, uint8_t* global_workspace_27_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_multiply_reshape(int8_t* p0, float* T_reshape, uint8_t* global_const_workspace_34_var, uint8_t* global_workspace_35_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_multiply_add_floor_clip_cast_reshape(float* p0, int8_t* T_reshape, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack(int8_t* p0, int8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_4_var, uint8_t* global_workspace_5_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_1(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_12_var, uint8_t* global_workspace_13_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_2(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_20_var, uint8_t* global_workspace_21_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_3(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_28_var, uint8_t* global_workspace_29_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_8_var, uint8_t* global_workspace_9_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_1(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_2(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_24_var, uint8_t* global_workspace_25_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_3(int8_t* p0, int8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_32_var, uint8_t* global_workspace_33_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default___tvm_main__(float* features_buffer_var, float* output_buffer_var, uint8_t* global_const_workspace_0_var, uint8_t* global_workspace_1_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL float floorf(float);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL float floorf(float);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL float floorf(float);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL float floorf(float);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_0(int8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_1(int8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_2(int8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_3(int8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_CONVERT);
#endif

  /* uint8 全范围逐值验证：逆缩放、ReLU、再缩放及取整的结果均为原值。 */
  for (int32_t i = 0; i < 32; ++i) T_cast[i] = p0[i];

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_CONVERT);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_18_var, uint8_t* global_workspace_19_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_CONVERT);
#endif

  /* uint8 全范围逐值验证：逆缩放、ReLU、再缩放及取整的结果均为原值。 */
  for (int32_t i = 0; i < 12; ++i) T_cast[i] = p0[i];

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_CONVERT);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_2(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_26_var, uint8_t* global_workspace_27_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_CONVERT);
#endif

  /* uint8 全范围逐值验证：逆缩放、ReLU、再缩放及取整的结果均为原值。 */
  for (int32_t i = 0; i < 8; ++i) T_cast[i] = p0[i];

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_CONVERT);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_multiply_reshape(int8_t* p0, float* T_reshape, uint8_t* global_const_workspace_34_var, uint8_t* global_workspace_35_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_OUTPUT);
#endif

  for (int32_t ax3 = 0; ax3 < 4; ++ax3) {
    T_reshape[ax3] = (((float)p0[ax3]) * 1.562500e-02f);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_OUTPUT);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_multiply_add_floor_clip_cast_reshape(float* p0, int8_t* T_reshape, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_INPUT);
#endif

  void* fused_reshape_multiply_constant_let = (&(global_const_workspace_2_var[0]));
  void* fused_reshape_constant_let = (&(global_const_workspace_2_var[16]));
  for (int32_t ax3 = 0; ax3 < 4; ++ax3) {
    float v_ = floorf(((p0[ax3] * ((float*)fused_reshape_constant_let)[0]) + ((float*)fused_reshape_multiply_constant_let)[0]));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    T_reshape[ax3] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_INPUT);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack(int8_t* p0, int8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_4_var, uint8_t* global_workspace_5_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PACK);
#endif

  for (int32_t i = 0; i < 4; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_1(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_12_var, uint8_t* global_workspace_13_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PACK);
#endif

  for (int32_t i = 0; i < 32; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_2(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_20_var, uint8_t* global_workspace_21_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PACK);
#endif

  for (int32_t i = 0; i < 12; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_3(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_const_workspace_28_var, uint8_t* global_workspace_29_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PACK);
#endif

  for (int32_t i = 0; i < 8; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_8_var, uint8_t* global_workspace_9_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_UNPACK);
#endif

  for (int32_t i = 0; i < 32; ++i) {
    c28_unpack_unsigned((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_UNPACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_1(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_UNPACK);
#endif

  for (int32_t i = 0; i < 12; ++i) {
    c28_unpack_unsigned((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_UNPACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_2(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_24_var, uint8_t* global_workspace_25_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_UNPACK);
#endif

  for (int32_t i = 0; i < 8; ++i) {
    c28_unpack_unsigned((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_UNPACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_3(int8_t* p0, int8_t* tinie_c28_unpack_generic, uint8_t* global_const_workspace_32_var, uint8_t* global_workspace_33_var) {
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_UNPACK);
#endif

  for (int32_t i = 0; i < 4; ++i) {
    c28_unpack_signed((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_UNPACK);
#endif
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default___tvm_main__(float* features_buffer_var_arg, float* output_buffer_var_arg, uint8_t* global_const_workspace_0_var_arg, uint8_t* global_workspace_1_var_arg) {
  tinie_curr_layer = 0;
  tvmgen_default_finished = 0;
  tinie_curr_sublayer = 0;
  tinie_num_sublayers = 0;
  tinie_sublayer_postproc = NULL;
  TINIE_registerInterrupt(tvmgen_default_IRQHandler);
  features_buffer_var = features_buffer_var_arg;
  output_buffer_var = output_buffer_var_arg;
  global_const_workspace_0_var = global_const_workspace_0_var_arg;
  global_workspace_1_var = global_workspace_1_var_arg;
  (void)tvmgen_default_IRQHandlerHelper();
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL void tvmgen_default_IRQHandlerHelper() {
  TINIE_clearInterruptACK();
  if (tinie_curr_sublayer < tinie_num_sublayers) {
    tinie_sublayer_IRQHandler();
    return;
  }
switch(tinie_curr_layer) {
case 0:
   sid_14_let = (&(global_workspace_1_var[0]));
   sid_11_let = (&(global_workspace_1_var[32]));
   sid_10_let = (&(global_workspace_1_var[16]));
   sid_16_let = (&(global_workspace_1_var[0]));
   sid_9_let = (&(global_workspace_1_var[0]));
   sid_12_let = (&(global_workspace_1_var[0]));
   sid_7_let = (&(global_workspace_1_var[32]));
   sid_6_let = (&(global_workspace_1_var[0]));
   sid_15_let = (&(global_workspace_1_var[16]));
   sid_5_let = (&(global_workspace_1_var[32]));
   sid_3_let = (&(global_workspace_1_var[32]));
   sid_4_let = (&(global_workspace_1_var[0]));
   sid_8_let = (&(global_workspace_1_var[16]));
   sid_1_let = (&(global_workspace_1_var[16]));
   sid_13_let = (&(global_workspace_1_var[16]));
   sid_2_let = (&(global_workspace_1_var[0]));
  tvmgen_default_fused_reshape_multiply_add_floor_clip_cast_reshape(features_buffer_var, sid_1_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_tinie_c28_pack(sid_1_let, sid_2_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_ti_npu_convolve1x1NHWC_0(sid_2_let, sid_3_let, global_const_workspace_0_var, global_workspace_1_var);
  return;
case 1:
  dab_npu_copy_words((uint16_t*)sid_3_let, (uint16_t*)sid_6_let, 16U);
  tvmgen_default_ti_npu_convolve1x1NHWC_1(sid_6_let, sid_7_let, global_const_workspace_0_var, global_workspace_1_var);
  return;
case 2:
  dab_npu_copy_words((uint16_t*)sid_7_let, (uint16_t*)sid_10_let, 6U);
  tvmgen_default_ti_npu_convolve1x1NHWC_2(sid_10_let, sid_11_let, global_const_workspace_0_var, global_workspace_1_var);
  return;
case 3:
  dab_npu_copy_words((uint16_t*)sid_11_let, (uint16_t*)sid_14_let, 4U);
  tvmgen_default_ti_npu_convolve1x1NHWC_3(sid_14_let, sid_15_let, global_const_workspace_0_var, global_workspace_1_var);
  return;
case 4:
  tvmgen_default_fused_tinie_c28_unpack_3(sid_15_let, sid_16_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_cast_multiply_reshape(sid_16_let, output_buffer_var, global_const_workspace_0_var, global_workspace_1_var);
  DAB_NN_noteNpuCompletion(); /* Final output is ready; stamp before publication. */
  tvmgen_default_finished = 1;
  break;
default:
  break;
}
}

