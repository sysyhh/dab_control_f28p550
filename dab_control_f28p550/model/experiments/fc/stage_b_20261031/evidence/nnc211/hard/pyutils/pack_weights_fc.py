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
# Pack FullyConnected weights for Hardware TINIE to use
# - input is raw weights data (8-bit)
# - output is encoded raw weights in 64-bit chunks

import numpy as np

def pack_w_fc_val_4b_1in2(w_val, w_encoding, w_shift, packed):
  # Encode 1 4-bit weight (w_val) into the existing encoding.
  # 4 4-bit weights are encoded into the same 16 bits at a time.
  # [3210] is shuffled as: [000000 [32]] [000000 [10]]
  w_16 = np.bitwise_and(w_val.astype(np.uint16), np.uint16(0xF))
  w_shuffle = np.bitwise_or(
  np.left_shift(np.bitwise_and(np.right_shift(w_16, np.uint16(2)), np.uint16(0x3)), np.uint16(8)),
  np.left_shift(np.bitwise_and(np.right_shift(w_16, np.uint16(0)), np.uint16(0x3)), np.uint16(0)))
  w_64 = w_shuffle.astype(np.uint64)
  w_encoding = np.bitwise_or(w_encoding, np.left_shift(w_64, np.uint64(w_shift)))
  w_shift +=2
  # After 4 weights, need to shift to the next 16-bit word.
  if w_shift % 8 == 0:
    w_shift += 8
  if w_shift >= 64:
    packed = np.append(packed, w_encoding)
    w_encoding = np.uint64(0)
    w_shift = 0

  return w_encoding, w_shift, packed

def pack_w_fc_val_8b_1in4(w_val, w_encoding, w_shift, packed):
  # Encode 1 8-bit weight (w_val) into existing encoding (w_encoding, w_shift)
  # 4 8-bit weights are encoded into the same 32-bit at a time, their bits are shuffled/packed as
  #   [76][76][76][76] [54][54][54][54] [32][32][32][32] [10][10][10][10]
  # each weight [76543210] is shuffled as: [000000][76] [000000][54] [000000][32] [000000][10]
  #   first, then shifted and or-ed into the encoding
  w_32 = np.bitwise_and(w_val.astype(np.uint32), np.uint32(0xFF))
  w_shuffle = np.bitwise_or(
  np.left_shift(np.bitwise_and(np.right_shift(w_32, np.uint32(6)), np.uint32(0x3)), np.uint32(24)),
  np.left_shift(np.bitwise_and(np.right_shift(w_32, np.uint32(4)), np.uint32(0x3)), np.uint32(16)))
  w_shuffle = np.bitwise_or(w_shuffle,
  np.left_shift(np.bitwise_and(np.right_shift(w_32, np.uint32(2)), np.uint32(0x3)), np.uint32(8)))
  w_shuffle = np.bitwise_or(w_shuffle,
  np.left_shift(np.bitwise_and(np.right_shift(w_32, np.uint32(0)), np.uint32(0x3)), np.uint32(0)))
  w_64 = w_shuffle.astype(np.uint64)
  w_encoding = np.bitwise_or(w_encoding, np.left_shift(w_64, np.uint64(w_shift)))

  # shift for each weight
  w_shift += 2
  # after 4 weights, we need to shift to the next 32-bits
  if w_shift == 8 or w_shift == 40:
    w_shift += 24
  if w_shift >= 64:
    packed = np.append(packed, w_encoding)
    w_encoding = np.uint64(0)
    w_shift = 0

  return w_encoding, w_shift, packed


