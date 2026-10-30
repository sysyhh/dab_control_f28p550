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
#include "tvm/runtime/contrib/tvm_tinie_c28.h"
#define TINIE_NPU_EXTRA_BUF_PADDING 32
#include "tvm/runtime/c_runtime_api.h"
#ifdef __cplusplus
extern "C" {
#endif
__attribute__((section(".rodata.tvm"), ))
static const struct global_const_workspace {
  float fused_reshape_multiply_constant_let[1] __attribute__((aligned(16))); // 2 bytes, aligned offset: 0
  float fused_reshape_constant_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 16
  float fused_cast_cast_multiply_nn_relu_multiply_constant_2_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 32
  float fused_cast_cast_multiply_nn_relu_multiply_constant_1_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 48
  float fused_cast_cast_multiply_nn_relu_multiply_constant_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 64
  float fused_cast_cast_multiply_nn_relu_constant_2_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 80
  float fused_cast_cast_multiply_nn_relu_constant_1_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 96
  float fused_cast_cast_multiply_nn_relu_constant_let[1] __attribute__((packed, aligned(16))); // 2 bytes, aligned offset: 112
} const global_const_workspace = {
  .fused_reshape_multiply_constant_let = {
    0x1.0000000000000p-1
  },
  .fused_reshape_constant_let = {
    0x1.0000000000000p+6
  },
  .fused_cast_cast_multiply_nn_relu_multiply_constant_2_let = {
    0x1.0000000000000p-1
  },
  .fused_cast_cast_multiply_nn_relu_multiply_constant_1_let = {
    0x1.0000000000000p-1
  },
  .fused_cast_cast_multiply_nn_relu_multiply_constant_let = {
    0x1.0000000000000p-1
  },
  .fused_cast_cast_multiply_nn_relu_constant_2_let = {
    0x1.0000000000000p+8
  },
  .fused_cast_cast_multiply_nn_relu_constant_1_let = {
    0x1.0000000000000p+7
  },
  .fused_cast_cast_multiply_nn_relu_constant_let = {
    0x1.0000000000000p+6
  },
};// of total size 114 bytes
__attribute__((section(".bss.noinit.tvm"), aligned(16)))
static uint8_t global_workspace[TINIE_NPU_EXTRA_BUF_PADDING + 64];
#include "tvmgen_default.h"
TVM_DLL int32_t tvmgen_default___tvm_main__(void* features,void* output0,uint8_t* global_const_workspace_0_var,uint8_t* global_workspace_1_var);
int32_t tvmgen_default_run(struct tvmgen_default_inputs* inputs,struct tvmgen_default_outputs* outputs) {return tvmgen_default___tvm_main__(inputs->features,outputs->output,((uint8_t*)&global_const_workspace),((uint8_t*)&global_workspace));
}
#ifdef __cplusplus
}
#endif
;