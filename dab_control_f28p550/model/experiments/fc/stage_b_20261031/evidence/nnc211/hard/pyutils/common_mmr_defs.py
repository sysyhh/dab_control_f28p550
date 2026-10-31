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

import numpy as np


# Definition of MMR indices
# MMRs are 32-bit memory-mapped registers that TINIE uses in microcode

IND_CTL5    = 0
IND_CTL4    = 1
IND_CTL3    = 2
# Clamp range, [clamp hi (16-bit), clamp lo (16-bit)]
IND_CTL2    = 3
# Input/output feature map address masks, set by TINIE API automatically
IND_CTL1    = 4
# Layer encoding for layer type, input/output feature map bits and signness
IND_CTL0    = 5
# 6 loop counters, store (#iters - 1)  (i.e. 0-iter loop not supported)
IND_LC0     = 6
IND_LC1     = 7
IND_LC2     = 8
IND_LC3     = 9
IND_LC4     = 10
IND_LC5     = 11
# Program counter
IND_PC      = 12
# Address registers (usually) for input/output feature maps
IND_ARin0   = 13
IND_ARin1   = 14
IND_ARt0    = 15
IND_ARt1    = 16
IND_ARout0  = 17
IND_ARout1  = 18
IND_ARt2    = 19
IND_ARt3    = 20
# Address registers (usually) for weights (in TINIE internal memory)
IND_ARwt0   = 21
IND_ARwt1   = 22
IND_ARt4    = 23
IND_ARt5    = 24
# Address registers (usually) for bias (in TINIE internal memory)
IND_ARbias0 = 25
IND_ARt6    = 26
# Address registers (usually) for scale/shifts (in TINIE internal memory)
IND_ARss0   = 27
IND_ARt7    = 28
# Address registers for input, output and residual feature maps
IND_mmr0    = 29
IND_mmr1    = 30
IND_mmr2    = 31
IND_mmr3    = 32

TOTAL_MMRS  = 33


class MMR():
  """MMR class, help track which entries are set and compress generated MMR data.

  Parameters
  ----------
  constant_defs: list of entries that may be set/defined, but the values are unmodified
                 constants by the microcode.  No need to specify the ones that microcode
                 cannot modify, e.g. LC0, they are include by default in __init__().

  Note
  ----
    - Capture set entries, compress, write to file
    - Compression:
      - Based on the following observations:
        - not all 33 entries are set
        - CTL5 is always updated with a known value in runtime
        - some entries only have 8-bit values
        - some entries are unmodified by microcode and the subsequent sublayer can reuse the values
      - Consider set entries only.  If an entry is not set, no need to update it.
      - Compare with previous MMR from previous sublayer, skip update if an entry has the same
            value set in the previous MMR and the entry is unmodifed by previous sublayer microcode
      - Maintain two bit-vectors, 1 for setting 32-bit values, 1 for setting 8-bit values
      - Uncompressed MMR data in the generated code:
        [33 32b values]
        (values for all 33 MMR registers are explicitly specified,
         size of total data structure is 33 32b values)
      - Compressed MMR data in the generated code:
        [one 32b bit-vector for 32b values]
        [one 32b bit-vector for  8b values]
        [m 32b values]   (m: non-0 bits in the  first 32b bit-vector, m <= 32)
        [n  8b values]   (n: non-0 bits in the second 32b bit-vector, n <= 32, m+n <= 32)
        (size of total data structure smaller than 33 32b values)
        (CTL5 is excluded from compressed MMR data, runtime always set CTL5 with a known value)
        (8b values are packed into 32b values, starting from LSB to MSB in 32b values,
         then stored as 32b values in the generated layer data)
  """

  def __init__(self, args, constant_defs=[]):
    self.args = args
    self.constant_defs = constant_defs + \
                         [ IND_CTL4, IND_CTL3, IND_CTL2, IND_CTL1, IND_CTL0,
                           IND_LC0, IND_LC1, IND_LC2, IND_LC3, IND_LC4, IND_LC5,
                           IND_mmr0, IND_mmr1, IND_mmr2, IND_mmr3 ]
    self.values = np.array(np.repeat(0, TOTAL_MMRS), dtype=np.uint32)
    self.is_set = TOTAL_MMRS * [False]

  def __getitem__(self, key):
    """ Provides the indexing [] operator """
    return self.values[key]

  def __setitem__(self, key, value):
    """ Provides the indexing [] operator """
    self.values[key] = value
    self.is_set[key] = True

  def tofile(self, fname, sep="", prev_mmr=None):
    """ Compress (if asked for) and write data to file """

    # no compression, write out all MMR values
    if (self.args.opt_for_space == 0):
      self.values.tofile(fname, sep=sep)
      return

    # compression
    compressed = np.array(np.repeat(0, 2), dtype=np.uint32)  # 2 32b bit-vectors
    bitvec_32b = np.uint32(0)
    bitvec_8b  = np.uint32(0)
    values_8b = []
    prev_set        = prev_mmr.is_set if prev_mmr is not None else (TOTAL_MMRS * [False])
    prev_unmodified = prev_mmr.constant_defs if prev_mmr is not None else []

    # track which ones are set and cannot reuse values from prev mmr, separate 32b and 8b values
    for i in range(IND_CTL4, TOTAL_MMRS):
      bit = i - 1
      if self.is_set[i] and not (prev_set[i] and i in prev_unmodified and
                                 self.values[i] == prev_mmr[i]):
        if self.values[i] > 255:
            bitvec_32b = np.bitwise_or(bitvec_32b, np.uint32(1 << bit))
            compressed = np.append(compressed, self.values[i])
        else:
            bitvec_8b = np.bitwise_or(bitvec_8b, np.uint32(1 << bit))
            values_8b.append(self.values[i])
    compressed[0] = bitvec_32b
    compressed[1] = bitvec_8b

    # pack and append 8b values as 32b entities
    v_encoding = np.uint32(0)
    v_shift = 0
    for val in values_8b:
      v_encoding = np.bitwise_or(v_encoding, np.left_shift(val, np.uint32(v_shift)))
      v_shift += 8
      if v_shift == 32:
        compressed = np.append(compressed, np.uint32(v_encoding))
        v_encoding = np.uint32(0)
        v_shift = 0
    if v_shift != 0:
      compressed = np.append(compressed, np.uint32(v_encoding))

    # if compression achieved, write out compressed values, else write out all MMR values
    if len(compressed) < TOTAL_MMRS:
      compressed.tofile(fname, sep=sep)
    else:
      self.values.tofile(fname, sep=sep)


