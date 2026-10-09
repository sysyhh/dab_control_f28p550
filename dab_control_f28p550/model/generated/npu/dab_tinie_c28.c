#define DAB_NPU_DETAIL_PROFILE 0
#include "dab_npu_trace.h"
extern volatile int32_t tinie_curr_layer;
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

#include <stdio.h>
#include <stdint.h>
#include "hard/inc/tinie.h"

/* Header file from C2000Ware SDK */
#include "driverlib.h"
#include "device.h"


/* Find the position of non-zero least significant bit in a 31-bit value and clear it.
 * C28 does not have an instruction to count trailing zeros.
 * Use __norm32() instead, which can handle up to 31-bit value. */
static inline uint8_t find_and_clear_lsb_in_31b(uint32_t *val)
{
    uint32_t v = *val;
    // clear the non-zero lsb bit for next iteration
    uint32_t v_lsb = v & (v - 1);
    *val = v_lsb;

    // (v - v_lsb) zeros out all bit except the non-zero lsb
    // __norm32() nomalize an integer to 0x40000000, return number of left shift bits
    int shift;
    __norm32((v - v_lsb), &shift);
    return (30 - shift);
}


static void write_configMMR(TINIE_layer_t *layer)
{
    volatile uint32_t *mmrs = (uint32_t *) (TINIE_BASE_ADDR + TINIE_MMR_OFS);

    // Part 1: Set MMRs except CTL5/4/3/1, MMR0/1  (CTL4/3 not used for now)
    if (layer->num_mmrs == TINIE_TOTAL_MMRS)
    {
        // uncompressed, all entries available
        mmrs[TINIE_CTL2_INDEX * 2] = layer->mmrs[TINIE_CTL2_INDEX];
        for (int i = TINIE_CTL0_INDEX; i < TINIE_MMR0_INDEX; i++)
            mmrs[i * 2] = layer->mmrs[i];
        if (layer->residual_fmap == NULL)
            mmrs[TINIE_MMR2_INDEX * 2] = layer->mmrs[TINIE_MMR2_INDEX];
        mmrs[TINIE_MMR3_INDEX * 2] = layer->mmrs[TINIE_MMR3_INDEX];
    }
    else if (layer->num_mmrs > 2)
    {
        // compressed, 2 32-bit bitvecs indicate which entries from CTL4 to MMR3 are set
        // always skip CTL5 in compressed mmrs[] data, so we start from element 1
        uint32_t bitvec_for_32b_val = layer->mmrs[0];
        uint32_t bitvec_for_8b_val  = layer->mmrs[1];
        const uint32_t *p_val = (const uint32_t *) &layer->mmrs[2];
        int32_t  bitvec_31bits;
        uint8_t  pos;

        if (bitvec_for_32b_val != 0)
        {
            bitvec_31bits = bitvec_for_32b_val & 0x7FFFFFFFUL;
            while (bitvec_31bits)
            {
                pos = find_and_clear_lsb_in_31b(&bitvec_31bits);
                mmrs[(1 + pos) * 2] = *p_val++;
            }
            if (bitvec_for_32b_val & 0x80000000UL)
            {
                mmrs[(1 + 31) * 2] = *p_val++;
            }
        }
        if (bitvec_for_8b_val != 0)
        {
            // 8b values are packed in 32b uint32_ts in little-endian (Cortex-M and C28)
            const uint8_t *p_8bval = (const uint8_t *) p_val;
            int count = 0;

            bitvec_31bits = bitvec_for_8b_val & 0x7FFFFFFFUL;
            while (bitvec_31bits)
            {
                pos = find_and_clear_lsb_in_31b(&bitvec_31bits);
                mmrs[(1 + pos) * 2] = __byte(p_8bval, count++);
            }
            if (bitvec_for_8b_val & 0x80000000UL)
            {
                mmrs[(1 + 31) * 2] = __byte(p_8bval, count++);
            }
        }
    }

    // Part 2: patch CTL1 and a few ARs to point them to correct ifmap/ofmap address values
    //         MMR0 for ifmap, MMR1 for ofmap, MMR2 for residual fmap
    uint32_t ctl1_val =  (((uint32_t)layer->in_fmap  >> 17) & 0xcfff) |
                        ((((uint32_t)layer->out_fmap >> 17) & 0xcfff) << 16);
    mmrs[TINIE_CTL1_INDEX * 2] = ctl1_val;
    mmrs[TINIE_MMR0_INDEX * 2] = ((((uint32_t) layer->in_fmap)  >> 1) & 0xffff);
    mmrs[TINIE_MMR1_INDEX * 2] = ((((uint32_t) layer->out_fmap) >> 1) & 0xffff);
    if (layer->residual_fmap != NULL)
        mmrs[TINIE_MMR2_INDEX * 2] = ((((uint32_t) layer->residual_fmap) >> 1) & 0xffff);
}


void TINIE_setup(TINIE_layer_t *layer)
{

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_PARAMS);
#endif
    // Step 1 - write to PARAMS memory
    volatile uint32_t *params = (uint32_t *) (TINIE_BASE_ADDR + TINIE_PARAMS_OFS);
    for (int i = 0; i < layer->num_params; i++)
    {
        params[i * 2] = layer->params[i];
    }


#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_PARAMS);
#endif

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_INS);
#endif
    // Step 2 - write to INS memory
    volatile uint32_t *ins = (uint32_t *) (TINIE_BASE_ADDR + TINIE_INS_MEM_OFS);
    for (int i = 0; i < layer->num_ins; i++)
    {
        ins[i * 2] = layer->ins[i];
    }


#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_INS);
#endif

#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_REGISTERS);
#endif
    // Step 3 - write to MMRs, config offsets for input/output
    write_configMMR(layer);
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceEnd(DAB_NPU_REGISTERS);
#endif

}


void TINIE_start(void)
{
#if DAB_NPU_DETAIL_PROFILE
  DAB_NN_traceBegin(DAB_NPU_WAIT0 + tinie_curr_layer - 1);
#endif

    // start layer execution, set START bit 1 in CTL5
    volatile uint32_t *mmrs = (uint32_t *) (TINIE_BASE_ADDR + TINIE_MMR_OFS);
    mmrs[TINIE_CTL5_INDEX * 2] = 0x1;
}


void TINIE_registerInterrupt(void (*handler)(void))
{
    Interrupt_disableGlobal();
    Interrupt_disable(INT_TINIE);
    Interrupt_register(INT_TINIE, handler);
    Interrupt_enable(INT_TINIE);
    Interrupt_enableGlobal();
}


void TINIE_clearInterruptACK(void)
{
    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP9);
}


void TI_NPU_init(void)
{
    // Configure TI NPU clock speed, enable TI NPU clock (i.e. enable TI NPU)
    SysCtl_setNPUClockDivider(SYSCTL_NPUCLK_DIV_1);
    SysCtl_enablePeripheral(SYSCTL_PERIPH_CLK_NPU);
    SYSCTL_REGWRITE_DELAY;

    // Enable interrupt; set IMASK 1
    HWREG(TINIE_BASE_ADDR + TINIE_INT_EVENT_IMASK_OFS) |= 0x1;

    Interrupt_clearACKGroup(INTERRUPT_ACK_GROUP9);
}

