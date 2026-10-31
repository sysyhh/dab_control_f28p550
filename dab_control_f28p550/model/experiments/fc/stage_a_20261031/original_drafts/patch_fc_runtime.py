"""FC-only runtime patches. Do not reuse the Conv PWCONV helpers in patch_npu_runtime."""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
sys.path.insert(0, str(APP / "tools"))
from patch_npu_runtime import function, trace  # noqa: E402

IDENTITY = "tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast"
INPUT_QUANT = "tvmgen_default_fused_multiply_add_floor_clip_cast"
DEQUANT = "3.906250e-03f"
REQUANT = "2.560000e+02f"
ROUND = "5.000000e-01f"
INPUT_SCALE = "6.400000e+01f"
INPUT_WIDTH_RE = re.compile(r"for \(int32_t ax1 = 0; ax1 < (\d+); \+\+ax1\)")
PACK_WIDTH_RE = re.compile(r"for \(int32_t i = 0; i < (\d+); \+\+i\)")
CONVERT_WIDTH_RE = re.compile(r"for \(int32_t ax1 = 0; ax1 < (\d+); \+\+ax1\)")
SID_OFFSET_RE = re.compile(r"(sid_\d+_let) = \(&\(global_workspace_0_var\[(\d+)\]\)\);")

# Firmware writes features[0]=-0.5f, features[2]=0.285714f, the rest zero except Vin.
# These int8 images are floor(x*64+0.5) clipped to [-128,127] under float32.
INPUT_CONST_Q = {
    0: -32,   # floor((-0.5)*64 + 0.5) = floor(-31.5) = -32
    2: 18,    # floor(0.285714*64 + 0.5) = floor(18.785696) = 18
}


def parse_hidden_converts(code: str) -> list[dict]:
    names = [IDENTITY] + [f"{IDENTITY}_{i}" for i in range(1, 8)]
    found = []
    for name in names:
        match = re.search(r"\b" + re.escape(name) + r"\([^;{}]*\)\s*\{", code)
        if not match:
            continue
        begin = match.end()
        depth = 1
        end = begin
        while depth:
            depth += (code[end] == "{") - (code[end] == "}")
            end += 1
        body = code[begin:end - 1]
        width = CONVERT_WIDTH_RE.search(body) or re.search(r"for \(int32_t i = 0; i < (\d+); \+\+i\)", body)
        if not width:
            raise RuntimeError(f"missing hidden-convert width in {name}")
        found.append({"name": name, "width": int(width[1]), "body": body})
    if not found:
        raise RuntimeError("no FC hidden-convert functions found")
    return found


def assert_int8_identity_formula(body: str, width: int) -> None:
    if width not in (16, 29):
        raise RuntimeError(f"unexpected INT8 hidden width {width}")
    if "2.009524e-03f" in body or "2.750980e-03f" in body or "2.826416e-03f" in body:
        raise RuntimeError("INT4 hidden scales are not bit-identical; refusing the identity patch")
    already = "T_cast[i] = p0[i]" in body and "floorf(" not in body
    original = DEQUANT in body and REQUANT in body and ROUND in body and "floorf(" in body
    if not already and not original:
        raise RuntimeError("hidden convert is not the checked 1/256, ReLU, 256, floor(+0.5) form")


def hidden_identity(code: str) -> str:
    """Replace proven uint8 identity converts with a byte copy. INT8 only."""
    for item in parse_hidden_converts(code):
        assert_int8_identity_formula(item["body"], item["width"])

        def replace(body, width=item["width"]):
            assert_int8_identity_formula(body, width)
            return (
                "\n  /* uint8 0..255 已穷举：1/256 反量化、ReLU、*256 再量化与原码逐位相同。 */\n"
                f"  for (int32_t i = 0; i < {width}; ++i) T_cast[i] = p0[i];\n"
                "  return 0;\n"
            )

        code = function(code, item["name"], replace)
    return code


def pack_width(code: str, name: str) -> int:
    match = re.search(
        r"\b" + re.escape(name) + r"\([^;{}]*\)\s*\{(?:.|\n)*?for \(int32_t i = 0; i < (\d+);",
        code,
    )
    if not match:
        raise RuntimeError("missing pack loop in " + name)
    return int(match[1])