# CTL0 encoding  (info from inc/hw_tinielite.h)
#TINIELITE_CTL0_WTYPE_OFS                 (12)                            /* !< WTYPE Offset */
TINIE_CTL0_WTYPE = {
  #2T : 0x00000000,
  1 : 0x00001000,
  2 : 0x00002000,
  4 : 0x00003000,
  8 : 0x00004000,
}

#TINIELITE_CTL0_IFMAPTYPE_OFS             (0)                             /* !< IFMAPTYPE Offset */
TINIE_CTL0_IFMAPTYPE = {
  0 : {
    16 : 0x00000000,
     8 : 0x00000001,
     4 : 0x00000002,
     1 : 0x00000003,
  },
  1 : {
    16 : 0x00000008,
     8 : 0x00000009,
     4 : 0x0000000A,
     1 : 0x00000003,
  },
}

#TINIELITE_CTL0_OFMAPTYPE_OFS             (4)                             /* !< OFMAPTYPE Offset */
TINIE_CTL0_OFMAPTYPE = {
  0 : {
    16 : 0x00000000,
     8 : 0x00000010,
     4 : 0x00000020,
     1 : 0x00000030,
  },
  1 : {
    16 : 0x00000080,
     8 : 0x00000090,
     4 : 0x000000A0,
     1 : 0x00000030,
  },
}

#TINIELITE_CTL0_RESIFMAPTYPE_OFS          (26)                         /* !< RESIFMAPTYPE Offset */
TINIE_CTL0_RFMAPTYPE = {
  0 : {
    16 : 0x00000000,
     8 : 0x04000000,
     4 : 0x08000000,
  },
  1 : {
    16 : 0x20000000,
     8 : 0x24000000,
     4 : 0x28000000,
  },
}

#TINIELITE_CTL0_LAYERTYPE_OFS             (20)                            /* !< LAYERTYPE Offset */
TINIE_CTL0_LAYERTYPE = {
  'FCONV'      : 0x00000000,
  'DWCONV'     : 0x00200000,
  'PWCONV'     : 0x00300000,
  'CONV'       : 0x00500000,
  'FC'         : 0x00600000,
  'AVGPOOL'    : 0x00700000,
  'MAXPOOL'    : 0x00800000,
  'FCONVRES'   : 0x01000000,
  'DWCONVRES'  : 0x01200000,
  'PWCONVRES'  : 0x01300000,
  'CONVRES'    : 0x01500000,
  'FCRES'      : 0x01600000,
  'AVGPOOLRES' : 0x01700000,
  'MAXPOOLRES' : 0x01800000,
}


def gen_ctl0(args, layer_type_name):
  return (TINIE_CTL0_WTYPE[args.w_packed_bits] |
          TINIE_CTL0_IFMAPTYPE[args.in_signed][args.in_bits] |
          TINIE_CTL0_OFMAPTYPE[args.out_signed][args.out_bits] |
          TINIE_CTL0_RFMAPTYPE[args.res_signed][args.res_bits] |
          TINIE_CTL0_LAYERTYPE[layer_type_name])

def gen_ctl2(args):
  """return encoded output fmap clamp range"""
  if args.out_bits == 8:
    return 0x007F0180 if (args.out_signed == 1) else 0x00FF0000   # [-128,127] or [0,255]
  else:
    assert False, f"Output feature map of {args.out_bits} bits not supported yet"


def gen_mmr_padH_same_microcode(mmr, args):
  """Generate mmr entries for output height padding in the same microcode
     LC4: iterations of padding on top
     LC5: iterations of padding on bottom
     ARt4: stride for jump to bottom padding addr after top padding
  """
  top_amount    = args.opT * args.oW * args.oC // 4
  jump_amount   = args.oH  * args.oW * args.oC // 4
  bottom_amount = args.opB * args.oW * args.oC // 4
  if top_amount > 0:
    mmr[IND_LC4] = top_amount - 1
  else:
    mmr[IND_LC4] = 0  # write 1 word of 0, will be overwritten by actual computation later
    jump_amount -= 1
  if bottom_amount > 0:
    mmr[IND_LC5] = bottom_amount - 1
  else:
    jump_amount  = 0
    mmr[IND_LC5] = 0  # write 1 word of 0, will be overwritten by actual computation later
  mmr[IND_ARt4] = jump_amount

