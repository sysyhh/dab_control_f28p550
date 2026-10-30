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
0x197cfc55,
0x1faf9f5c,
0x5373a004,
0x105b358e,
0xf0d0d07,
0x6000407,
0x2040908,
0x3020e00,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,

 // 24-bit bias in little-endian:
0xbd1,
0x0,
0xeff,
0x0,
0x609,
0x0,
0x2592,
0x0,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1090108,
0x1080109,
};

static const uint32_t FC_MMR[] = {
0x0,
0x0,
0x0,
0x7f0180,
0x0,
0x4604091,
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
#include "hard/ins_asm/FC_iB8_oB8_kB8_iCm8b16_oCm4_INS.h"

static const uint32_t FC_PARAMS_1[] = {
  // 8-bit weights in little-endian:
0xb0b1a38,
0x25300b06,
0x34161b10,
0x39082212,
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
0xb0f3026,
0x34071706,
0x2538160f,
0xb070226,
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
0x29351b0d,
0x29113e32,
0xb170839,
0xb072d35,
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
0xb160b09,
0x341a2107,
0xb1e0329,
0x253c1301,
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
0xb0b253a,
0x381e3839,
0xb0b0b2e,
0x34071b03,
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
0x3416030f,
0xb160a13,
0x25302407,
0x2534283b,
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
0xb07130c,
0xb0f1235,
0xb0b0b11,
0xb161a02,
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

 // 24-bit bias in little-endian:
0x485,
0x0,
0xefbe,
0xff000000,
0xf6fc,
0xff000000,
0x1d77,
0x0,
0x516,
0x0,
0xf42d,
0xff000000,
0xf08a,
0xff000000,
0x852,
0x0,
0x1c42,
0x0,
0x1a60,
0x0,
0xaa8,
0x0,
0x678,
0x0,
0xaff,
0x0,
0xf7d5,
0xff000000,
0x640,
0x0,
0xefd7,
0xff000000,
0x642,
0x0,
0xd96,
0x0,
0x741,
0x0,
0xf3b7,
0xff000000,
0xf5a1,
0xff000000,
0x7fb,
0x0,
0xf4ff,
0xff000000,
0xf4d4,
0xff000000,
0x3ff,
0x0,
0x4ae,
0x0,
0x6a6,
0x0,
0xb63,
0x0,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1050105,
0x1090104,
0x1050104,
0x1060105,
0x1090109,
0x1050106,
0x1040106,
0x1050104,
0x1080105,
0x1050106,
0x1050104,
0x1060106,
0x1050105,
0x1060106,
};

static const uint32_t FC_MMR_1[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4604019,
0x0,
0x0,
0x6,
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
0x38,
0x0,
0x54,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB8_iCm8b16_oC1LL_INS.h"

static const uint32_t FC_PARAMS_1_sub1[] = {
  // 8-bit weights in little-endian:
0x3508001a,
0x0,
0x0,
0x0,

 // 24-bit bias in little-endian:
0xf317,
0xff000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1050105,
0x1050105,
};

static const uint32_t FC_MMR_1_sub1[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4604019,
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
0x2,
0x0,
0x3,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB8_iCm8b16_oCm4_INS.h"

static const uint32_t FC_PARAMS_2[] = {
  // 8-bit weights in little-endian:
0x3f3f0e20,
0x3c3c1517,
0xd3ddc8b3,
0xfcecf3ec,
0x3c3c2b48,
0x3d2c6049,
0xfeedbb63,
0x3c2b7ce6,
0xc0c040a0,
0xc0cdc0c,
0xff6f4e55,
0xf4f5f3b,
0xfcec9c62,
0xcc700105,
0xbb229b2e,
0xdca8e644,
0xc0c08142,
0xcccc0f1f,
0xc2612039,
0xcc8ccf89,
0xf2f3f72d,
0xf3f7bd80,
0x8045ffc,
0xf3f667df,
0x3030690,
0x4b59,
0xfe92afd8,
0x19519,
0x3030301,
0x3030003,
0x1000200,
0x3030002,
0x130b3ec4,
0x1026,
0xfcfcfad2,
0xffefcbbd,
0xc3faf768,
0x3c3e1e63,
0x3c2d752f,
0xecf2d5b7,
0xf0f0a029,
0xc0,
0xf0fdf8f,
0x3f3f3faa,
0x3cf46bb,
0xf86460a9,
0xc8f0511c,
0x8b9b16c9,
0x382927a,
0xc0c14161,
0xfcfc7efc,
0x8fde2f91,
0xd065d12,
0xf3f7ff63,
0xf3f3fd15,
0xfff5ba57,
0xfffbf90d,
0x33333f73,
0x534d,
0xfff6c80a,
0x1010003,
0x2,
0x3030102,
0x201,
0xff00913b,
0x3370b0c,
0xaff0f0e0,
0xff002703,
0xfb0dad37,
0xc0d0dc87,
0xeb3c2dbe,
0xfb0c1de2,
0xff01dde9,
0xf0f0f025,
0xfe034bc3,
0xff001ab1,
0xff402a77,
0x34b434e,
0xee336368,
0xff008418,
0xff00be03,
0x303c0b7,
0xbec387ca,
0xff00742f,
0xff443254,
0xd080cab,
0xaef374c9,
0xbfc0dee1,
0xff009bcc,
0xfffffa96,
0xee33671d,
0xfe03cf0a,
0x3000002,
0x20100,
0x3000000,
0x3000001,
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
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,
0x0,

 // 24-bit bias in little-endian:
0x58b,
0x0,
0xfaef,
0xff000000,
0xb53b,
0xff000000,
0xfe93,
0xff000000,
0xe2fc,
0xff000000,
0xfe3f,
0xff000000,
0x33c,
0x0,
0xdc21,
0xff000000,
0xfaf7,
0xff000000,
0xf3d5,
0xff000000,
0xf36d,
0xff000000,
0xf6f8,
0xff000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1050103,
0x1050109,
0x1050106,
0x1080104,
0x1050109,
0x1090109,
0x1170117,
0x1170117,
};

static const uint32_t FC_MMR_2[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4604011,
0x0,
0x0,
0x3,
0x2,
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
0x40,
0x0,
0x50,
0x0,
0x0,
0x0,
0x0,
0x0,
};
#include "hard/ins_asm/FC_iB8_oB8_kB8_iCm8b16_oCm4_INS.h"

static const uint32_t FC_PARAMS_3[] = {
  // 8-bit weights in little-endian:
0x393df41e,
0x3c3ab5e4,
0x88cfc2a0,
0xf979b08a,
0x3f165895,
0x3a2f2794,
0xece7a44f,
0x2c0e2b51,
0x4084534,
0x40896,
0xf3f7f70c,
0xae04,
0x0,
0x0,
0x0,
0x0,
0xf8bf6f2b,
0xfdb4bdcb,
0x0,
0x0,
0x2e3e131e,
0x4131e4a,
0x0,
0x0,
0xc0c59fb,
0xc0c9630,
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
0x0,
0x0,

 // 24-bit bias in little-endian:
0xe935,
0xff000000,
0xea38,
0xff000000,
0xc377,
0xff000000,
0xef57,
0xff000000,
0xf7eb,
0xff000000,
0xf882,
0xff000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,
0x0,
0x40000000,

 // (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:
0x1050106,
0x1060106,
0x1060106,
0x1170117,
0x1170117,
0x1170117,
0x1170117,
0x1170117,
};

static const uint32_t FC_MMR_3[] = {
0x0,
0x0,
0x0,
0xff0000,
0x0,
0x4604011,
0x0,
0x0,
0x3,
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
0x20,
0x0,
0x30,
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
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_12_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_7_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_11_var);
#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_12_var) {
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_3_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_1)/sizeof(FC_MMR_1[0]),
      sizeof(FC_PARAMS_1)/sizeof(FC_PARAMS_1[0]),
      sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS)/sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS[0]),
      FC_MMR_1,
      FC_PARAMS_1,
      FC_iB8_oB8_kB8_iCm8b16_oCm4_INS,
      inputData,
      NULL,
      outputData,
    };
  }
  {
    tinie_sublayers_data[1] = (TINIE_layer_t) {
      sizeof(FC_MMR_1_sub1)/sizeof(FC_MMR_1_sub1[0]),
      sizeof(FC_PARAMS_1_sub1)/sizeof(FC_PARAMS_1_sub1[0]),
      sizeof(FC_iB8_oB8_kB8_iCm8b16_oC1LL_INS)/sizeof(FC_iB8_oB8_kB8_iCm8b16_oC1LL_INS[0]),
      FC_MMR_1_sub1,
      FC_PARAMS_1_sub1,
      FC_iB8_oB8_kB8_iCm8b16_oC1LL_INS,
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_7_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_2)/sizeof(FC_MMR_2[0]),
      sizeof(FC_PARAMS_2)/sizeof(FC_PARAMS_2[0]),
      sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS)/sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS[0]),
      FC_MMR_2,
      FC_PARAMS_2,
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

#ifdef __cplusplus
extern "C"
#endif
TVM_DLL int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int8_t* __restrict__ inputData, int8_t* __restrict__ outputData, uint8_t* __restrict__ global_workspace_11_var) {
  {
    tinie_sublayers_data[0] = (TINIE_layer_t) {
      sizeof(FC_MMR_3)/sizeof(FC_MMR_3[0]),
      sizeof(FC_PARAMS_3)/sizeof(FC_PARAMS_3[0]),
      sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS)/sizeof(FC_iB8_oB8_kB8_iCm8b16_oCm4_INS[0]),
      FC_MMR_3,
      FC_PARAMS_3,
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

