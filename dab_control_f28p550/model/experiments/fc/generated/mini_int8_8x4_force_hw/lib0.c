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
  int8_t fused_constant_let[32] __attribute__((aligned(16))); // 32 bytes, aligned offset: 0
  int32_t fused_nn_contrib_dense_pack_constant_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 32
  int32_t fused_nn_contrib_dense_pack_add_multiply_constant_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 48
  int32_t fused_nn_contrib_dense_pack_add_constant_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 64
} const global_const_workspace = {
  .fused_constant_let = {
    +0x63, +0x1a, +0x40, -0x0f, +0x78, -0x1e, -0x1c, -0x0c, 
    -0x67, +0x34, -0x05, -0x40, +0x31, +0x05, -0x3e, -0x3d, 
    -0x11, -0x5e, +0x0e, +0x29, +0x35, -0x74, -0x2a, +0x2e, 
    +0x37, +0x66, +0x17, +0x16, -0x5a, -0x0a, -0x33, -0x12
  },
  .fused_nn_contrib_dense_pack_constant_let = {
    +0x00000080L, +0x00000080L, +0x00000040L, +0x00000040L
  },
  .fused_nn_contrib_dense_pack_add_multiply_constant_let = {
    +0x00000008L, +0x00000008L, +0x00000007L, +0x00000007L
  },
  .fused_nn_contrib_dense_pack_add_constant_let = {
    +0x00000001L, +0x00000001L, +0x00000001L, +0x00000001L
  },
};// of total size 72 bytes
__attribute__((section(".bss.noinit.tvm"), aligned(16)))
static uint8_t global_workspace[TINIE_NPU_EXTRA_BUF_PADDING + 24];
#include "tvmgen_default.h"
TVM_DLL int32_t tvmgen_default___tvm_main__(void* features,void* output0,uint8_t* global_const_workspace_0_var,uint8_t* global_workspace_1_var);
int32_t tvmgen_default_run(struct tvmgen_default_inputs* inputs,struct tvmgen_default_outputs* outputs) {return tvmgen_default___tvm_main__(inputs->features,outputs->output,((uint8_t*)&global_const_workspace),((uint8_t*)&global_workspace));
}
#ifdef __cplusplus
}
#endif
;