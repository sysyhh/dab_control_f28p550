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
# Pack scale,shift for Hardware TINIE to use
# - input is raw scale,shift data (32-bit)
# - output is encoded raw (scale,shift) pairs, in 64-bit chunks

import numpy as np


def pack_ss_oCb_in32_pair(args, oC_start, oC_block_size, num_oC_blocks, dup=1):
  if args.sc_bits == 32 and args.sh_bits == 32 and args.ss_packed_bits == 8:
    scale = np.fromfile(args.sc_file, dtype='int32', count=-1, sep="")
    shift = np.fromfile(args.sh_file, dtype='int32', count=-1, sep="")
    if scale.size == 1:  # repeat for oC times
      scale = np.repeat(scale, args.oC)
    if shift.size == 1:  # repeat for oC times
      shift = np.repeat(shift, args.oC)

    oC_end = min(oC_start + oC_block_size * num_oC_blocks, args.oC)
    packed = np.array([], dtype=np.uint64)
    ss_encoding = np.uint64(0)
    ss_shift = np.uint64(0)
    for i in range(oC_start, oC_end):
      scale_val = scale[i]
      shift_val = shift[i]
      assert(0 <= scale_val and scale_val <= 0xFF), f"TINIE: scale {scale_val} needs to be 8-bit unsigned"
      assert(0 <= shift_val and shift_val <= 0x1F), f"TINIE: shift {shift_val} needs to be 5-bit unsigned"
      ss_pair = np.bitwise_or(np.left_shift(scale_val, np.int32(8)), shift_val);
      ss_encoding = np.bitwise_or(ss_encoding, np.left_shift(np.uint64(ss_pair), ss_shift))
      ss_shift += np.uint64(16)
      if (ss_shift >= 64):
        packed = np.append(packed, ss_encoding)
        ss_encoding = np.uint64(0)
        ss_shift = np.uint64(0)
    if ss_shift != 0:
      # duplicate ss_encoding to all channels
      while ss_shift < 64:
        dup_ss_encoding = np.left_shift(np.uint64(ss_encoding), np.uint64(ss_shift))
        ss_encoding = np.bitwise_or(ss_encoding, dup_ss_encoding)
        ss_shift *= 2
      packed = np.append(packed, ss_encoding)
    if dup > 1:
      dup_packed = np.array([], dtype=np.uint64)
      for i in range(dup):
        dup_packed = np.append(dup_packed, packed)
      packed = dup_packed
    packed.tofile(args.ss_packed_file, sep="")
    return packed.size

  else:
    assert(False), f"pack_ss_oCb_in32_pair does not yet support this config: {args}"


def pack_ss_in32_pair(args, dup=1):
  return pack_ss_oCb_in32_pair(args, 0, args.oC, 1, dup=dup)

