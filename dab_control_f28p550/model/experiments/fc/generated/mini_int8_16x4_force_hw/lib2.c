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
// tvm target: ti-npu 
#include "tvm/runtime/contrib/tvm_tinie_c28.h"
#define TVM_EXPORTS
#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/c_backend_api.h"
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "soft/inc/tinie_soft.h"
#include "hard/inc/tinie.h"
extern volatile int32_t tinie_curr_layer;
extern volatile int32_t tinie_curr_sublayer;
extern volatile int32_t tinie_num_sublayers;
extern void (*tinie_sublayer_postproc)(void);
extern void tinie_sublayer_IRQHandler();
      

#include "hard/ins_asm/FC_iB8_oB8_kB8_iCm8b16_oCm4_INS.h"

static const uint32_t FC_PARAMS[] = {
  // 8-bit weights in little-endian:
0x711a9ede,
0x71d3a0b2,
0x66070b6d,
0x1a3fe1d9,
0x7b9b6c4,
0x17c9953d,
0x339a22ce,
0x67b3d7b7,
0x2ec1372c,
0xe5f826c6,
0x8026278c,
0x381c9b68,
0xfa03fe7a,
0x4fbed9a7,
0x6cbf31bd,
0x30018ed4,

 // 24-bit bias in little-endian:
0x80,
0x0,
0x80,
0x0,
0x80,
0x0,
0x80,
0x0,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1080108,
0x1080108,
};

static const uint32_t FC_MMR[] = {
0x0,
0x0,
0x0,
0x7f0180,
0x0,
0x4604099,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x10,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x8,
0x0,
0xc,
0x0,
0x0,
0x0,
0x0,
0x0,
};
extern TINIE_layer_t* tinie_sublayers;
static TINIE_layer_t __attribute__((aligned(4))) tinie_sublayers_data[1];

static uint8_t __attribute__((section(".bss.noinit.tvm"), aligned(4))) tvm_tensors[1];


#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR)/sizeof(FC_MMR[0]),
      sizeof(FC_PARAMS)/sizeof(FC_PARAMS[0]),
      sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS)/sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS[0]),
      FC_MMR,
      FC_PARAMS,
      FC_iB8_oB8_kB8_iCm8b16_oCm4_INS,
      inputData,
      NULL,
      outputData,
    };
  }
  tinie_sublayers = &tinie_sublayers_data[0];
  tinie_num_sublayers = 1;
  tinie_curr_sublayer = 0;
  tinie_curr_layer += 1;
  tinie_sublayer_IRQHandler();
  return 0;
}

