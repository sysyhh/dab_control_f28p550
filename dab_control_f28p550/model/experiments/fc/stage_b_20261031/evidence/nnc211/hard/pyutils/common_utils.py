
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
# Common utils

import os
import numpy as np


TINIE_PARAMS_BUFSIZE = 2048
TINIE_NPU_ACCUM_BITS = 18

DIAGS_CONFIG_CONV = "{in_bits}-bit input [{iH}, {iW}, {iC}], {out_bits}-bit output [{oH}, {oW}, {oC}], {w_packed_bits}-bit kernel [{kH}, {kW}], strides [{sH}, {sW}], padding [({pT}, {pB}), ({pL}, {pR})], data layout {data_layout}, kernel layout {w_layout}"
DIAGS_CONFIG_POOL = "{in_bits}-bit input [{iH}, {iW}, {iC}], {out_bits}-bit output [{oH}, {oW}, {oC}], pool [{kH}, {kW}], strides [{sH}, {sW}], padding [({pT}, {pB}), ({pL}, {pR})], layout {data_layout}"
DIAGS_CONFIG_GLOBAL_POOL = "{in_bits}-bit input [{iH}, {iW}, {iC}], {out_bits}-bit output [{oC}]"
DIAGS_CONFIG_FC = "{in_bits}-bit input [{iC}], {out_bits}-bit output [{oC}], {w_packed_bits}-bit weights"

DIAGS_IFMAP_LAYOUT = "{layer} does not support {layout} data layout. Please change to {expected_layout} data layout."
DIAGS_IFMAP_NOPADDING = "{layer} does not support padding on input. Please remove."
DIAGS_IFMAP_8BIT = "{layer} only supports 8-bit input for now. Please clip input feature map to 8-bit."
DIAGS_OFMAP_8BIT = "{layer} only supports 8-bit output for now. Please clip output feature map to 8-bit."
DIAGS_SC1_FOR_8BIT_WEIGHTS = "{layer} only supports scale value of 1 for 8-bit weights."
DIAGS_OFMAP_PAD_HEIGHT_BOTH_OR_NONE = "{layer} does not support padding [{opT}, {opB}] on output height. Padding has to be either both top and bottom or none."
DIAGS_W_LAYOUT = "{layer} does not support {layout} kernel layout. Please change to {expected_layout} kernel layout."
DIAGS_IC_M4 = "{layer} does not support {iC} input channels. Please change to multiples of 4."
DIAGS_OC_M4 = "{layer} does not support {oC} output channels. Please change to multiples of 4."
DIAGS_SH1_SW1 = "{layer} does not support strides [{sH}, {sW}]. Please change to [1, 1]."
DIAGS_UNSUPPORTED_CONFIGS = "Current {layer} implementation only supports certain layer configs. Please follow TI Neural Network Compiler for MCUs User's Guide to check supported layer configs and request support for your layer config."
DIAGS_ACCUM_OVERFLOW = "Weights and bias in this {layer} layer could potentially cause internal {accum_bits}-bit accumulator to overflow or underflow. Please use less number of bits for bias and/or reduce the size of input channels, kernel height and kernel width."


