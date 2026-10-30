#pragma DATA_SECTION(FC_PARAMS, ".dab_npu_const")
#pragma DATA_SECTION(FC_MMR, ".dab_npu_const")
#pragma DATA_SECTION(FC_PARAMS_1, ".dab_npu_const")
#pragma DATA_SECTION(FC_MMR_1, ".dab_npu_const")
#pragma DATA_SECTION(FC_PARAMS_2, ".dab_npu_const")
#pragma DATA_SECTION(FC_MMR_2, ".dab_npu_const")
#pragma DATA_SECTION(FC_PARAMS_3, ".dab_npu_const")
#pragma DATA_SECTION(FC_MMR_3, ".dab_npu_const")
#pragma DATA_SECTION(FC_PARAMS_3_sub1, ".dab_npu_const")
#pragma DATA_SECTION(FC_MMR_3_sub1, ".dab_npu_const")
#pragma DATA_SECTION(FC_iB8_oB8_kB4_iCm8_oC2L_INS, ".dab_npu_const")
#pragma DATA_SECTION(FC_iB8_oB8_kB4_iCm8_oCm4_INS, ".dab_npu_const")
#pragma CODE_SECTION(tvmgen_default_ti_npu_fullyConnectedNHWC_1, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_fullyConnectedNHWC_3, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_fullyConnectedNHWC_2, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_fullyConnectedNHWC_0, ".dab_npu_ramfunc")
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
      

#include "hard/ins_asm/FC_iB8_oB8_kB4_iCm8_oCm4_INS.h"

static const uint32_t FC_PARAMS[] = {
  // 4-bit weights in little-endian:
0x3c3d3333,
0x3c3d131d,
0x3d5f3c3d,
0x3c3f3232,
0x40c0c0,
0x40f060,
0x98d5f0d0,
0xdcf9bb67,
0xc082c0c1,
0xc0c1c272,
0xc3cf0205,
0xc3cb0809,
0x450303,
0x41fee7,
0x3030000,
0x3030100,
0x131f,
0x30200001,
0x3033130f,
0x2c333c3d,
0xc0c0,
0x40,
0xf8744400,
0x8b67c8f4,
0xc0c103c2,
0x83a3c0c0,
0x80d0b,
0xcfc50307,
0x40f0f,
0x3f360001,
0x102,
0x10303,
0x101caaaa,
0xaa6baaaa,
0x24abb4,
0xaaa6aaeb,
0xabec,
0xaaaaaaee,
0x480aaea,
0xaa99aaee,
0x343aabf,
0xaabaaaae,
0xd0baafe,
0xaa6eaaad,
0xf0faaef,
0xaaddaaee,
0x1000202,
0x2010202,

 // 16-bit bias in little-endian:
0x122,
0xfeec,
0xf770,
0xffcf,
0xfc1b,
0xffc7,
0x5b,
0xfab6,
0xfeec,
0xfd81,
0xfdc3,
0xfe1c,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0xd60adf08,
0xac09c70d,
0xb709a90a,
0x9b0ccf08,
0xde0ae00e,
0xe10e830d,
};

