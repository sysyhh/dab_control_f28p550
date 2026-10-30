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
      

extern TINIE_layer_t* tinie_sublayers;
static TINIE_layer_t __attribute__((aligned(4))) tinie_sublayers_data[1];

static uint8_t __attribute__((section(".bss.noinit.tvm"), aligned(4))) tvm_tensors[1];


static const TINIE_Dims TINIE_DIMS_0 = { .n=1, .h=1, .w=1, .c=16 };

static const TINIE_Dims TINIE_DIMS_1 = { .n=4, .h=1, .w=1, .c=16 };

static const TINIE_Dims TINIE_DIMS_2 = { .n=1, .h=1, .w=1, .c=4 };

static const TINIE_FcParams TINIE_FC_PARAMS_0 = { { -128, 127 } };


static const TINIE_LayerParams TINIE_LAYER_PARAMS_0 = { .inputSign=1, .residualSign=1, .outputSign=1, .softTinieCodegen=0, .weightBitWidth=8,  };

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_0(int8_t* __restrict__ inputData, int8_t* __restrict__ filter, int32_t* __restrict__ biasData, int8_t* __restrict__ multiplier, int8_t* __restrict__ shift, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_4_var, uint8_t* __restrict__ global_workspace_5_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnected_0(int8_t* __restrict__ inputData, int8_t* __restrict__ filter, int32_t* __restrict__ biasData, int8_t* __restrict__ multiplier, int8_t* __restrict__ shift, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_4_var, uint8_t* __restrict__ global_workspace_5_var) {
  const TINIE_PerChannelQuantParams quantParams = { (uint8_t*)multiplier, (uint8_t*)shift };
  TINIE_Status status = TINIE_fullyConnected(&TINIE_FC_PARAMS_0, &quantParams, &TINIE_DIMS_0, inputData, &TINIE_LAYER_PARAMS_0, &TINIE_DIMS_1, filter, biasData, &TINIE_DIMS_2, outputData);
  if (status != TINIE_SUCCESS) {
    return -1;
  }
  return 0;
}

