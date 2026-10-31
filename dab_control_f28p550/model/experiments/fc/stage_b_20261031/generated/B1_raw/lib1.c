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
static uint8_t* global_workspace_0_var;
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
  static void* sid_13_let;
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
  static void* sid_8_let;
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
  static void* sid_5_let;
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
  static void* sid_9_let;
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
  static void* sid_15_let;
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
extern "C" {
#endif
  static void* sid_3_let;
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
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_workspace_5_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_workspace_9_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_multiply(int8_t* p0, float* T_multiply, uint8_t* global_workspace_14_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast(float* p0, int8_t* T_cast, uint8_t* global_workspace_1_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack(int8_t* p0, int8_t* tinie_c28_pack_generic, uint8_t* global_workspace_2_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_1(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_workspace_6_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_2(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_workspace_10_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_4_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_1(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_8_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_2(int8_t* p0, int8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_13_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default___tvm_main__(float* features_buffer_var, float* output_buffer_var, uint8_t* global_workspace_0_var);
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
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t*, int8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int8_t*, int8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int8_t*, int8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int8_t*, int8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_workspace_5_var) {
  for (int32_t ax1 = 0; ax1 < 32; ++ax1) {
    float v_ = ((float)((int32_t)p0[ax1])) * 3.906250e-03f;
    float v__1 = floorf(((((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f)) * 2.560000e+02f) + 5.000000e-01f));
    float v__2 = (v__1) < (2.550000e+02f) ? (v__1) : (2.550000e+02f);
    T_cast[ax1] = ((uint8_t)((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f)));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_workspace_9_var) {
  for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float v_ = ((float)((int32_t)p0[ax1])) * 3.906250e-03f;
    float v__1 = floorf(((((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f)) * 2.560000e+02f) + 5.000000e-01f));
    float v__2 = (v__1) < (2.550000e+02f) ? (v__1) : (2.550000e+02f);
    T_cast[ax1] = ((uint8_t)((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f)));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_multiply(int8_t* p0, float* T_multiply, uint8_t* global_workspace_14_var) {
  for (int32_t ax1 = 0; ax1 < 4; ++ax1) {
    T_multiply[ax1] = (((float)p0[ax1]) * 1.562500e-02f);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast(float* p0, int8_t* T_cast, uint8_t* global_workspace_1_var) {
  for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float v_ = floorf(((p0[ax1] * 6.400000e+01f) + 5.000000e-01f));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    T_cast[ax1] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack(int8_t* p0, int8_t* tinie_c28_pack_generic, uint8_t* global_workspace_2_var) {
  for (int32_t i = 0; i < 16; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_1(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_workspace_6_var) {
  for (int32_t i = 0; i < 32; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_pack_2(uint8_t* p0, uint8_t* tinie_c28_pack_generic, uint8_t* global_workspace_10_var) {
  for (int32_t i = 0; i < 16; ++i) {
    c28_pack((&(p0[0])), (&(tinie_c28_pack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_4_var) {
  for (int32_t i = 0; i < 32; ++i) {
    c28_unpack_unsigned((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_1(uint8_t* p0, uint8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_8_var) {
  for (int32_t i = 0; i < 16; ++i) {
    c28_unpack_unsigned((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_tinie_c28_unpack_2(int8_t* p0, int8_t* tinie_c28_unpack_generic, uint8_t* global_workspace_13_var) {
  for (int32_t i = 0; i < 4; ++i) {
    c28_unpack_signed((&(p0[0])), (&(tinie_c28_unpack_generic[0])), i);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default___tvm_main__(float* features_buffer_var_arg, float* output_buffer_var_arg, uint8_t* global_workspace_0_var_arg) {
  tinie_curr_layer = 0;
  tvmgen_default_finished = 0;
  tinie_curr_sublayer = 0;
  tinie_num_sublayers = 0;
  tinie_sublayer_postproc = NULL;
  TINIE_registerInterrupt(tvmgen_default_IRQHandler);
  features_buffer_var = features_buffer_var_arg;
  output_buffer_var = output_buffer_var_arg;
  global_workspace_0_var = global_workspace_0_var_arg;
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
   sid_16_let = (&(global_workspace_0_var[0]));
   sid_13_let = (&(global_workspace_0_var[16]));
   sid_12_let = (&(global_workspace_0_var[0]));
   sid_11_let = (&(global_workspace_0_var[16]));
   sid_10_let = (&(global_workspace_0_var[32]));
   sid_8_let = (&(global_workspace_0_var[16]));
   sid_7_let = (&(global_workspace_0_var[32]));
   sid_6_let = (&(global_workspace_0_var[0]));
   sid_5_let = (&(global_workspace_0_var[32]));
   sid_14_let = (&(global_workspace_0_var[0]));
   sid_9_let = (&(global_workspace_0_var[0]));
   sid_4_let = (&(global_workspace_0_var[0]));
   sid_15_let = (&(global_workspace_0_var[16]));
   sid_2_let = (&(global_workspace_0_var[0]));
   sid_3_let = (&(global_workspace_0_var[32]));
   sid_1_let = (&(global_workspace_0_var[16]));
  tvmgen_default_fused_multiply_add_floor_clip_cast(features_buffer_var, sid_1_let, global_workspace_0_var);
  tvmgen_default_fused_tinie_c28_pack(sid_1_let, sid_2_let, global_workspace_0_var);
  tvmgen_default_ti_npu_fullyConnectedNHWC_0(sid_2_let, sid_3_let, global_workspace_0_var);
  return;
case 1:
  tvmgen_default_fused_tinie_c28_unpack(sid_3_let, sid_4_let, global_workspace_0_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(sid_4_let, sid_5_let, global_workspace_0_var);
  tvmgen_default_fused_tinie_c28_pack_1(sid_5_let, sid_6_let, global_workspace_0_var);
  tvmgen_default_ti_npu_fullyConnectedNHWC_1(sid_6_let, sid_7_let, global_workspace_0_var);
  return;
case 2:
  tvmgen_default_fused_tinie_c28_unpack_1(sid_7_let, sid_8_let, global_workspace_0_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(sid_8_let, sid_9_let, global_workspace_0_var);
  tvmgen_default_fused_tinie_c28_pack_2(sid_9_let, sid_10_let, global_workspace_0_var);
  tvmgen_default_ti_npu_fullyConnectedNHWC_2(sid_10_let, sid_11_let, global_workspace_0_var);
  return;
case 3:
  tvmgen_default_fused_tinie_c28_unpack_1(sid_11_let, sid_12_let, global_workspace_0_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(sid_12_let, sid_13_let, global_workspace_0_var);
  tvmgen_default_fused_tinie_c28_pack_2(sid_13_let, sid_14_let, global_workspace_0_var);
  tvmgen_default_ti_npu_fullyConnectedNHWC_3(sid_14_let, sid_15_let, global_workspace_0_var);
  return;
case 4:
  tvmgen_default_fused_tinie_c28_unpack_2(sid_15_let, sid_16_let, global_workspace_0_var);
  tvmgen_default_fused_cast_multiply(sid_16_let, output_buffer_var, global_workspace_0_var);
  tvmgen_default_finished = 1;
  break;
default:
  break;
}
}

