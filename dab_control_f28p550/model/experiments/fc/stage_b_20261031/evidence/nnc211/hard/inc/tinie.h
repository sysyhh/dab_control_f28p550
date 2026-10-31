/******************************************************************************
Copyright (c) 1990-2024 Texas Instruments Incorporated

All rights reserved not granted herein.

Limited License.

Texas Instruments Incorporated grants a world-wide, royalty-free, non-exclusive
license under copyrights and patents it now or hereafter owns or controls to
make, have made, use, import, offer
to sell and sell ("Utilize") this software subject to the terms herein. With
respect to the foregoing patent license, such license is granted solely to the
extent that any such patent is necessary to Utilize the software alone. The
patent license shall not apply to any combinations
which include this software, other than combinations with devices manufactured
by or for TI ("TI Devices"). No hardware patent is licensed hereunder.

Redistributions must preserve existing copyright notices and reproduce this
license (including the above copyright notice and the disclaimer and
(if applicable) source code license limitations below)
in the documentation and/or other materials provided with the distribution.

Redistribution and use in binary form, without modification, are permitted
provided that the following conditions are met:

* No reverse engineering, decompilation, or disassembly of this software is
permitted with respect to any software provided in binary form.

* Any redistribution and use are licensed by TI for use only with TI Devices.

* Nothing shall obligate TI to provide you with source code for the software
licensed and provided to you in object code.

If software source code is provided to you, modification and redistribution of
the source code are permitted provided that the following conditions are met:

* Any redistribution and use of the source code, including any resulting
derivative works, are licensed by TI for use only with TI Devices.

* Any redistribution and use of any object code compiled from the source code
and any resulting derivative works, are licensed by TI for use only with TI
Devices.

Neither the name of Texas Instruments Incorporated nor the names of its
suppliers may be used to endorse or promote products derived from this software
without specific prior written permission.

DISCLAIMER.

THIS SOFTWARE IS PROVIDED BY TI AND TI"S LICENSORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL TI AND TI"S LICENSORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
******************************************************************************/

#ifndef _TINIE_HARD_H_
#define _TINIE_HARD_H_

#include <stdio.h>
#include <stdint.h>


#define TINIE_CTL5_INDEX    (0)
#define TINIE_CTL2_INDEX    (3)
#define TINIE_CTL1_INDEX    (4)
#define TINIE_CTL0_INDEX    (5)
#define TINIE_MMR0_INDEX    (29)
#define TINIE_MMR1_INDEX    (30)
#define TINIE_MMR2_INDEX    (31)
#define TINIE_MMR3_INDEX    (32)
#define TINIE_TOTAL_MMRS    (33)


#ifdef __TMS320C2000__
  /* Header file from C2000Ware SDK */
  #include "driverlib.h"  /* containing: typedef  int16_t  int8_t;  typedef uint16_t uint8_t; */
  #define TINIE_BASE_ADDR           EXTEVT_BASE  /* 0x00054000UL */
  #define TINIE_INT_EVENT_OFS            0x0020
  #define TINIE_INT_EVENT_IMASK_OFS      0x0028
  #define TINIE_MMR_OFS                  0x0120
  #define TINIE_CTL5_OFS                 0x0120
  #define TINIE_CTL1_OFS                 0x0130
  #define TINIE_MMR0_OFS                 0x0194
  #define TINIE_MMR1_OFS                 0x0198
  #define TINIE_MMR2_OFS                 0x019C
  #define TINIE_ACCREG_OFS               0x0C00
  #define TINIE_INS_MEM_OFS              0x1000
  #define TINIE_PARAMS_OFS               0x1800

  #define INT_TINIE                  0x00C70910U  // 9.16 - TINIE Interrupt

  #define TINIE_GET_ACCVAL_BASE_ADDR()  (TINIE_BASE_ADDR + TINIE_ACCREG_OFS)
  #define TINIE_GET_ACCVAL(base_addr, idx)  (*(volatile int32_t*)((base_addr) + (idx)*4))
  #define TINIE_STORE_BYTE(a, b) __byte((a), (b))

#else  /* M0, M33 */
  /*
   * MSPM0/AM13x SDK driverlib provide APIs for TINIE NPU internal registers accesses
   * */
  /* Set the instruction memory of the NPU at the specified offset. */
  extern void NPU_setInstrMem(uint32_t byteOffset, uint32_t num, const uint32_t *src);
  /* Set the parameter memory of the NPU at the specified offset. */
  extern void NPU_setParamMem(uint32_t byteOffset, uint32_t num, const uint32_t *src);
  /* Get the address of the NPU control register. */
  extern uint32_t NPU_getCtlReg(void);
  /* Get the address of the NPU ACC register. */
  extern uint32_t NPU_getAccReg(void);

  #define TINIE_GET_ACCVAL_BASE_ADDR()  (NPU_getAccReg())
  #define TINIE_GET_ACCVAL(base_addr, idx)  (*(volatile int32_t*)((base_addr) + (idx)*4))
  #define TINIE_STORE_BYTE(a, b) (a)[(b)]
#endif


typedef struct
{
    uint32_t  num_mmrs;            /* Number of MMR registers to be configured */
    uint32_t  num_params;          /* Number of parameters for this specific layer */
    uint32_t  num_ins;             /* Number of instructions to be configured */
    const uint32_t *mmrs;          /* Address of MMR's array */
    const uint32_t *params;        /* Address of parameters array */
    const uint32_t *ins;           /* Address of instructions array */
    int8_t   *in_fmap;             /* Address of input feature map */
    int8_t   *residual_fmap;       /* Address of residual input feature map */
    int8_t   *out_fmap;            /* Address of output feature map */
} TINIE_layer_t;


extern void TINIE_init(void);

extern void TINIE_registerInterrupt(void (*handler)(void));

extern void TINIE_clearInterruptACK(void);

extern void TINIE_setup(TINIE_layer_t *);

extern void TINIE_start(void);

#endif /* _TINIE_HARD_H_ */
