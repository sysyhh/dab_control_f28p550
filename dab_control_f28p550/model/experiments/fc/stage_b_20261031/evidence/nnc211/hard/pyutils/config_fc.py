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
# Generate fully connected layer config for Hardware TINIE to use
# - parameters, mmr, ins

import numpy as np
from common_utils import *
from pack_weights_fc import *
from pack_bias import *
from pack_scale_shift import *
from gen_mmr_fc import *

# Max iC that can fit into TINIE params buffer for computing even 1 oC
#   each 64-bit computing 8 iCs, 1 64-bit for bias, 1 64-bit for scale/shift
#     for 4-bit weights, we compute 2 oCs at a time in each TMAout register
TINIE_FC_MAX_IC_NO_HOST = (TINIE_PARAMS_BUFSIZE // 8 - 1 - 1) * 8
# If with host post-processing, bias/scale/shift is done on host,
#     but we still need 1 64-bit bias to initialize TMAouts
#     for 8-bit weights, each 32-bit can hold 1oCs x 4iCs
#     for 4-bit weights, each 32-bit can hold 2oCs x 4iCs
TINIE_FC_MAX_IC_W_HOST      = (TINIE_PARAMS_BUFSIZE // 8 - 1) * 8
TINIE_FC_MAX_ICOC_W_HOST_w8 = TINIE_FC_MAX_IC_W_HOST * 1
TINIE_FC_MAX_ICOC_W_HOST_w4 = TINIE_FC_MAX_IC_W_HOST * 2


def get_fc_ins_pc(oC_start, oC_block_size, num_oC_blocks, w_packed_bits=8):
  ins = "" if oC_start == 0 else "\n"
  pc = 8
  if w_packed_bits == 4:
    if oC_block_size == 4:
      ins += "FC_iB8_oB8_kB4_iCm8_oCm4_INS"
    elif oC_block_size in [1,2]:
      if (oC_start % 4 in [0,1]):
        ins += "FC_iB8_oB8_kB4_iCm8_oC2L_INS"
      else:
        ins += "FC_iB8_oB8_kB4_iCm8_oC2H_INS"
  elif w_packed_bits == 8:
    if oC_block_size == 4:
      ins += "FC_iB8_oB8_kB8_iCm8b16_oCm4_INS"
      pc = 16
    elif oC_block_size == 2:
      if (oC_start % 4 == 0):
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC2L_INS"
      else:
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC2H_INS"
    else:
      if (oC_start % 4 == 0):
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC1LL_INS"
      elif (oC_start % 4 == 1):
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC1LH_INS"
      elif (oC_start % 4 == 2):
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC1HL_INS"
      else:
        ins += "FC_iB8_oB8_kB8_iCm8b16_oC1HH_INS"
  else:
    assert False, f"w_packed_bits: {w_packed_bits} is not a valid bitwidth"
  return ins, pc


# Valid (with microcode support) oC block sizes
# Case 1: Does not need host post-processing (block oCs only, no need to block iCs)
# 8-bit: m4 (TODO: replace w/ m8+4, m8+0), 2L, 2H, 1LL, 1LH, 1HL, 1HH
# 4-bit: m4 (TODO: replace w/ m16+12, m16+8, m16+4, m16+0), 2L, 2H  (if oC%2 == 1, pad oC to m2)
#
# Case 2: Need host post-processing (blocks both iCs and oCs)
# 8-bit: 8 (iCm8), 6 (iCm8), 4 (iCm8), 3 (iCm16), 2 (iCm16), 1 (iCm32)
# 4-bit: 16 (iCm8), 14 (iCm16), 12 (iCm8), 10 (iCm16), 8 (iCm8), 6 (iCm16), 4 (iCm16), 2 (iCm32)
#
FC_W_HOST_POSTPROC_VALID_oC_BLOCK_SIZES = {
        # weight bit-wdith: list of valide oC block sizes
        8: [8, 6, 4, 3, 2, 1],
        4: [16, 14, 12, 10, 8, 6, 4, 2],
}
# Microcode iC iterations in loop body when computing different oC
FC_W_HOST_POSTPROC_iC_MULTIPLE = {
        # weight bit-wdith: list of valide oC block sizes to iC multiple mapping
        8: { 8:8, 6:8, 4:8, 3:16, 2:16, 1:32 },
        4: { 16:8, 14:16, 12:8, 10:16, 8:8, 6:16, 4:16, 2:32 },
}


def get_fc_w_host_postproc_ins_iC_multiple(args, sublayer, oC_block_size):
  ins = "" if sublayer == 0 else "\n"
  iC_multiple = FC_W_HOST_POSTPROC_iC_MULTIPLE[args.w_packed_bits][oC_block_size]
  if args.w_packed_bits == 4 and oC_block_size % 2 == 0 and oC_block_size//2 in \
    FC_W_HOST_POSTPROC_VALID_oC_BLOCK_SIZES[8] and \
    iC_multiple == FC_W_HOST_POSTPROC_iC_MULTIPLE[8][oC_block_size//2]:
    ins += f"FC_iB8_oB8_kB8_iCm{iC_multiple}_oC{oC_block_size//2}_w_host_postproc_INS"
  else:
    ins += f"FC_iB8_oB8_kB{args.w_packed_bits}_iCm{iC_multiple}_oC{oC_block_size}_w_host_postproc_INS"
  return ins, iC_multiple


def check_fc_overflow(args):

  def sublayers_search(args, weights, d_min, d_max, search_oC_first=False):
    sublayers = []
    oC_remaining = args.oC
    oC_remaining_start = 0
    if args.w_packed_bits == 8:
      TINIE_FC_MAX_ICOC_W_HOST = TINIE_FC_MAX_ICOC_W_HOST_w8
      check_accum_overflow_kB_func = check_accum_overflow_kB8
    else:
      TINIE_FC_MAX_ICOC_W_HOST = TINIE_FC_MAX_ICOC_W_HOST_w4
      check_accum_overflow_kB_func = check_accum_overflow_kB4

    # for all remaining oCs not yet computed
    while oC_remaining > 0:
      iC_remaining = args.iC
      iC_remaining_start = 0
      if search_oC_first:
        for oC_block_size in FC_W_HOST_POSTPROC_VALID_oC_BLOCK_SIZES[args.w_packed_bits]:
          if oC_block_size <= oC_remaining:
            break
      else:
        oC_block_size = 0

      # for all remaining iCs not yet computed
      while iC_remaining > 0:
        oC_max_block_size = FC_W_HOST_POSTPROC_VALID_oC_BLOCK_SIZES[args.w_packed_bits][0]
        oC_try_block_size = min(oC_max_block_size, oC_remaining) if oC_block_size == 0 \
                                                               else oC_block_size
        overflow = [iC_remaining] * oC_max_block_size

        # compute max iCs without overflow for each oC
        for oC in range(oC_remaining_start, oC_remaining_start + oC_try_block_size):
          # case 1: weight is 8-bit
          # if oC_try_block_size <= 4, each oC's partial sum are spread across multiple TMAouts
          # e.g. oC_try_block_size==2, first oC gets TMAout 0,1,2,3, second oC gets 4,5,6,7
          # case 2: weight is 4-bit
          # if oC_try_block_size <= 8, each oC's partial sum are spread across multiple TMAouts
          # e.g. oC_try_block_size==4, oC0/1 gets TMAout 0,1,2,3, oC2/3 gets 4,5,6,7
          weights_spread = oC_max_block_size // oC_try_block_size
          for spread in range(weights_spread):
            tmaout_min = [0, 0, 0, 0]  # host post-processing will handle bias
            tmaout_max = [0, 0, 0, 0]
            for iC in range(iC_remaining_start + spread,
                            iC_remaining_start + iC_remaining, weights_spread):
              w_val = weights[oC][iC] if oC < args.oC else np.int8(0)
              if check_accum_overflow_kB_func(w_val, d_min, d_max, tmaout_min, tmaout_max):
                overflow[oC - oC_remaining_start] = min(overflow[oC - oC_remaining_start],
                                                        iC - iC_remaining_start)
                break

        # use the minimum iCs without overflow across all oCs as the iCs across all oCs
        iC_block_size = min(overflow)
        if iC_block_size < iC_remaining:
          iC_block_size -= (iC_block_size % 4)
        iC_block_size = min(iC_block_size, TINIE_FC_MAX_IC_W_HOST)
        if oC_block_size == 0:
          # Given iC_block_size, find max oC_block_size that packed weights can fit in memory
          for oC_block_size in FC_W_HOST_POSTPROC_VALID_oC_BLOCK_SIZES[args.w_packed_bits]:
            if oC_block_size <= oC_remaining and \
               iC_block_size * oC_block_size <= TINIE_FC_MAX_ICOC_W_HOST:
              break

        # Given oC_block_size, find max iC_block_size that packed weights can fit in memory
        max_iC_block_size = TINIE_FC_MAX_ICOC_W_HOST // oC_block_size
        max_iC_block_size -= (max_iC_block_size % 4)
        iC_block_size = min(iC_block_size, max_iC_block_size)

        # iC is rounded up by iC_multiple and computed with padded weights in microcode
        # make sure padded dimension still fits in memory
        iC_multiple = FC_W_HOST_POSTPROC_iC_MULTIPLE[args.w_packed_bits][oC_block_size]
        iC_roundup = ((iC_block_size + iC_multiple - 1) // iC_multiple) * iC_multiple
        if (iC_roundup * oC_block_size) > TINIE_FC_MAX_ICOC_W_HOST:
          iC_block_size = iC_roundup - iC_multiple

        # record the computed sublayer, continue for remaining iCs
        sublayers.append([iC_block_size, oC_block_size])
        iC_remaining -= iC_block_size
        iC_remaining_start += iC_block_size

      # continue for remaining oCs
      oC_remaining -= oC_block_size
      oC_remaining_start += oC_block_size
    return sublayers


  weights = args.w_data if args.w_data is not None else \
            np.fromfile(args.w_file, dtype='int8', count=-1, sep="")
  weights = np.reshape(weights, (args.oC, args.iC))
  bias = args.b_data if args.b_data is not None else \
         np.fromfile(args.b_file, dtype='int32', count=-1, sep="")
  d_min, d_max = get_indata_min_max(args)

  # For 24-bit bias, search and record split decision that won't cause overflow
  if args.w_packed_bits == 8:
    args_dict = vars(args)
    args_dict['b_24b_split'] = [(0, 0)] * args.oC
  no_overflow = True
  for oC in range(args.oC):
    if check_npu_accum_overflow(args, oC, d_min, d_max, weights[oC], bias[oC]):
      no_overflow = False
      break
  # if no oC has potential overflow, return empty list
  if no_overflow:
    return []

  # Compute sublayer partitioning in order to avoid overflow
  # return [(iC_block_size, oC_block_size), ...]
  # iC first search (maximizing iCs being computed each sublayer)
  iCf_sublayers = sublayers_search(args, weights, d_min, d_max, search_oC_first=False)
  # oC first search (maximizing oCs being computed each sublayer)
  oCf_sublayers = sublayers_search(args, weights, d_min, d_max, search_oC_first=True)
  #print("iCf_sublayers:", iCf_sublayers)
  #print("oCf_sublayers:", oCf_sublayers)
  # pick the partition with the least amount of sublayers
  return iCf_sublayers if len(iCf_sublayers) < len(oCf_sublayers) else oCf_sublayers


def config_fc_no_host_postproc(args):
  oC_start = 0
  oC_remaining = args.oC
  sublayers_bounds = []  # list of [start oC, oC_block_size, num_oC_blocks] tuple
  ## Block oC using oC_block_size = 4 channels, 2 channels, 1 channel, in this order
  block_sizes = [4, 2, 1] if args.oC >= 4 else ([2, 1] if args.oC >= 2 else [1])
  for oC_block_size in block_sizes:
    if oC_remaining == 0:
      break
    num_64bits_w_packed_block  = pack_w_fc_iCm8_oCm(args, 0, oC_block_size, 1)
    if args.w_packed_bits == 4:
      num_64bits_b_packed_block  = pack_b_oCb_in32_alternatively(args, 0, oC_block_size, 1)
    else:
      num_64bits_b_packed_block  = pack_b_oCb_in32_signextend(args, 0, oC_block_size, 1)
    # oCm4 microcode overloads biases
    num_64bits_b_prefetched = args.w_packed_bits // 2 if oC_block_size == 4 else 0
    num_64bits_ss_packed_block = pack_ss_oCb_in32_pair(args, 0, oC_block_size, 1)
    num_sublayers, num_oC_blocks = block_output_channels(args, oC_remaining, oC_block_size,
        num_64bits_w_packed_block*8, num_64bits_b_packed_block*8, num_64bits_ss_packed_block*8,
        must_block=(oC_block_size == 1), num_bias_prefetches=num_64bits_b_prefetched)
    if (num_sublayers == 0):
      continue
    if (oC_block_size != 4):
      num_oC_blocks = 1
      num_sublayers = oC_remaining // oC_block_size
    for i in range(num_sublayers):
      curr_num_oC_blocks = min(num_oC_blocks, oC_remaining // oC_block_size)
      if curr_num_oC_blocks > 0:
        sublayers_bounds.append([oC_start, oC_block_size, curr_num_oC_blocks])
        oC_start     += oC_block_size * curr_num_oC_blocks
        oC_remaining -= oC_block_size * curr_num_oC_blocks

  if os.environ.get("TINIE_COMPILE_DEBUG", None):
    print(f"FC sublayers (oC blocking): {sublayers_bounds}")
  save_args_out_filenames(args)
  all_ins = ""
  prev_ins = ""
  prev_mmr = None
  for sublayer, bounds in enumerate(sublayers_bounds):
    set_args_sublayer_out_filenames(args, sublayer)
    oC_start, oC_block_size, num_oC_blocks = bounds
    ins, pc = get_fc_ins_pc(oC_start, oC_block_size, num_oC_blocks, args.w_packed_bits)
    all_ins += (ins if (ins != prev_ins and ins != f"\n{prev_ins}") else "\nEMPTY_INS")
    prev_ins = ins
    num_64bits_w_packed  = pack_w_fc_iCm8_oCm(args, oC_start, oC_block_size, num_oC_blocks)
    if args.w_packed_bits == 4:
      num_64bits_b_packed = pack_b_oCb_in32_alternatively(args, oC_start, oC_block_size, num_oC_blocks)
    else:
      num_64bits_b_packed  = pack_b_oCb_in32_signextend(args, oC_start, oC_block_size,num_oC_blocks)
    _ = pack_ss_oCb_in32_pair(args, oC_start, oC_block_size, num_oC_blocks)
    if args.w_packed_bits == 4:
      prev_mmr = gen_mmr_fc_iCm8b8_oCm_w4(args, num_64bits_w_packed, num_64bits_b_packed,
                                          oC_start, num_oC_blocks, pc, prev_mmr=prev_mmr)
    else:
      prev_mmr = gen_mmr_fc_iCm8b16_oCm_w8(args, num_64bits_w_packed, num_64bits_b_packed,
                                           oC_start, num_oC_blocks, pc, prev_mmr=prev_mmr)
  restore_args_out_filenames(args)
  get_ins_generic(args, all_ins)


def config_fc_with_host_postproc(args, overflow_sublayers):
  if os.environ.get("TINIE_COMPILE_DEBUG", None):
    print(f"FC sublayers (iCxoC blocking): {overflow_sublayers}")
  # An empty array to help empty the files where parameters are not needed by microcode(s)
  packed = np.array([], dtype=np.uint64)

  save_args_out_filenames(args)
  all_ins = ""
  prev_ins = ""
  prev_mmr = None
  iC_start = 0
  oC_start = 0
  num_iC_blocks = 0
  host_postproc_control = np.array([], dtype=np.uint8)  # list of (num_iC_blocks, oC_block_size)
  for sublayer, bounds in enumerate(overflow_sublayers):
    set_args_sublayer_out_filenames(args, sublayer)
    iC_block_size, oC_block_size = bounds
    ins, iC_multiple = get_fc_w_host_postproc_ins_iC_multiple(args, sublayer, oC_block_size)
    all_ins += (ins if (ins != prev_ins and ins != f"\n{prev_ins}") else "\nEMPTY_INS")
    prev_ins = ins
    num_64bits_w_packed  = pack_w_fc_w_host_postproc_iCm_oCm(args,
        iC_start, iC_block_size, iC_multiple, oC_start, oC_block_size)
    _ = pack_b_0(args)
    # no scale/shift are needed in the microcode for the host post-processing
    packed.tofile(args.ss_packed_file, sep="")
    prev_mmr = gen_mmr_fc_w_host_postproc_iCm_oCm(args, num_64bits_w_packed,
                                                  iC_start, iC_block_size, iC_multiple, prev_mmr)
    num_iC_blocks += 1
    iC_start += iC_block_size
    if iC_start >= args.iC:
      host_postproc_control = np.append(host_postproc_control,
                                        [np.uint8(num_iC_blocks), np.uint8(oC_block_size)])
      iC_start = num_iC_blocks = 0
      oC_start += oC_block_size
  host_postproc_control.tofile(args.postproc_file, sep="")
  # add a terminating sublayer to finish the host post-processing
  # there will be no updates to INS/Weights/MMR, rerun last layer's END instruction (where PC was)
  set_args_sublayer_out_filenames(args, len(overflow_sublayers))
  packed.tofile(args.w_packed_file, sep="")
  packed.tofile(args.b_packed_file, sep="")
  packed.tofile(args.ss_packed_file, sep="")
  packed.tofile(args.mmr_file, sep="")
  restore_args_out_filenames(args)
  all_ins += "\nEMPTY_INS"

  get_ins_generic(args, all_ins)


def config_fc(args, check_only=False):
  """ Generating hardware TINIE setup for a layer config

  Parameters
  ----------
  args : Namespace object
  check_only : only checks if a layer config is supported, no need to generate hardware setup

  Return
  ------
  diags : list of diagnostic information
  hardware TINIE setup: in the filesystem
  """

  diags = []
  layer = "FC"
  diags.append(("INFO", f"{layer} layer config: " + DIAGS_CONFIG_FC.format(**(vars(args)))))
  diags_check_ifmap_8bit(diags, args, layer)
  diags_check_ofmap_8bit(diags, args, layer)
  diags_check_w_layout(diags, args, "OI", layer)
  diags_check_scale1_if_8bit_weights(diags, args, layer)
  if (args.iC < 16 and args.w_packed_bits == 8):
    diags.append(("WARNING", f"{layer} does not support iC less than 16"))
  elif (args.iC < 8 and args.w_packed_bits == 4):
    diags.append(("WARNING", f"{layer} does not support iC less than 8"))
  if (args.w_packed_bits not in [4,8]):
    diags.append(("WARNING", f"{layer} does not support {args.w_packed_bits}-bit weights"))


  # check if weights in input channels could potentially cause an overflow in accumulation
  # - If not, use microcodes that block only oCs (i.e. iterate all iCs) and write oCs
  # - If yes, use microcodes that block both iCs and oCs, host postproc will write oCs
  overflow_sublayers = check_fc_overflow(args)
  if len(overflow_sublayers) == 0 and (args.iC > TINIE_FC_MAX_IC_NO_HOST):
    diags.append(("WARNING", f"{layer} does not support iC larger than {TINIE_FC_MAX_IC_NO_HOST}"))
  if check_only:
    return diags
  reassure_at_codegen(diags)

  if len(overflow_sublayers) == 0:
    config_fc_no_host_postproc(args)
  else:
    config_fc_with_host_postproc(args, overflow_sublayers)


if __name__ == "__main__":
  args = parse_args()
  for item in ['iC', 'oC', 'w_packed_bits']:
    assert(args.__dict__[item] is not None), f"Please specify {item}"

  config_fc(args)