def packed_transitions(code: str) -> str:
    """Replace unpack + identity convert + pack with a C28 packed-word copy.

    Legal only because the hidden convert is a uint8 identity. The last used
    byte of an odd channel count sits in the low half of a 16-bit word; the
    high half is padding and is forced to 0, matching unpack's zero-extend
    then pack-back of the original IRQ helper buffers.
    """
    for item in parse_hidden_converts(code):
        assert_int8_identity_formula(item["body"], item["width"])
    offsets = {name: int(offset) for name, offset in SID_OFFSET_RE.findall(code)}
    if not offsets:
        raise RuntimeError("missing FC workspace sid offsets")
    for layer in (1, 2, 3):
        begin = code.index(f"case {layer}:")
        end = code.index(f"case {layer + 1}:", begin)
        block = code[begin:end]
        lines = block.splitlines()
        calls = [line.strip() for line in lines if line.strip().startswith("tvmgen_default_")]
        if len(calls) != 4:
            raise RuntimeError(f"unexpected FC layer {layer} call count {calls}")
        if "unpack" not in calls[0] or IDENTITY not in calls[1] or "pack" not in calls[2]:
            raise RuntimeError(f"unexpected FC layer {layer} CPU sequence {calls[:3]}")
        if "fullyConnectedNHWC" not in calls[3] and "fullyConnected" not in calls[3]:
            raise RuntimeError(f"layer {layer} does not end in hardware FC")
        pack_name = re.search(r"(tvmgen_default_fused_tinie_c28_pack(?:_\d+)?)", calls[2])[1]
        channels = pack_width(code, pack_name)
        if channels not in (16, 29):
            raise RuntimeError(f"unexpected packed channel count {channels}")
        words = (channels + 1) // 2
        source = re.search(r"\((sid_\d+_let),", calls[0])[1]
        destination = re.search(r"\(sid_\d+_let, (sid_\d+_let),", calls[2])[1]
        gap = abs(offsets[source] - offsets[destination])
        if source != destination and 0 < gap < words:
            raise RuntimeError(
                f"packed FC buffers overlap: {source}@{offsets[source]} -> "
                f"{destination}@{offsets[destination]} words={words}"
            )
        replaced = (
            f"  dab_npu_copy_packed((uint16_t*){source}, (uint16_t*){destination}, {channels}U);"
        )
        block = block.replace("\n".join(lines[1:4]), replaced)
        code = code[:begin] + block + code[end:]
    helper = (
        "TVM_DLL int32_t dab_npu_copy_packed(uint16_t* source, uint16_t* destination, uint16_t channels) {\n"
        "  /* C28 一个存储单元装两个 8 位通道。奇数通道的填充字节与 unpack 零扩展后再 pack 一致，强制为 0。 */\n"
        + trace("DAB_NN_traceBegin(DAB_NPU_PACK)")
        + "  uint16_t words = channels >> 1;\n"
        "  if (source != destination) {\n"
        "    for (uint16_t i = 0; i < words; ++i) destination[i] = source[i];\n"
        "  }\n"
        "  if (channels & 1U) {\n"
        "    destination[words] = (uint16_t)(source[words] & 0x00FFu);\n"
        "  }\n"
        + trace("DAB_NN_traceEnd(DAB_NPU_PACK)")
        + "  return 0;\n"
        "}\n"
    )
    marker = "void tvmgen_default_IRQHandlerHelper();"
    if code.count(marker) < 1:
        raise RuntimeError("missing IRQ helper prototype for packed copy")
    return code.replace(marker, helper + marker, 1)


def input_prequant(code: str) -> str:
    """Keep the original floor(x*64+0.5)/clip formula on Vin; constants and zeros are precomputed."""
    match = re.search(
        r"  for \(int32_t ax1 = 0; ax1 < (\d+); \+\+ax1\) \{\n"
        r"    float v_ = floorf\(\(\(p0\[ax1\] \* 6\.400000e\+01f\) \+ 5\.000000e\-01f\)\);\n"
        r"    float v__1 = \(v_\) < \(1\.270000e\+02f\) \? \(v_\) : \(1\.270000e\+02f\);\n"
        r"    T_cast\[ax1\] = \(\(int8_t\)\(\(v__1\) > \(-1\.280000e\+02f\) \? \(v__1\) : \(-1\.280000e\+02f\)\)\);\n"
        r"  \}\n",
        code,
    )
    if not match:
        raise RuntimeError("unexpected FC INT8 input quantization loop")
    width = int(match.group(1))
    if width != 16:
        raise RuntimeError(f"FC INT8 input prequant expects width 16, got {width}")
    if INPUT_QUANT not in code:
        raise RuntimeError("missing FC input quant function")
    fast = (
        "  /* 常量通道与补零通道已用原 floor(x*64+0.5) 公式预计算；Vin 仍走同一公式。 */\n"
        f"  for (int32_t ax1 = 0; ax1 < {width}; ++ax1) T_cast[ax1] = 0;\n"
        f"  T_cast[0] = (int8_t){INPUT_CONST_Q[0]};\n"
        "  {\n"
        "    float v_ = floorf(((p0[1] * 6.400000e+01f) + 5.000000e-01f));\n"
        "    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);\n"
        "    T_cast[1] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));\n"
        "  }\n"
        f"  T_cast[2] = (int8_t){INPUT_CONST_Q[2]};\n"
    )
    return code[: match.start()] + fast + code[match.end() :]
