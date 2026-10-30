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
  static void* sid_7_let;
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
  static void* sid_6_let;
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
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast_reshape(float* p0, int8_t* T_reshape, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack(int8_t* p0, int32_t* compute, uint8_t* global_const_workspace_4_var, uint8_t* global_workspace_5_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_8_var, uint8_t* global_workspace_9_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract_1(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_12_var, uint8_t* global_workspace_13_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract_2(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply(int32_t* p0, float* T_multiply, uint8_t* global_const_workspace_18_var, uint8_t* global_workspace_19_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_multiply_add_f_afb9046a28628b23_(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_6_var, uint8_t* global_workspace_7_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb_(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb__1(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_14_var, uint8_t* global_workspace_15_var);
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
TVM_DLL int32_t tvmgen_default_fused_multiply_add_floor_clip_cast_reshape(float* p0, int8_t* T_reshape, uint8_t* global_const_workspace_2_var, uint8_t* global_workspace_3_var) {
  void* fused_multiply_constant_let = (&(global_const_workspace_2_var[1520]));
  void* fused_constant_let = (&(global_const_workspace_2_var[1536]));
  for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float v_ = floorf(((p0[ax1] * ((float*)fused_constant_let)[0]) + ((float*)fused_multiply_constant_let)[0]));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    T_reshape[ax1] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack(int8_t* p0, int32_t* compute, uint8_t* global_const_workspace_4_var, uint8_t* global_workspace_5_var) {
  void* fused_constant_1_let = (&(global_const_workspace_4_var[0]));
  for (int32_t x_outer_y_outer_fused = 0; x_outer_y_outer_fused < 29; ++x_outer_y_outer_fused) {
    void* compute_global_let = (&(global_workspace_5_var[16]));
    ((int32_t*)compute_global_let)[0] = 0;
    for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
      ((int32_t*)compute_global_let)[0] = (((int32_t*)compute_global_let)[0] + (((int32_t)p0[k_outer]) * ((int32_t)((int8_t*)fused_constant_1_let)[((x_outer_y_outer_fused * 16) + k_outer)])));
    }
    compute[x_outer_y_outer_fused] = ((int32_t*)compute_global_let)[0];
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_8_var, uint8_t* global_workspace_9_var) {
  void* fused_nn_contrib_dense_pack_constant_let = (&(global_const_workspace_8_var[1264]));
  void* fused_constant_2_let = (&(global_const_workspace_8_var[464]));
  for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2; ++ax1_outer_ax0_outer_fused) {
    void* compute_global_let = (&(global_workspace_9_var[64]));
    for (int32_t x_c_init = 0; x_c_init < 6; ++x_c_init) {
      ((int32_t*)compute_global_let)[x_c_init] = 0;
    }
    for (int32_t k_outer = 0; k_outer < 29; ++k_outer) {
      for (int32_t x_c = 0; x_c < 6; ++x_c) {
        ((int32_t*)compute_global_let)[x_c] = (((int32_t*)compute_global_let)[x_c] + (((int32_t)p0[k_outer]) * ((int32_t)((int8_t*)fused_constant_2_let)[(((ax1_outer_ax0_outer_fused * 174) + (k_outer * 6)) + x_c)])));
      }
    }
    for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 6; ++ax1_inner_inner) {
      int32_t cse_var_1 = ((ax1_outer_ax0_outer_fused * 6) + ax1_inner_inner);
      T_subtract[cse_var_1] = (((int32_t*)compute_global_let)[ax1_inner_inner] - ((int32_t*)fused_nn_contrib_dense_pack_constant_let)[cse_var_1]);
    }
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract_1(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_12_var, uint8_t* global_workspace_13_var) {
  void* fused_nn_contrib_dense_pack_constant_1_let = (&(global_const_workspace_12_var[1344]));
  void* fused_constant_3_let = (&(global_const_workspace_12_var[816]));
  void* compute_global_let = (&(global_workspace_13_var[32]));
  for (int32_t x_c_init = 0; x_c_init < 6; ++x_c_init) {
    ((int32_t*)compute_global_let)[x_c_init] = 0;
  }
  for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
    for (int32_t x_c = 0; x_c < 6; ++x_c) {
      ((int32_t*)compute_global_let)[x_c] = (((int32_t*)compute_global_let)[x_c] + (((int32_t)p0[k_outer]) * ((int32_t)((int8_t*)fused_constant_3_let)[((k_outer * 6) + x_c)])));
    }
  }
  for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 6; ++ax1_inner_inner) {
    T_subtract[ax1_inner_inner] = (((int32_t*)compute_global_let)[ax1_inner_inner] - ((int32_t*)fused_nn_contrib_dense_pack_constant_1_let)[ax1_inner_inner]);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_nn_contrib_dense_pack_subtract_2(int8_t* p0, int32_t* T_subtract, uint8_t* global_const_workspace_16_var, uint8_t* global_workspace_17_var) {
  void* fused_nn_contrib_dense_pack_constant_2_let = (&(global_const_workspace_16_var[1408]));
  void* fused_constant_4_let = (&(global_const_workspace_16_var[912]));
  void* compute_global_let = (&(global_workspace_17_var[16]));
  for (int32_t x_c_init = 0; x_c_init < 4; ++x_c_init) {
    ((int32_t*)compute_global_let)[x_c_init] = 0;
  }
  for (int32_t k_outer = 0; k_outer < 16; ++k_outer) {
    for (int32_t x_c = 0; x_c < 4; ++x_c) {
      ((int32_t*)compute_global_let)[x_c] = (((int32_t*)compute_global_let)[x_c] + (((int32_t)p0[k_outer]) * ((int32_t)((int8_t*)fused_constant_4_let)[((k_outer * 4) + x_c)])));
    }
  }
  for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 4; ++ax1_inner_inner) {
    T_subtract[ax1_inner_inner] = (((int32_t*)compute_global_let)[ax1_inner_inner] - ((int32_t*)fused_nn_contrib_dense_pack_constant_2_let)[ax1_inner_inner]);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply(int32_t* p0, float* T_multiply, uint8_t* global_const_workspace_18_var, uint8_t* global_workspace_19_var) {
  void* fused_reshape_add_multiply_constant_3_let = (&(global_const_workspace_18_var[1376]));
  void* fused_reshape_add_constant_3_let = (&(global_const_workspace_18_var[1392]));
  void* fused_reshape_constant_3_let = (&(global_const_workspace_18_var[1360]));
  for (int32_t ax3 = 0; ax3 < 4; ++ax3) {
    int32_t v_ = ((p0[ax3] + ((int32_t*)fused_reshape_constant_3_let)[ax3]) * ((int32_t*)fused_reshape_add_constant_3_let)[ax3]) >> ((int32_t*)fused_reshape_add_multiply_constant_3_let)[ax3];
    int32_t v__1 = (v_) < (127) ? (v_) : (127);
    T_multiply[ax3] = (((float)((v__1) > (-128) ? (v__1) : (-128))) * 1.562500e-02f);
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_multiply_add_f_afb9046a28628b23_(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_6_var, uint8_t* global_workspace_7_var) {
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_multiply_constant_let = (&(global_const_workspace_6_var[1488]));
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_constant_let = (&(global_const_workspace_6_var[1504]));
  void* fused_reshape_add_multiply_constant_let = (&(global_const_workspace_6_var[1040]));
  void* fused_reshape_add_constant_let = (&(global_const_workspace_6_var[1104]));
  void* fused_reshape_constant_let = (&(global_const_workspace_6_var[976]));
  for (int32_t ax1 = 0; ax1 < 29; ++ax1) {
    int32_t v_ = ((p0[ax1] + ((int32_t*)fused_reshape_constant_let)[ax1]) * ((int32_t*)fused_reshape_add_constant_let)[ax1]) >> ((int32_t*)fused_reshape_add_multiply_constant_let)[ax1];
    int32_t v__1 = (v_) < (255) ? (v_) : (255);
    float v__2 = ((float)((v__1) > (0) ? (v__1) : (0))) * 3.906250e-03f;
    float v__3 = floorf(((((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f)) * ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_constant_let)[0]) + ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_multiply_constant_let)[0]));
    float v__4 = (v__3) < (2.550000e+02f) ? (v__3) : (2.550000e+02f);
    T_cast[ax1] = ((int8_t)(((int32_t)((uint8_t)((v__4) > (0.000000e+00f) ? (v__4) : (0.000000e+00f)))) - 128));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb_(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_10_var, uint8_t* global_workspace_11_var) {
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multiply_constant_let = (&(global_const_workspace_10_var[1440]));
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_constant_let = (&(global_const_workspace_10_var[1472]));
  void* fused_reshape_add_multiply_constant_1_let = (&(global_const_workspace_10_var[1200]));
  void* fused_reshape_add_constant_1_let = (&(global_const_workspace_10_var[1232]));
  void* fused_reshape_constant_1_let = (&(global_const_workspace_10_var[1168]));
  for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float condval;
    if ((ax1 < 12)) {
      int32_t v_ = ((p0[ax1] + ((int32_t*)fused_reshape_constant_1_let)[ax1]) * ((int32_t*)fused_reshape_add_constant_1_let)[ax1]) >> ((int32_t*)fused_reshape_add_multiply_constant_1_let)[ax1];
      int32_t v__1 = (v_) < (255) ? (v_) : (255);
      float v__2 = ((float)((v__1) > (0) ? (v__1) : (0))) * 3.906250e-03f;
      condval = ((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f));
    } else {
      condval = 0.000000e+00f;
    }
    float v__3 = floorf(((condval * ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_constant_let)[0]) + ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multiply_constant_let)[0]));
    float v__4 = (v__3) < (2.550000e+02f) ? (v__3) : (2.550000e+02f);
    T_cast[ax1] = ((int8_t)(((int32_t)((uint8_t)((v__4) > (0.000000e+00f) ? (v__4) : (0.000000e+00f)))) - 128));
  }
  return 0;
}

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb__1(int32_t* p0, int8_t* T_cast, uint8_t* global_const_workspace_14_var, uint8_t* global_workspace_15_var) {
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multiply_constant_1_let = (&(global_const_workspace_14_var[1424]));
  void* fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_constant_1_let = (&(global_const_workspace_14_var[1456]));
  void* fused_reshape_add_multiply_constant_2_let = (&(global_const_workspace_14_var[1312]));
  void* fused_reshape_add_constant_2_let = (&(global_const_workspace_14_var[1328]));
  void* fused_reshape_constant_2_let = (&(global_const_workspace_14_var[1296]));
  for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float condval;
    if ((ax1 < 6)) {
      int32_t v_ = ((p0[ax1] + ((int32_t*)fused_reshape_constant_2_let)[ax1]) * ((int32_t*)fused_reshape_add_constant_2_let)[ax1]) >> ((int32_t*)fused_reshape_add_multiply_constant_2_let)[ax1];
      int32_t v__1 = (v_) < (255) ? (v_) : (255);
      float v__2 = ((float)((v__1) > (0) ? (v__1) : (0))) * 3.906250e-03f;
      condval = ((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f));
    } else {
      condval = 0.000000e+00f;
    }
    float v__3 = floorf(((condval * ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_constant_1_let)[0]) + ((float*)fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multiply_constant_1_let)[0]));
    float v__4 = (v__3) < (2.550000e+02f) ? (v__3) : (2.550000e+02f);
    T_cast[ax1] = ((int8_t)(((int32_t)((uint8_t)((v__4) > (0.000000e+00f) ? (v__4) : (0.000000e+00f)))) - 128));
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
   sid_7_let = (&(global_workspace_1_var[0]));
   sid_5_let = (&(global_workspace_1_var[0]));
   sid_6_let = (&(global_workspace_1_var[16]));
   sid_1_let = (&(global_workspace_1_var[0]));
   sid_4_let = (&(global_workspace_1_var[32]));
   sid_8_let = (&(global_workspace_1_var[0]));
   sid_2_let = (&(global_workspace_1_var[32]));
   sid_3_let = (&(global_workspace_1_var[0]));
  tvmgen_default_fused_multiply_add_floor_clip_cast_reshape(features_buffer_var, sid_1_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_nn_contrib_dense_pack(sid_1_let, sid_2_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_multiply_add_f_afb9046a28628b23_(sid_2_let, sid_3_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_nn_contrib_dense_pack_subtract(sid_3_let, sid_4_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb_(sid_4_let, sid_5_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_nn_contrib_dense_pack_subtract_1(sid_5_let, sid_6_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply_nn_relu_nn_pad_multipl_7ae7be8224ee3ddb__1(sid_6_let, sid_7_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_nn_contrib_dense_pack_subtract_2(sid_7_let, sid_8_let, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_fused_reshape_add_multiply_right_shift_clip_cast_multiply(sid_8_let, output_buffer_var, global_const_workspace_0_var, global_workspace_1_var);
  tvmgen_default_finished = 1;
  break;
default:
  break;
}
}