def get_parser():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--w_file', action='store',
                      default=None,
                      help='input file for weights')
  parser.add_argument('--w_data', action='store',
                      default=None,
                      help='input data (numpy) for weights')
  parser.add_argument('--w_packed_file', action='store',
                      default=None,
                      help="output file for encoded weights, in 64-bit chunks")
  parser.add_argument('--b_file', action='store',
                      default=None,
                      help='input file for bias')
  parser.add_argument('--b_data', action='store',
                      default=None,
                      help='input data (numpy) for bias')
  parser.add_argument('--b_packed_file', action='store',
                      default=None,
                      help="output file for encoded bias, in 64-bit chunks")
  parser.add_argument('--sc_file', action='store',
                      default=None,
                      help='input file for scale')
  parser.add_argument('--sc_data', action='store',
                      default=None,
                      help='input data (numpy) for scale')
  parser.add_argument('--sh_file', action='store',
                      default=None,
                      help='input file for shift')
  parser.add_argument('--sh_data', action='store',
                      default=None,
                      help='input data (numpy) for shift')
  parser.add_argument('--ss_packed_file', action='store',
                      default=None,
                      help="output file for encoded (scale,shift) pairs, in 64-bit chunks")
  parser.add_argument('--mmr_file', action='store',
                      default=None,
                      help="output file for encoded MMR")
  parser.add_argument('--ins_file', action='store',
                      default=None,
                      help="output file for selected ins filename")
  parser.add_argument('--layer_name', action='store',
                      default=None,
                      help="name of current layer being code generated")
  parser.add_argument('--prep_size_file', action='store',
                      default=None,
                      help="output file (binary) for buffer size of prepared tensor")
  parser.add_argument('--prep_code_file', action='store',
                      default=None,
                      help="output file (text) for code of preparing input tensor for FConv")
  parser.add_argument('--postproc_file', action='store',
                      default=None,
                      help="output file (binary) for storing post processing control values")
  parser.add_argument('--opt_for_space', action='store',
                      default=0, type=int,
                      help="compress NPU layer data to save rodata space")

  parser.add_argument('--iH', action='store',
                      default=None, type=int,
                      help="input feature map height (does not include ioT, ioB)")
  parser.add_argument('--iW', action='store',
                      default=None, type=int,
                      help="input feature map width")
  parser.add_argument('--iC', action='store',
                      default=None, type=int,
                      help="input feature map channels")
  parser.add_argument('--oH', action='store',
                      default=None, type=int,
                      help="output feature map height (does not include opT, opB)")
  parser.add_argument('--oW', action='store',
                      default=None, type=int,
                      help="output feature map width")
  parser.add_argument('--oC', action='store',
                      default=None, type=int,
                      help="output feature map channels")

  parser.add_argument('--kH', action='store',
                      default=None, type=int,
                      help="filter/weights kernel height")
  parser.add_argument('--kW', action='store',
                      default=None, type=int,
                      help="filter/weights kernel width")

  parser.add_argument('--pT', action='store',
                      default=None, type=int,
                      help="padding on top")
  parser.add_argument('--pB', action='store',
                      default=None, type=int,
                      help="padding on bottom")
  parser.add_argument('--pL', action='store',
                      default=None, type=int,
                      help="padding on left")
  parser.add_argument('--pR', action='store',
                      default=None, type=int,
                      help="padding on right")
  parser.add_argument('--sH', action='store',
                      default=None, type=int,
                      help="stride height")
  parser.add_argument('--sW', action='store',
                      default=None, type=int,
                      help="stride width")

  parser.add_argument('--groups', action='store',
                      default=1, type=int,
                      help="groups for convolution")
  parser.add_argument('--data_layout', action='store',
                      default="NHWC",
                      help="data layout in layer")
  parser.add_argument('--w_layout', action='store',
                      default="HWIO",
                      help="weights layout in w_file")
  parser.add_argument('--w_bits', action='store',
                      default=8, type=int,
                      help="weights bits in w_file")
  parser.add_argument('--w_packed_bits', action='store',
                      default=None, type=int,
                      help="packed weights bits in w_packed_file")
  parser.add_argument('--b_bits', action='store',
                      default=32, type=int,
                      help="bias bits in b_file")
  parser.add_argument('--b_packed_bits', action='store',
                      default=None, type=int,
                      help="packed bias bits in b_packed_file")
  parser.add_argument('--sc_bits', action='store',
                      default=32, type=int,
                      help="scale bits in sc_file")
  parser.add_argument('--sh_bits', action='store',
                      default=32, type=int,
                      help="shift bits in sh_file")
  parser.add_argument('--ss_packed_bits', action='store',
                      default=8, type=int,
                      help="packed scale/shift bits in ss_packed_file")

  parser.add_argument('--in_bits', action='store',
                      default=None, type=int,
                      help="input feature map bits")
  parser.add_argument('--in_signed', action='store',
                      default=None, type=int,
                      help="input feature map signed (1) or unsigned (0)")
  parser.add_argument('--out_bits', action='store',
                      default=None, type=int,
                      help="output feature map bits")
  parser.add_argument('--out_signed', action='store',
                      default=None, type=int,
                      help="output feature map signed (1) or unsigned (0)")
  parser.add_argument('--res_bits', action='store',
                      default=8, type=int,
                      help="residual feature map bits")
  parser.add_argument('--res_signed', action='store',
                      default=0, type=int,
                      help="residual feature map signed (1) or unsigned (0)")
  parser.add_argument('--opT', action='store',
                      default=0, type=int,
                      help="number of rows to pad on top of output feature map")
  parser.add_argument('--opB', action='store',
                      default=0, type=int,
                      help="number of rows to pad on bottom of output feature map")
  parser.add_argument('--ioT', action='store',
                      default=0, type=int,
                      help="compute starts on offset (number of rows on top) in input feature map")
  parser.add_argument('--ioB', action='store',
                      default=0, type=int,
                      help="compute ends on offset (number of rows on bottom) in input feature map")
  return parser


