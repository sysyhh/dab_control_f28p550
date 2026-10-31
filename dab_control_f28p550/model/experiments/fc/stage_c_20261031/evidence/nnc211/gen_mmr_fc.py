"""
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
"""
# Generate FullyConnected MMRs for Hardware TINIE to use
# - output is encoded raw MMR values in 32-bit unsigned

import numpy as np
from common_mmr_defs import *


def gen_mmr_fc_iCm8b8_oCm_w4(args, w_num_64bits, b_num_64bits, oC_start, num_oC_blocks, PC,
                             prev_mmr=None):
  if args.iC >= 8:
    mmr = MMR(args, [IND_ARout1, IND_ARt5])
    mmr[IND_CTL2] = gen_ctl2(args)
    mmr[IND_CTL0] = gen_ctl0(args, "FC")
    mmr[IND_LC2] = num_oC_blocks - 1
    # Macro computing 8 input channels at a time.
    mmr[IND_LC3] = (args.iC + 7) // 8 -1
    mmr[IND_PC] = PC # starting PC, there might be macro defined at the beginning

    mmr[IND_ARout1] = 0            # init value for sublayer offset to start read  in ifmap
    mmr[IND_ARt5] = oC_start // 4  # init value for sublayer offset to start write in ofmap.
    mmr[IND_ARwt0] = 0
    mmr[IND_ARbias0] = w_num_64bits
    mmr[IND_ARss0] = (w_num_64bits + b_num_64bits)

    mmr.tofile(args.mmr_file, sep="", prev_mmr=prev_mmr)
    return mmr
  else:
    assert (False), f"gen_mmr_fc_iCm8b8_oCm_w4 does not support this config: {args}"


def gen_mmr_fc_iCm8b16_oCm_w8(args, w_num_64bits, b_num_64bits, oC_start, num_oC_blocks, PC,
                              prev_mmr=None):
  if args.iC >= 16:
    mmr = MMR(args, [IND_ARout1, IND_ARt5])
    mmr[IND_CTL2] = gen_ctl2(args)
    mmr[IND_CTL0] = gen_ctl0(args, "FC")
    mmr[IND_LC2] = num_oC_blocks - 1
    # MACRO computing 8 input channels at a time, pad args.iC to multiple of 8
    mmr[IND_LC3] = (args.iC + 7 - 8) // 8 - 1
    mmr[IND_PC] = PC  # starting PC, there might be macro defined at the beginning

    mmr[IND_ARout1] = 0            # init value for sublayer offset to start read  in ifmap
    mmr[IND_ARt5] = oC_start // 4  # init value for sublayer offset to start write in ofmap.
    mmr[IND_ARwt0] = 0
    mmr[IND_ARbias0] = w_num_64bits
    mmr[IND_ARss0] = (w_num_64bits + b_num_64bits)

    mmr.tofile(args.mmr_file, sep="", prev_mmr=prev_mmr)
    return mmr

  else:
    assert(False), f"gen_mmr_fc_iCm8b16_oCm_w8 does not support this config: {args}"


def gen_mmr_fc_w_host_postproc_iCm_oCm(args, w_num_64bits, iC_start, iC_block_size, iC_multiple,
                                       prev_mmr=None):
  mmr = MMR(args, [IND_ARout1, IND_ARbias0])
  mmr[IND_CTL2] = gen_ctl2(args)
  mmr[IND_CTL0] = gen_ctl0(args, "FC")
  mmr[IND_LC3] = (iC_block_size + (iC_multiple-1)) // iC_multiple - 1
  mmr[IND_PC] = 0
  mmr[IND_ARout1] = iC_start // 4
  mmr[IND_ARwt0] = 0
  mmr[IND_ARbias0] = w_num_64bits

  mmr.tofile(args.mmr_file, sep="", prev_mmr=prev_mmr)
  return mmr

