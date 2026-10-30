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
  int8_t constant_0_let[64] __attribute__((aligned(16))); // 64 bytes, aligned offset: 0
  int32_t constant_1_let[4] __attribute__((packed, aligned(16))); // 8 bytes, aligned offset: 64
  uint8_t constant_3_let[4] __attribute__((packed, aligned(16))); // 4 bytes, aligned offset: 80
  uint8_t constant_2_let[4] __attribute__((packed, aligned(16))); // 4 bytes, aligned offset: 96
} const global_const_workspace = {
  .constant_0_let = {
    +0x6a, +0x2f, -0x2b, +0x4b, -0x28, +0x65, +0x3c, +0x2b, 
    -0x64, -0x39, -0x72, +0x30, -0x46, -0x72, -0x31, -0x33, 
    +0x72, +0x00, -0x25, +0x7a, -0x2b, +0x67, +0x47, +0x38, 
    +0x4a, +0x65, -0x48, -0x0d, -0x19, -0x07, +0x36, +0x6e, 
    -0x43, +0x5b, -0x7e, +0x41, -0x16, +0x23, -0x28, +0x23, 
    +0x2c, +0x17, +0x28, -0x7e, +0x35, -0x0d, -0x41, +0x62, 
    -0x4b, -0x4e, +0x79, +0x0f, -0x01, +0x45, -0x49, +0x6e, 
    +0x0c, -0x46, -0x2a, +0x09, +0x18, +0x0d, -0x3f, +0x0b
  },
  .constant_1_let = {
    +0x00000080L, +0x00000080L, +0x00000080L, +0x00000080L
  },
  .constant_3_let = {
    0x08, 0x08, 0x08, 0x08
  },
  .constant_2_let = {
    0x01, 0x01, 0x01, 0x01
  },
};// of total size 100 bytes
__attribute__((section(".bss.noinit.tvm"), aligned(16)))
static uint8_t global_workspace[TINIE_NPU_EXTRA_BUF_PADDING + 20];
#include "tvmgen_default.h"
TVM_DLL int32_t tvmgen_default___tvm_main__(void* features,void* output0,uint8_t* global_const_workspace_0_var,uint8_t* global_workspace_1_var);
int32_t tvmgen_default_run(struct tvmgen_default_inputs* inputs,struct tvmgen_default_outputs* outputs) {return tvmgen_default___tvm_main__(inputs->features,outputs->output,((uint8_t*)&global_const_workspace),((uint8_t*)&global_workspace));
}
#ifdef __cplusplus
}
#endif
;