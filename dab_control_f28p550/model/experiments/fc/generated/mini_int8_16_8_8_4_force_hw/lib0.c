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
  int8_t fused_constant_let[64] __attribute__((aligned(16))); // 64 bytes, aligned offset: 0
  int8_t fused_constant_1_let[32] __attribute__((packed, aligned(16))); // 32 bytes, aligned offset: 64
  int32_t fused_nn_contrib_dense_pack_subtract_constant_let[8] __attribute__((packed, aligned(16))); // 16 bytes, aligned offset: 96
  int32_t fused_nn_contrib_dense_pack_subtract_add_multiply_constant_let[8] __attribute__((packed, aligned(16))); // 16 bytes, aligned offset: 112
  int32_t fused_nn_contrib_dense_pack_subtract_add_constant_let[8] __attribute__((packed, aligned(16))); // 16 bytes, aligned offset: 128
  int32_t fused_nn_contrib_dense_pack_constant_let[8] __attribute__((packed, aligned(16))); // 16 bytes, aligned offset: 144
  int32_t fused_nn_contrib_dense_pack_subtract_constant_1_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 160
  int32_t fused_nn_contrib_dense_pack_subtract_add_multiply_constant_1_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 176
  int32_t fused_nn_contrib_dense_pack_subtract_add_constant_1_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 192
  int32_t fused_nn_contrib_dense_pack_constant_1_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 208
} const global_const_workspace = {
  .fused_constant_let = {
    -0x63, +0x46, +0x4c, +0x67, +0x5d, -0x73, -0x4c, -0x5a, 
    +0x02, -0x64, -0x04, -0x6e, -0x63, +0x73, +0x01, +0x26, 
    -0x4e, -0x0f, +0x48, +0x6c, -0x24, -0x0d, -0x32, -0x70, 
    +0x3e, +0x60, -0x6c, -0x26, -0x73, +0x27, -0x37, -0x62, 
    +0x6f, +0x2a, +0x58, +0x79, -0x25, +0x0f, +0x2a, -0x13, 
    -0x7d, +0x64, -0x04, +0x52, +0x70, +0x25, +0x1c, +0x2a, 
    +0x28, -0x02, +0x19, +0x27, +0x3e, +0x76, -0x77, +0x3e, 
    -0x4f, +0x30, +0x3d, -0x02, +0x70, +0x3e, -0x47, -0x12
  },
  .fused_constant_1_let = {
    +0x7a, -0x1e, -0x77, +0x3e, +0x67, +0x05, -0x07, +0x42, 
    -0x69, -0x31, +0x24, +0x4f, -0x6d, -0x75, -0x2c, -0x3f, 
    -0x19, -0x2f, +0x0a, -0x02, +0x08, -0x5b, +0x58, -0x3f, 
    -0x76, -0x77, -0x49, -0x31, -0x26, +0x79, -0x1b, -0x48
  },
  .fused_nn_contrib_dense_pack_subtract_constant_let = {
    +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L
  },
  .fused_nn_contrib_dense_pack_subtract_add_multiply_constant_let = {
    +0x00000008L, +0x00000008L, +0x00000008L, +0x00000008L, +0x00000008L, +0x00000008L, +0x00000008L, +0x00000008L
  },
  .fused_nn_contrib_dense_pack_subtract_add_constant_let = {
    +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L
  },
  .fused_nn_contrib_dense_pack_constant_let = {
    +0x00005300L, -0x00007780L, -0x00006700L, -0x00009780L, -0x00002e00L, -0x00008100L, +0x00009600L, +0x00006180L
  },
  .fused_nn_contrib_dense_pack_subtract_constant_1_let = {
    +0x00000100L, +0x00000100L, +0x00000100L, +0x00000100L
  },
  .fused_nn_contrib_dense_pack_subtract_add_multiply_constant_1_let = {
    +0x00000009L, +0x00000009L, +0x00000009L, +0x00000009L
  },
  .fused_nn_contrib_dense_pack_subtract_add_constant_1_let = {
    +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L
  },
  .fused_nn_contrib_dense_pack_constant_1_let = {
    +0x00005100L, +0x0000a380L, +0x00004400L, +0x00001500L
  },
};// of total size 216 bytes
__attribute__((section(".bss.noinit.tvm"), aligned(16)))
static uint8_t global_workspace[TINIE_NPU_EXTRA_BUF_PADDING + 32];
#include "tvmgen_default.h"
TVM_DLL int32_t tvmgen_default___tvm_main__(void* features,void* output0,uint8_t* global_const_workspace_0_var,uint8_t* global_workspace_1_var);
int32_t tvmgen_default_run(struct tvmgen_default_inputs* inputs,struct tvmgen_default_outputs* outputs) {return tvmgen_default___tvm_main__(inputs->features,outputs->output,((uint8_t*)&global_const_workspace),((uint8_t*)&global_workspace));
}
#ifdef __cplusplus
}
#endif
;