def parse_args(input_args=None):
  parser = get_parser()
  args = parser.parse_args(input_args)
  return args


def get_default_args():
  return parse_args(input_args=[])


def is_supported(diags):
  return not any(x[0] == "WARNING" for x in diags)


def is_supported_with_diags(diags, layer_name, ti_npu_type="TI-NPU"):
  """Check diags to see if the layer config can be supported on TI-NPU or not """
  if any(x[0] == "WARNING" for x in diags):
    res = False
    final_diags = [("WARNING", f"{layer_name} layer NOT offloaded to {ti_npu_type}")] + diags
  else:
    res = True
    final_diags = [("INFO", f"{layer_name} layer offloaded to {ti_npu_type}")] + diags
  return res, final_diags


def reassure_at_codegen(diags):
  assert(is_supported(diags)), f"Compiler internal error, please report: {diags}"


def diags_check_ifmap_layout(diags, args, expected_layout, layer):
  if args.data_layout != expected_layout:
    diags.append(("WARNING", DIAGS_IFMAP_LAYOUT.format(layer=layer, layout=args.data_layout,
                                                       expected_layout=expected_layout)))

def diags_check_ifmap_nopadding(diags, args, layer):
  if args.pT != 0 or args.pB != 0 or args.pL != 0 or args.pR != 0:
    diags.append(("WARNING", DIAGS_IFMAP_NOPADDING.format(layer=layer)))

def diags_check_ifmap_8bit(diags, args, layer):
  if args.in_bits != 8:
    diags.append(("WARNING", DIAGS_IFMAP_8BIT.format(layer=layer)))

def diags_check_scale1_if_8bit_weights(diags, args, layer):
  if args.w_packed_bits == 8:
    if args.sc_data is None:
      assert args.sc_file is not None, f"Scale file is missing"
      args.sc_data = np.fromfile(args.sc_file, dtype="int32",  count=-1, sep="")
    if not np.all(args.sc_data == 1):
      diags.append(("WARNING", DIAGS_SC1_FOR_8BIT_WEIGHTS.format(layer=layer)))

def diags_check_ofmap_pad_height_both_or_none(diags, args, layer):
  if not check_output_pad_both_or_none(args):
    diags.append(("WARNING", DIAGS_OFMAP_PAD_HEIGHT_BOTH_OR_NONE.format(layer=layer,
                             opT=args.opT, opB=args.opB)))

def diags_check_ofmap_8bit(diags, args, layer):
  if args.out_bits != 8:
    diags.append(("WARNING", DIAGS_OFMAP_8BIT.format(layer=layer)))

def diags_check_w_layout(diags, args, expected_layout, layer):
  if args.w_layout != expected_layout:
    diags.append(("WARNING", DIAGS_W_LAYOUT.format(layer=layer, layout=args.w_layout,
                                                   expected_layout=expected_layout)))

def diags_check_iC_m4(diags, args, layer):
  if args.iC % 4  != 0:
    diags.append(("WARNING", DIAGS_IC_M4.format(layer=layer, iC=args.iC)))

def diags_check_oC_m4(diags, args, layer):
  if args.oC % 4  != 0:
    diags.append(("WARNING", DIAGS_OC_M4.format(layer=layer, oC=args.oC)))

def diags_check_sH1_sW1(diags, args, layer):
  if args.sH != 1 or args.sW != 1:
    diags.append(("WARNING", DIAGS_SH1_SW1.format(layer=layer, sH=args.sH, sW=args.sW)))

def diags_unsupported_config(diags, layer):
  diags.append(("WARNING", DIAGS_UNSUPPORTED_CONFIGS.format(layer=layer)))


