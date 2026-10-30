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
  static void* constant_15_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_14_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_11_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_8_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_7_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_9_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_13_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_5_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_10_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_3_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_6_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_2_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_4_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_1_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_0_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* constant_12_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C" {
#endif
  static void* sid_19_let;
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
  static void* sid_13_let;
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
  static void* sid_20_let;
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
  static void* sid_1_let;
#ifdef __cplusplus
} // extern "C"
#endif
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_6_var, uint8_t* global_workspace_7_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_multiply(int8_t* p0, float* T_multiply, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast(float* p0, int8_t* T_cast, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var);
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
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_0(int8_t*, int8_t*, int32_t*, uint8_t*, uint8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_1(int8_t*, int8_t*, int32_t*, uint8_t*, uint8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_2(int8_t*, int8_t*, int32_t*, uint8_t*, uint8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_3(int8_t*, int8_t*, int32_t*, uint8_t*, uint8_t*, int8_t*, uint8_t*, uint8_t*);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_6_var, uint8_t* global_workspace_7_var) {
  for (int32_t ax1 = 0; ax1 < 29; ++ax1) {
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
TVM_DLL int32_t tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(uint8_t* p0, uint8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var) {
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
TVM_DLL int32_t tvmgen_default_fused_cast_multiply(int8_t* p0, float* T_multiply, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var) {
  for (int32_t ax1 = 0; ax1 < 4; ++ax1) {
    T_multiply[ax1] = (((float)p0[ax1]) * 1.562500e-02f);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast(float* p0, int8_t* T_cast, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var) {
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
   constant_15_let = (&(global_const_workspace_0_var[1520]));
   constant_14_let = (&(global_const_workspace_0_var[1536]));
   constant_11_let = (&(global_const_workspace_0_var[1472]));
   constant_8_let = (&(global_const_workspace_0_var[928]));
   constant_7_let = (&(global_const_workspace_0_var[1440]));
   constant_9_let = (&(global_const_workspace_0_var[1312]));
   constant_13_let = (&(global_const_workspace_0_var[1504]));
   constant_5_let = (&(global_const_workspace_0_var[1344]));
   constant_10_let = (&(global_const_workspace_0_var[1488]));
   constant_3_let = (&(global_const_workspace_0_var[1376]));
   constant_6_let = (&(global_const_workspace_0_var[1456]));
   constant_2_let = (&(global_const_workspace_0_var[1408]));
   constant_4_let = (&(global_const_workspace_0_var[0]));
   constant_1_let = (&(global_const_workspace_0_var[1248]));
   constant_0_let = (&(global_const_workspace_0_var[464]));
   constant_12_let = (&(global_const_workspace_0_var[1184]));
   sid_19_let = (&(global_workspace_1_var[0]));
   sid_14_let = (&(global_workspace_1_var[16]));
   sid_13_let = (&(global_workspace_1_var[0]));
   sid_8_let = (&(global_workspace_1_var[32]));
   sid_7_let = (&(global_workspace_1_var[0]));
   sid_20_let = (&(global_workspace_1_var[16]));
   sid_2_let = (&(global_workspace_1_var[32]));
   sid_1_let = (&(global_workspace_1_var[0]));
  tvmgen_default_fused_multiply_add_floor_clip_cast(features_buffer_var, sid_1_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_ti_npu_fullyConnected_0(sid_1_let, constant_0_let, constant_1_let, constant_2_let, constant_3_let, sid_2_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(sid_2_let, sid_7_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_ti_npu_fullyConnected_1(sid_7_let, constant_4_let, constant_5_let, constant_6_let, constant_7_let, sid_8_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(sid_8_let, sid_13_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_ti_npu_fullyConnected_2(sid_13_let, constant_8_let, constant_9_let, constant_10_let, constant_11_let, sid_14_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(sid_14_let, sid_19_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_ti_npu_fullyConnected_3(sid_19_let, constant_12_let, constant_13_let, constant_14_let, constant_15_let, sid_20_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_cast_multiply(sid_20_let, output_buffer_var, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_finished = 1;
  break;
default:
  break;
}
}

