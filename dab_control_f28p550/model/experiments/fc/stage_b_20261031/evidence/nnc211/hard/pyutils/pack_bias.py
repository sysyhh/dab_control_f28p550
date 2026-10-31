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
# Pack bias for Hardware TINIE to use
# - input is raw bias data (32-bit)
# - output is encoded raw bias in 64-bit chunks

import numpy as np


def pack_b_oCb_in32_continuously(args, oC_start, oC_block_size, num_oC_blocks):
  # biases are packed continuously together in each 64-bit chunk
  if args.b_bits == 32 and args.b_packed_bits in [16, 24]:
    assert args.b_packed_bits != 24, "ERROR: 24-bit bias cannot be packed continuously"
    bias = np.fromfile(args.b_file, dtype='int32', count=-1, sep="")
    if bias.size == 1:  # repeat bias oC times
      bias = np.repeat(bias, args.oC)

    BIAS_MAX = np.int32(0x00007FFF) if args.b_packed_bits == 16 else np.int32(0x007FFFFF)
    BIAS_MIN = -BIAS_MAX - 1
    BIAS_MASK = np.uint32(0x0000FFFF) if args.b_packed_bits == 16 else  np.uint32(0x00FFFFFF)
    SHIFT_INC = 16 if args.b_packed_bits == 16 else 32  # 24-bit bias are padded as 32-bit

    oC_end   = min(oC_start + oC_block_size * num_oC_blocks, args.oC)
    packed = np.array([], dtype=np.uint64)
    b_encoding = np.uint64(0)
    b_shift = np.uint64(0)
    for i in range(oC_start, oC_end):
      b_val = bias[i]
      if (b_val < BIAS_MIN or b_val > BIAS_MAX):
        print(f"WARNING: pack_b_in32_continuously: {b_val} exceeded {args.b_packed_bits} bits, "
              "clamping to within range")
        b_val = BIAS_MIN if b_val < BIAS_MIN else (BIAS_MAX if b_val > BIAS_MAX else b_val)
      b_encoding = np.bitwise_or(b_encoding,
                    np.left_shift(np.uint64(np.bitwise_and(np.uint32(b_val), BIAS_MASK)), b_shift))
      b_shift += np.uint64(SHIFT_INC)
      if (b_shift >= 64):
        packed = np.append(packed, b_encoding)
        b_encoding = np.uint64(0)
        b_shift = np.uint64(0)
    if b_shift != 0:
      packed = np.append(packed, b_encoding)
    packed.tofile(args.b_packed_file, sep="")
    return packed.size

  else:
    assert(False), f"pack_b_oCb_in32_continuously does not support this config: {args}"


def pack_b_in32_continuously(args):
  return pack_b_oCb_in32_continuously(args, 0, args.oC, 1)


def pack_b_oCb_in32_signextend(args, oC_start, oC_block_size, num_oC_blocks, dup=1):
  """each 24-bit bias gets "sign-extended" and packed into 64-bit (4 x 16-bit lanes).
     Split decisions for each bias between lanes 0 and 3 are recorded during the overflow check.
     dup: duplicate the bias multiple times (required by the microcode)
  """
  if args.b_bits == 32 and args.b_packed_bits == 24:
    oC_end   = min(oC_start + oC_block_size * num_oC_blocks, args.oC)
    packed = np.array([], dtype=np.uint64)
    for  i in range(oC_start, oC_end):
      # Packing: b_lane0 are packed into [15:0] of 64-bit packed bias
      #          b_lane3 (including sign bits) are packed into [63:48] of 64-bit packed bias
      # LDBIAS: [15:0] (b_lane0) are treated as unsigned and put in the 18b lane 0 of TMA register
      #        [63:48] (b_lane3) are left-shifted by 2   and put in the 18b lane 3 of TMA register
      # Exmaple for b_lane0:b_lane3 splits (two extremes) on 24b bias of value -1:
      #    - 16:8 split, b_lane0 0x0000FFFF (unsigned, 65535), b_lane3: 0xFFFFFC00 (signed, -1024)
      #                  packed 64b bias 0xFF0000000000FFFF
      #    - 8:16 split, b_lane0 0x000000FF (unsigned,   255), b_lane3: 0xFFFFFFFC (signed,    -4)
      #                  packed 64b bias 0xFFFF0000000000FF
      b_lane0, b_lane3 = args.b_24b_split[i]
      b_encoding = np.bitwise_or(np.uint64(b_lane0),
                    np.left_shift(np.int64(b_lane3).astype(np.uint64), np.uint64(48-2)))
      packed = np.append(packed, b_encoding)
    if dup > 1:
      dup_packed = np.array([], dtype=np.uint64)
      for i in range(dup):
        dup_packed = np.append(dup_packed, packed)
      packed = dup_packed
    packed.tofile(args.b_packed_file, sep="")
    return packed.size

  else:
    assert(False), f"pack_b_oCb_in32_signextend does not yet support this config: {args}"


