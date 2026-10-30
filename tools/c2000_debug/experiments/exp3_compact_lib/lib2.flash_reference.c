#pragma CODE_SECTION(tvmgen_default_ti_npu_convolve1x1NHWC_1, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_convolve1x1NHWC_3, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_convolve1x1NHWC_2, ".dab_npu_ramfunc")
#pragma CODE_SECTION(tvmgen_default_ti_npu_convolve1x1NHWC_0, ".dab_npu_ramfunc")
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
      

#include "hard/ins_asm/PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS.h"

static const uint32_t PWCONV_PARAMS[] = {
  // 8-bit weights in little-endian:
0x3f1e2607,
0x3c281b37,
0xc3faf4e9,
0xfce9ccd3,
0x3c296f66,
0x3d0bf3d3,
0xfffc9849,
0x3d680231,
0xcc8c5cbc,
0xf4fbf0b,
0xffaf4f19,
0xf4fffbb,
0xfc8cf98f,
0x988c6b0f,
0xbff64736,
0xdcb9582a,
0xc08180f2,
0xcc4edd8b,
0xc272e067,
0xcc8d0ec4,
0xf2f6669a,
0xf7f3119d,
0x80c516c,
0xf3fb184b,
0x3025ecc,
0x5df82,
0xff94e018,
0x422db1,
0x3030200,
0x3020102,
0x20302,
0x3020203,
0x173335d0,
0x2016,
0xfcfce3ff,
0xffdfdba4,
0xd7e28043,
0x3c3f09ae,
0x3c2e80b3,
0xe8dbf819,
0xf0f0500a,
0x4000,
0xf4f6faf,
0x3f3f3fca,
0x430bdd41,
0xf82ce035,
0xc8b4f6de,
0x8f13d086,
0x4311115a,
0xc0c21062,
0xfcfc3f6b,
0x9f4e482e,
0xd0062c6,
0xf0f8f80c,
0xf3f7aa70,
0xfff27680,
0xfff66786,
0x3337375a,
0x1a6dc,
0xfbed8d20,
0x1030101,
0x3,
0x3030001,
0x203,
0xff4096ba,
0x133f2d6b,
0xff409a0a,
0xff4114e9,
0xbb8dfbd8,
0xc0e8b1ba,
0xbf81d0cd,
0xbb8c5a73,
0xef76445e,
0xf0f060da,
0xef75059e,
0xef3542c4,
0xfe5b65f6,
0x38bca9c,
0xfe5a1683,
0xfe1ad189,
0xef248148,
0x3910287,
0xee1713e8,
0xee234e25,
0xff422d47,
0xd045276,
0xaff2f48c,
0xaff2f56f,
0xabecbe8a,
0xfffb982e,
0xabec5cfc,
0xaaef9e4d,
0x3000202,
0x1000302,
0x3000301,
0x3000200,

 // 24-bit bias in little-endian:
0xab5,
0x0,
0xf887,
0xff000000,
0xdbcf,
0xff000000,
0xfe78,
0xff000000,
0xe064,
0xff000000,
0xfe53,
0xff000000,
0x3af,
0x0,
0xde75,
0xff000000,
0xfcf2,
0xff000000,
0xebc2,
0xff000000,
0xf8c5,
0xff000000,
0xfa16,
0xff000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1060105,
0x1060109,
0x1050106,
0x1090105,
0x1060109,
0x1090109,
};