def pack_w_fc_iCm8_oCm(args, oC_start, oC_block_size, num_oC_blocks):
  if args.w_layout == "OI" and args.w_bits == 8 and args.w_packed_bits in [4,8]:
    # Weights: data is 1 x iC, input weights layout is oC x iC, output data is 1 x oC
    #   Weights packing is tied to microcode:
    #     oC_outer x iC_outer x oC_inner x iC_inner
    #     in one particular instance: (oC_inner x iC_inner) is a (4 x 8) block
    #   ic_inner is packed specially because HW TINIE is doing 4 8b(data) x 2b (weights) TMAs
    #     and 4 sub sums are shifted and added together by BNORM instruction for final result

    weights = np.fromfile(args.w_file, dtype='int8', count=-1, sep="")
    weights = np.reshape(weights, (args.oC, args.iC))

    iC_block_size = 4  # 4 input  channels at a time, tied to the micro code
    # pad total iC to multiple of 8, tied to micro code
    num_iC_blocks = (((args.iC + 7) // 8) * 8) // iC_block_size
    # pad total oC to a multiple of 2, tied to 4-bit weights mirco code
    if args.w_packed_bits == 4 and oC_block_size < 2:
      oC_block_size = 2

    packed = np.array([], dtype=np.uint64)
    w_encoding = np.uint64(0)
    w_shift = 0
    for oblock in range(num_oC_blocks):
      for iblock in range(num_iC_blocks):
          for oC in range(oC_block_size):
            for iC in range(iC_block_size):
              if  oC_start + oblock * oC_block_size + oC < args.oC and \
                iblock * iC_block_size + iC < args.iC:
                w_val = weights[oC_start + oblock * oC_block_size + oC][iblock * iC_block_size + iC]
              else:
                w_val = np.int8(0)
              if args.w_packed_bits == 4:
                w_encoding, w_shift, packed =pack_w_fc_val_4b_1in2(w_val, w_encoding,w_shift,packed)
              else:
                w_encoding, w_shift, packed =pack_w_fc_val_8b_1in4(w_val, w_encoding,w_shift,packed)
    if w_shift != 0:
      packed = np.append(packed, w_encoding)
    packed.tofile(args.w_packed_file, sep="")
    return packed.size

  else:
    assert(False), f"pack_w_fc_iCm8b16_oCm does not support this config: {args}"


def pack_w_fc_w_host_postproc_iCm_oCm(args, iC_start, iC_block_size, iC_multiple,
                                               oC_start, oC_block_size):
  if args.w_layout == "OI" and args.w_bits == 8 and args.w_packed_bits in [4,8]:
    # Compute partial results of 1 x iC_block_size data with iC_block_size x oC_block_size weights
    #   Weights packing is tied to microcode:
    #     (iC_outer padded to iC_multiple) x oC_block_size x (iC_inner=4)
    #   ic_inner is packed specially because HW TINIE is doing 4 8b(data) x 2b (weights) TMAs
    #     and 4 sub sums are shifted and added together for the total sum on host CPU

    weights = np.fromfile(args.w_file, dtype='int8', count=-1, sep="")
    weights = np.reshape(weights, (args.oC, args.iC))

    iC_inner = 4  # 4 input  channels at a time, tied to the micro code
    num_iC_blocks = ((iC_block_size + (iC_multiple-1)) // iC_multiple) * iC_multiple // iC_inner

    packed = np.array([], dtype=np.uint64)
    w_encoding = np.uint64(0)
    w_shift = 0
    for iblock in range(num_iC_blocks):
      for oC in range(oC_block_size):
        for iC in range(iC_inner):
          if (iblock * iC_inner + iC < iC_block_size) and (oC_start + oC < args.oC):
            w_val = weights[oC_start + oC][iC_start + iblock * iC_inner + iC]
          else:
            w_val = np.int8(0)
          if args.w_packed_bits == 4:
            w_encoding, w_shift, packed = pack_w_fc_val_4b_1in2(w_val, w_encoding,w_shift,packed)
          else:
            w_encoding, w_shift, packed = pack_w_fc_val_8b_1in4(w_val, w_encoding,w_shift,packed)

    if w_shift != 0:
      packed = np.append(packed, w_encoding)
    packed.tofile(args.w_packed_file, sep="")
    return packed.size
  else:
    assert(False), f"pack_w_fc_w_host_postproc_iCm_oCm does not support this config: {args}"