static const uint32_t FC_MMR[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4603011,
0x0,
0x0,
0x2,
0x3,
0x0,
0x0,
0x8,
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
0x18,
0x0,
0x1e,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB4_iCm8_oCm4_INS.h"

static const uint32_t FC_PARAMS_1[] = {
  // 4-bit weights in little-endian:
0x10a01db0,
0x117c5373,
0x6010302,
0x3060205,

 // 16-bit bias in little-endian:
0xe5,
0x120,
0x70,
0x3ef,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0xae0cae0b,
0x800bad0c,
};

static const uint32_t FC_MMR_1[] = {
0x0,
0x0,
0x0,
0x7f0180,
0x0,
0x4603091,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x8,
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
0x2,
0x0,
0x4,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB4_iCm8_oCm4_INS.h"

static const uint32_t FC_PARAMS_2[] = {
  // 4-bit weights in little-endian:
0xc4b094e,
0xc98989c8,
0x3a263f16,
0x2013edd4,
0x8040c,
0x40008,
0x0,
0x0,
0xcd86c989,
0x0,
0x52d2e2d,
0x0,
0xc5d0c5d,
0x0,
0x0,
0x0,

 // 16-bit bias in little-endian:
0xfdbd,
0xfd18,
0xf91a,
0xfe97,
0xff01,
0xff0a,
0x7fff,
0x7fff,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0xa609df0a,
0x8309c20a,
0xad0ab40a,
0xf71ff71f,
};

static const uint32_t FC_MMR_2[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4603011,
0x0,
0x0,
0x1,
0x1,
0x0,
0x0,
0x8,
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
#include "hard/ins_asm/FC_iB8_oB8_kB4_iCm8_oCm4_INS.h"

static const uint32_t FC_PARAMS_3[] = {
  // 4-bit weights in little-endian:
0x251b0b17,
0x3905341f,
0x0,
0x0,
0x253d0b17,
0x804253d,
0x0,
0x0,
0x29252936,
0xb170b17,
0x0,
0x0,
0x341f0b17,
0x253d0b26,
0x0,
0x0,
0x38170b17,
0x253d0804,
0x0,
0x0,
0xb17350c,
0x253d251e,
0x0,
0x0,
0xb170804,
0xb170804,
0x0,
0x0,

 // 16-bit bias in little-endian:
0xb9,
0xfd27,
0xfe93,
0x433,
0xe4,
0xfe0b,
0xfde6,
0x109,
0x3d5,
0x31e,
0x174,
0xe8,
0x17e,
0xfed3,
0x11e,
0xfdfb,
0xf6,
0x2a6,
0x130,
0xfe0a,
0xfe41,
0x110,
0xfddb,
0xfe45,
0x81,
0xd1,
0x10c,
0x183,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0xb209c109,
0xd70dc508,
0xbd09b108,
0xf80ae509,
0x810ce10d,
0xdd09e20a,
0xd808e40a,
0xf909ae08,
0x9d0cc909,
0xc309bd0a,
0xe909b908,
0xc90aa10a,
0xb009f409,
0xe90ac40a,
};

static const uint32_t FC_MMR_3[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4603019,
0x0,
0x0,
0x6,
0x0,
0x0,
0x0,
0x8,
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
0xe,
0x0,
0x1c,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB4_iCm8_oC2L_INS.h"

static const uint32_t FC_PARAMS_3_sub1[] = {
  // 4-bit weights in little-endian:
0x253d,
0x0,

 // 16-bit bias in little-endian:
0xfe29,
0x0,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0xdb09db09,
0xdb09db09,
};

static const uint32_t FC_MMR_3_sub1[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4603019,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x8,
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
0x7,
0x1,
0x0,
0x2,
0x0,
0x0,
0x0,
0x0,
0x0,
};
extern TINIE_layer_t* tinie_sublayers;
static TINIE_layer_t __attribute__((aligned(4))) tinie_sublayers_data[2];

static uint8_t __attribute__((section(".bss.noinit.tvm"), aligned(4))) tvm_tensors[1];


#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_7_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_15_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_11_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_7_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR)/sizeof(FC_MMR[0]),
      sizeof(FC_PARAMS)/sizeof(FC_PARAMS[0]),
      sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS)/sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS[0]),
      FC_MMR,
      FC_PARAMS,
      FC_iB8_oB8_kB4_iCm8_oCm4_INS,
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_15_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_1)/sizeof(FC_MMR_1[0]),
      sizeof(FC_PARAMS_1)/sizeof(FC_PARAMS_1[0]),
      sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS)/sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS[0]),
      FC_MMR_1,
      FC_PARAMS_1,
      FC_iB8_oB8_kB4_iCm8_oCm4_INS,
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_11_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_2)/sizeof(FC_MMR_2[0]),
      sizeof(FC_PARAMS_2)/sizeof(FC_PARAMS_2[0]),
      sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS)/sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS[0]),
      FC_MMR_2,
      FC_PARAMS_2,
      FC_iB8_oB8_kB4_iCm8_oCm4_INS,
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_3)/sizeof(FC_MMR_3[0]),
      sizeof(FC_PARAMS_3)/sizeof(FC_PARAMS_3[0]),
      sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS)/sizeof(FC_iB8_oB8_kB4_iCm8_oCm4_INS[0]),
      FC_MMR_3,
      FC_PARAMS_3,
      FC_iB8_oB8_kB4_iCm8_oCm4_INS,
      inputData,
      NULL,
      outputData,
    };
  }
  {
    tinie_sublayers_data[1] = (TINIE_layer_t) {
      sizeof(FC_MMR_3_sub1)/sizeof(FC_MMR_3_sub1[0]),
      sizeof(FC_PARAMS_3_sub1)/sizeof(FC_PARAMS_3_sub1[0]),
      sizeof(FC_iB8_oB8_kB4_iCm8_oC2L_INS)/sizeof(FC_iB8_oB8_kB4_iCm8_oC2L_INS[0]),
      FC_MMR_3_sub1,
      FC_PARAMS_3_sub1,
      FC_iB8_oB8_kB4_iCm8_oC2L_INS,
      inputData,
      NULL,
      outputData,
    };
  }
  tinie_sublayers = &tinie_sublayers_data[0];
  tinie_num_sublayers = 2;
  tinie_curr_sublayer = 0;
  tinie_curr_layer += 1;
  tinie_sublayer_IRQHandler();
  return 0;
}