static const uint32_t PWCONV_MMR[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4304011,
0x0,
0x0,
0x2,
0x7,
0x0,
0x0,
0x8,
0x0,
0x0,
0x8,
0x3,
0x0,
0x0,
0x3,
0x0,
0x0,
0x0,
0x0,
0x0,
0x30,
0x30,
0x3c,
0x3c,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS.h"

static const uint32_t PWCONV_PARAMS_1[] = {
  // 8-bit weights in little-endian:
0x19acc67e,
0xf6fefce,
0x43334103,
0x104beb0a,
0xf0d090e,
0x30c000c,
0x304000c,
0x306010b,

 // 24-bit bias in little-endian:
0xbd1,
0x0,
0x77f,
0x0,
0x305,
0x0,
0x2592,
0x0,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1080108,
0x1080108,
};

static const uint32_t PWCONV_MMR_1[] = {
0x0,
0x0,
0x0,
0x7f0180,
0x0,
0x4304091,
0x0,
0x0,
0x0,
0x1,
0x0,
0x0,
0x8,
0x0,
0x0,
0x2,
0x1,
0x0,
0x0,
0x1,
0x0,
0x0,
0x0,
0x0,
0x0,
0x4,
0x4,
0x8,
0x8,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS.h"

static const uint32_t PWCONV_PARAMS_2[] = {
  // 8-bit weights in little-endian:
0x3d34b696,
0x3d743dce,
0x89cc4e62,
0xfcb7b59f,
0x3f1b7d78,
0x3b1c25fe,
0xecd977d6,
0x2c3c3f05,
0xc04a7,
0x408ae,
0xf3f7f344,
0x5504,
0xfdb464e4,
0xfdba61a1,
0x0,
0x0,
0x3f0d0b04,
0x1e2950,
0x0,
0x0,
0xc0c5d65,
0xc0ca608,
0x0,
0x0,

 // 24-bit bias in little-endian:
0xf61e,
0xff000000,
0xebe1,
0xff000000,
0xd9a3,
0xff000000,
0xfaa0,
0xff000000,
0xfc14,
0xff000000,
0xfaeb,
0xff000000,
0x0,
0x20000000,
0x0,
0x20000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1050105,
0x1050105,
0x1060105,
0x1160116,
};

static const uint32_t PWCONV_MMR_2[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4304011,
0x0,
0x0,
0x1,
0x2,
0x0,
0x0,
0x8,
0x0,
0x0,
0x3,
0x2,
0x0,
0x0,
0x2,
0x0,
0x0,
0x0,
0x0,
0x0,
0xc,
0xc,
0x14,
0x14,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS.h"

static const uint32_t PWCONV_PARAMS_3[] = {
  // 8-bit weights in little-endian:
0x8080800,
0x400080c,
0x404000c,
0x80c0c04,
0x8080808,
0x4000c08,
0x408040c,
0x80c0408,
0x80c0c00,
0x80c0c00,
0x80c0800,
0x8040404,
0x80c0804,
0x4040c04,
0x804000c,
0x40c0c00,
0x80c0400,
0x80c000c,
0x8080800,
0x4040408,
0x4040804,
0x8080400,
0x40c0800,
0x4040408,
0x8040c00,
0x800040c,
0x8000408,
0x80c0404,
0x4080c00,
0x0,
0x0,
0x0,

 // 24-bit bias in little-endian:
0xbd40,
0xff000000,
0x9fdf,
0xff000000,
0x2fe,
0x0,
0xf2e1,
0xff000000,
0xcd10,
0xff000000,
0xde8b,
0xff000000,
0xcd4b,
0xff000000,
0xce08,
0xff000000,
0xdbef,
0xff000000,
0xcd82,
0xff000000,
0xe4fe,
0xff000000,
0xb9b3,
0xff000000,
0xe789,
0xff000000,
0x155a,
0x0,
0xd07d,
0xff000000,
0xcc8a,
0xff000000,
0xd06c,
0xff000000,
0xd422,
0xff000000,
0xc8f8,
0xff000000,
0xdcf1,
0xff000000,
0xef82,
0xff000000,
0xd01b,
0xff000000,
0x9d09,
0xff000000,
0xe0c7,
0xff000000,
0xa5c5,
0xff000000,
0xa921,
0xff000000,
0xabe3,
0xff000000,
0xe8c0,
0xff000000,
0xde3f,
0xff000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1080108,
0x10b0107,
0x1080107,
0x1090108,
0x10b010b,
0x1080109,
0x1060109,
0x1080107,
0x10b0108,
0x108010a,
0x1080106,
0x109010a,
0x1090108,
0x109010a,
0x1170108,
0x1170117,
};

static const uint32_t PWCONV_MMR_3[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4304019,
0x0,
0x0,
0x7,
0x0,
0x0,
0x0,
0x8,
0x0,
0x0,
0x1,
0x8,
0x0,
0x0,
0x8,
0x0,
0x0,
0x0,
0x0,
0x0,
0x10,
0x10,
0x30,
0x30,
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
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_14_var, uint8_t* __restrict__ global_workspace_15_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_30_var, uint8_t* __restrict__ global_workspace_31_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_22_var, uint8_t* __restrict__ global_workspace_23_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_6_var, uint8_t* __restrict__ global_workspace_7_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_14_var, uint8_t* __restrict__ global_workspace_15_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(PWCONV_MMR)/sizeof(PWCONV_MMR[0]),
      sizeof(PWCONV_PARAMS)/sizeof(PWCONV_PARAMS[0]),
      sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS)/sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS[0]),
      PWCONV_MMR,
      PWCONV_PARAMS,
      PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS,
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
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_30_var, uint8_t* __restrict__ global_workspace_31_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(PWCONV_MMR_1)/sizeof(PWCONV_MMR_1[0]),
      sizeof(PWCONV_PARAMS_1)/sizeof(PWCONV_PARAMS_1[0]),
      sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS)/sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS[0]),
      PWCONV_MMR_1,
      PWCONV_PARAMS_1,
      PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS,
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
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_22_var, uint8_t* __restrict__ global_workspace_23_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(PWCONV_MMR_2)/sizeof(PWCONV_MMR_2[0]),
      sizeof(PWCONV_PARAMS_2)/sizeof(PWCONV_PARAMS_2[0]),
      sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS)/sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS[0]),
      PWCONV_MMR_2,
      PWCONV_PARAMS_2,
      PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS,
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
TVM_DLL int32_t tvmgen_default_ti_npu_convolve1x1NHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_const_workspace_6_var, uint8_t* __restrict__ global_workspace_7_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(PWCONV_MMR_3)/sizeof(PWCONV_MMR_3[0]),
      sizeof(PWCONV_PARAMS_3)/sizeof(PWCONV_PARAMS_3[0]),
      sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS)/sizeof(PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS[0]),
      PWCONV_MMR_3,
      PWCONV_PARAMS_3,
      PWCONV_iB8_oB8_kB8_iHiW1_iCm4_oCm4_INS,
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