def get_channel_weights(args, oC):
  weights_iC = args.iC
  if args.iC == args.oC and args.groups == args.iC:   # dwconv uses weights kH x kW x oC
    weights_iC = 1
  if args.w_layout == "HWIO":
    return args.w_data.reshape(args.kH, args.kW, weights_iC, args.oC)[:,:,:,oC].flatten()
  elif args.w_layout == "HWOI":
    return args.w_data.reshape(args.kH, args.kW, args.oC, weights_iC)[:,:,oC,:].flatten()
  elif args.w_layout == "OI":
    return args.w_data.reshape(args.oC, weights_iC)[oC,:].flatten()
  else:
    assert False, f"Unsupported weights layout: {args.w_layout}"


def get_tconv_channel_weights(args, kH, kW, oC):
  """Each (kH, kW) point goes to one output point """
  if args.w_layout == "HWIO":
    return args.w_data.reshape(args.kH, args.kW, args.iC, args.oC)[kH,kW,:,oC].flatten()
  else:
    assert False, f"Unsupported TCONV weights layout: {args.w_layout}"


def get_channel_bias(args, oC):
  f_b_data = args.b_data.flatten()
  return f_b_data[oC % len(f_b_data)]


def get_indata_min_max(args):
  if args.in_signed == 1:
    d_min, d_max = -(2**(args.in_bits-1)), 2**(args.in_bits-1) - 1
  else:
    d_min, d_max =                      0, 2**args.in_bits - 1
  return d_min, d_max