def pack_b_in32_signextend(args, dup=1):
  return pack_b_oCb_in32_signextend(args, 0, args.oC, 1, dup=dup)


def pack_b_oCb_in32_alternatively(args, oC_start, oC_block_size, num_oC_blocks):
  # 16b biases are packed "alternatively". e.g. 0x1234, 0x5678 packed as 0x0000567800001234
  if args.b_bits == 32 and args.b_packed_bits == 16:
    bias = np.fromfile(args.b_file, dtype='int32', count=-1, sep="")
    if bias.size == 1:  # repeat bias oC times
      bias = np.repeat(bias, args.oC)

    BIAS_MAX = np.int32(0x00007FFF)
    BIAS_MIN = -BIAS_MAX - 1
    BIAS_MASK = np.uint32(0x0000FFFF)
    SHIFT_INC = 32

    oC_end   = min(oC_start + oC_block_size * num_oC_blocks, args.oC)
    packed = np.array([], dtype=np.uint64)
    b_encoding = np.uint64(0)
    b_shift = np.uint64(0)
    for i in range(oC_start, oC_end):
      b_val = bias[i]
      if (b_val < BIAS_MIN or b_val > BIAS_MAX):
        print(f"WARNING: pack_b_in32_alternatively: {b_val} exceeded {args.b_packed_bits} bits, "
              "clamping to within range")
        b_val = BIAS_MIN if b_val < BIAS_MIN else (BIAS_MAX if b_val > BIAS_MAX else b_val)
      b_encoding = np.bitwise_or(b_encoding,
                    np.left_shift(np.uint64(np.bitwise_and(np.uint32(b_val), BIAS_MASK)), b_shift))
      b_shift += np.uint64(SHIFT_INC)
      if (b_shift >= 64):
        packed = np.append(packed, b_encoding)
        b_encoding = np.uint64(0)
        b_shift = np.uint64(0)
    if b_shift != 0:
      packed = np.append(packed, b_encoding)
    packed.tofile(args.b_packed_file, sep="")
    return packed.size

  else:
    assert(False), f"pack_b_oCb_in32_alternatively does not support this config: {args}"


def pack_b_0(args):
  packed = np.array([], dtype=np.uint64)
  packed = np.append(packed, np.uint64(0))
  packed.tofile(args.b_packed_file, sep="")
  return packed.size

def pack_b_oCb_in32(args, oC_start, oC_block_size, num_oC_blocks):
  """pack biases according to the kernel bit-width"""
  if args.w_packed_bits == 8:
    num_64bits_b_packed  = pack_b_oCb_in32_signextend(args, oC_start, oC_block_size,
                                                            num_oC_blocks)
  elif args.w_packed_bits == 4:
    num_64bits_b_packed  = pack_b_oCb_in32_alternatively(args, oC_start, oC_block_size,
                                                               num_oC_blocks)
  elif args.w_packed_bits==2:
    num_64bits_b_packed  = pack_b_oCb_in32_continuously(args, oC_start, oC_block_size,
                                                                num_oC_blocks)
  else:
    assert False, "Unsupported kernel bit-width for pack_b_oCb_in32"
  return num_64bits_b_packed