def get_num_reserve_bytes(num_bias_prefetches, sublayer_oCs):
  """returns the number of bytes read from tinie param buffer memory beyond the scale-shift region
     tinie param buffer memory is laid out as: weights -> biases -> scale-shift(s)
     each bias prefetch loads 64 bits
  """
  return max(0, (num_bias_prefetches - sublayer_oCs//4)*8)


def check_accum_overflow_lane(w_lane, d_min, d_max, tmaout_min, tmaout_max, lane, accum_bits):
  accum_min = - (1 << (accum_bits - 1))
  accum_max =   (1 << (accum_bits - 1)) - 1
  if (w_lane > 0):
    tmaout_min[lane] += w_lane * d_min
    tmaout_max[lane] += w_lane * d_max
  else:
    tmaout_min[lane] += w_lane * d_max
    tmaout_max[lane] += w_lane * d_min
  if tmaout_max[lane] > accum_max:
    return True
  if tmaout_min[lane] < accum_min:
    return True
  return False


def check_accum_overflow_kB4(w_val, d_min, d_max, tmaout_min, tmaout_max,
                             accum_bits=TINIE_NPU_ACCUM_BITS):
  for lane in range(2):
    w_lane = np.bitwise_and(np.right_shift(w_val, np.int8(lane*2)), np.int8(3)).item()
    if lane == 1:
      w_lane = -1 if (w_lane == 3) else (-2 if (w_lane == 2) else w_lane)
    if check_accum_overflow_lane(w_lane, d_min, d_max, tmaout_min, tmaout_max, lane, accum_bits):
      return True
  return False


def check_accum_overflow_kB8(w_val, d_min, d_max, tmaout_min, tmaout_max,
                             accum_bits=TINIE_NPU_ACCUM_BITS):
  for lane in range(4):
    w_lane = np.bitwise_and(np.right_shift(w_val, np.int8(lane*2)), np.int8(3)).item()
    if lane == 3:
      w_lane = -1 if (w_lane == 3) else (-2 if (w_lane == 2) else w_lane)
    if check_accum_overflow_lane(w_lane, d_min, d_max, tmaout_min, tmaout_max, lane, accum_bits):
      return True
  return False


def get_all_24b_bias_splits(ch_b):
  """ return a list of valid (unsigned b_lane0, signed b_lane3) splits for a 24b bias value
    24b signed value is split such that: bias = (b_lane3 << 6) + b_lane0
    b_lane0 and be_lane3 can be up to 16 bits each for a combined 24 bits
    So, the valid splits are 16:8, 15:9, 14:10, 13:11, 12:12, ..., 9:15, 8:16.
    Examples:
    bias = -1
      - 16:8  split: -1 = ((-1 << 10) << 6) + 0xFFFF = (-1024 << 6) + 65535
      - 15:9  split: -1 = ((-1 <<  9) << 6) + 0x7FFF = ( -512 << 6) + 32767
      - 12:12 split: -1 = ((-1 <<  6) << 6) +  0xFFF = (  -64 << 6) +  4095
    bias = 0x7FFFFF (8388607)
      - 16:8  split: = ((0x7F << 10) << 6) + 0xFFFF = (130048 << 6) + 65535
      - 15:9  split: = ((0xFF <<  9) << 6) + 0x7FFF = (130560 << 6) + 32767
    bias = 0x800000 (-8388608)
      - 16:8  split: = ((-0x80 << 10) << 6) + 0x0000 = (-131072 << 6) + 0
      - 15:9  split: = ((-0x100 << 9) << 6) + 0x0000 = (-131072 << 6) + 0
    bias = 0x1F0FF (127231)
      - 16:8  split: = ((0x1 << 10) << 6) + 0xF0FF = (1024 << 6) + 61695
      - 12:12 split: = ((0x1f << 6) << 6) + 0x0FF  = (1984 << 6) + 255
    bias = 0x780FF (491775)
      - 16:8  split: = ((0x7 << 10) << 6) + 0x80FF = (7168 << 6) + 33023
      - 15:9  split: = ((0xF <<  9) << 6) + 0x00FF = (7680 << 6) + 255
  """

  splits = []
  for lane3_mask, lane0_mask in [   (0x00FF0000, 0x0000FFFF), (0x00FF8000, 0x00007FFF),
          (0x00FFC000, 0x00003FFF), (0x00FFE000, 0x00001FFF), (0x00FFF000, 0x00000FFF),
          (0x00FFF800, 0x000007FF), (0x00FFFC00, 0x000003FF), (0x00FFFE00, 0x000001FF),
          (0x00FFFF00, 0x000000FF) ]:
    b_lane0 = np.bitwise_and(ch_b, np.int32(lane0_mask)).item()
    b_lane3 = np.right_shift(np.left_shift(np.bitwise_and(ch_b, np.int32(lane3_mask)),
                                           np.int32(8)), np.int32(14)).item()
    assert ch_b.item() == (b_lane3 << 6) + b_lane0, f"Bias split error should not happen"
    splits.append( (b_lane0, b_lane3) )
  return splits


def check_npu_accum_overflow(args, ch, d_min, d_max, ch_w, ch_b, accum_bits=TINIE_NPU_ACCUM_BITS):
  if args.w_packed_bits == 8 and accum_bits == TINIE_NPU_ACCUM_BITS:  # TI-NPU 8b weights
    # try all possible splits for 24b bias until we find one without causing overflow
    for b_lane0, b_lane3 in get_all_24b_bias_splits(ch_b):
      overflow = False
      tmaout_min = [b_lane0, 0, 0, b_lane3]  # possible accumulated minimum in a TMAout reg
      tmaout_max = [b_lane0, 0, 0, b_lane3]  # possible accumulated maximum in a TMAout reg
      for w_val in ch_w:
        if check_accum_overflow_kB8(w_val, d_min, d_max, tmaout_min, tmaout_max, accum_bits):
          overflow = True
          break
      if not overflow:
        args.b_24b_split[ch] = (b_lane0, b_lane3)
        break
    return overflow
  elif args.w_packed_bits == 4:
    tmaout_min = [0, ch_b.item()]
    tmaout_max = [0, ch_b.item()]
    for w_val in ch_w:
      if check_accum_overflow_kB4(w_val, d_min, d_max, tmaout_min, tmaout_max, accum_bits):
        return True
  elif args.w_packed_bits == 2 or args.w_packed_bits == 8:  # TI-NPU 2b or M33CDE 2b/8b weights
    tmaout_min = [ch_b.item()]
    tmaout_max = [ch_b.item()]
    for w_val in ch_w:
      if check_accum_overflow_lane(w_val.item(), d_min, d_max, tmaout_min, tmaout_max,
                                   0, accum_bits):
        return True
  return False


def diags_check_conv_accum_overflow(diags, args, layer, with_bias=True,
                                    accum_bits=TINIE_NPU_ACCUM_BITS, is_tconv=False):
  if args.w_data is None or args.b_data is None:
    if args.w_file is not None and args.b_file is not None:
      args.w_data = np.fromfile(args.w_file, dtype="int8",  count=-1, sep="")
      args.b_data = np.fromfile(args.b_file, dtype="int32", count=-1, sep="")
    else:
      return

  # For 24-bit bias on TI-NPU, search and record split decision that won't cause overflow
  if args.w_packed_bits == 8 and accum_bits == TINIE_NPU_ACCUM_BITS:
    args_dict = vars(args)
    args_dict['b_24b_split'] = [(0, 0)] * args.oC

  d_min, d_max = get_indata_min_max(args)
  if is_tconv:
    for kH in range(args.kH):
      for kW in range(args.kW):
        for oC in range(args.oC):
          ch_w = get_tconv_channel_weights(args, kH, kW, oC)
          ch_b = get_channel_bias(args, oC) if with_bias else np.int32(0)
          if check_npu_accum_overflow(args, oC, d_min, d_max, ch_w, ch_b, accum_bits=accum_bits):
            diags.append(("WARNING", DIAGS_ACCUM_OVERFLOW.format(layer=layer,
                                                                 accum_bits=accum_bits)))
            return
  else:
    for oC in range(args.oC):
      ch_w = get_channel_weights(args, oC)
      ch_b = get_channel_bias(args, oC) if with_bias else np.int32(0)
      if check_npu_accum_overflow(args, oC, d_min, d_max, ch_w, ch_b, accum_bits=accum_bits):
        diags.append(("WARNING", DIAGS_ACCUM_OVERFLOW.format(layer=layer, accum_bits=accum_bits)))
        return


def get_ins_generic(args, ins):
  with open(args.ins_file, 'w') as f:
    f.write(f"{ins}\n")


def check_1d_stride(args):
  if (args.sH == 1 and args.sW == 1):
    return True
  return (args.sH > 1 and args.iW == 1) or (args.sW > 1 and args.iH == 1)


def check_output_pad_both_or_none(args):
  return (args.opT > 0 and args.opB > 0) or (args.opT == 0 and args.opB == 0)


def check_input_no_pad(args):
  return (args.pT == 0 and args.pB == 0 and args.pL == 0 and args.pR == 0)


def check_output_no_padH(args):
  return (args.opT == 0 and args.opB == 0)

def check_input_no_offsetTB(args):
  return (args.ioT == 0 and args.ioB == 0)


def save_args_out_filenames(args):
  args_dict = vars(args)
  args_dict['orig_w_packed_file'] = args.w_packed_file
  args_dict['orig_b_packed_file'] = args.b_packed_file
  args_dict['orig_ss_packed_file'] = args.ss_packed_file
  args_dict['orig_mmr_file'] = args.mmr_file


def set_args_sublayer_out_filenames(args, sublayer):
  suffix = "" if sublayer == 0 else f"_sub{sublayer}"
  args.w_packed_file = args.orig_w_packed_file + suffix
  args.b_packed_file = args.orig_b_packed_file + suffix
  args.ss_packed_file = args.orig_ss_packed_file + suffix
  args.mmr_file = args.orig_mmr_file + suffix


def restore_args_out_filenames(args):
  args.w_packed_file = args.orig_w_packed_file
  args.b_packed_file = args.orig_b_packed_file
  args.ss_packed_file = args.orig_ss_packed_file
  args.mmr_file = args.orig_mmr_file


def block_output_channels(args, num_oC, oC_block_size, w_bytes, b_bytes, ss_bytes,
                          must_block=True, num_bias_prefetches=0):
  per_block_bytes = w_bytes + b_bytes + ss_bytes
  num_oC_blocks = num_oC // oC_block_size
  while (num_oC_blocks * per_block_bytes > TINIE_PARAMS_BUFSIZE - \
         get_num_reserve_bytes(num_bias_prefetches, num_oC_blocks*oC_block_size)):
    num_oC_blocks -= 1
  if (num_oC_blocks == 0):
    if must_block:
      assert False, \
"Minimum params block of {per_block_bytes} bytes exceeded TI-NPU memory limit {TINIE_PARAMS_BUFSIZE}"
    num_sublayers = 0
  else:
    oC_block_size_per_sublayer = num_oC_blocks * oC_block_size
    num_sublayers = (num_oC + (oC_block_size_per_sublayer-1)) // oC_block_size_per_sublayer
  if os.environ.get("TINIE_COMPILE_DEBUG", None):
    print(f"Params per_block: {oC_block_size} channels, "
          f"{w_bytes} (w) + {b_bytes} (b) + {ss_bytes} (ss) = {per_block_bytes} bytes, "
          f"per_sublayer: {num_oC_blocks} blocks, num sublayers: {num_sublayers}")
  return num_sublayers, num_oC_blocks

