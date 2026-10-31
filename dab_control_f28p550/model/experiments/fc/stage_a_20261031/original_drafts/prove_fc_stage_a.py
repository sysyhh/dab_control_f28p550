"""Host-side bit-exact proofs for FC stage-A patches. No board, no NNC recompile."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from patch_fc_runtime import (  # noqa: E402
    DEQUANT,
    INPUT_CONST_Q,
    REQUANT,
    ROUND,
    hidden_identity,
    input_prequant,
    packed_transitions,
    parse_hidden_converts,
)

INT8_LIB1 = HERE.parents[2] / "model/generated/fc_int8/lib1.c"
INT4_LIB1 = HERE.parents[2] / "model/generated/fc_int4/lib1.c"
RAW_INT8 = HERE / "generated/int8_zero_neuron_force_hw/lib1.c"


def dump(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    def convert(obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        raise TypeError(type(obj))

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=convert), encoding="utf-8", newline="\n")
    return path


def f32(x):
    return np.float32(x)


def hidden_formula(u: int, inv: np.float32, scale: np.float32) -> int:
    v = f32(np.int32(u)) * inv
    relu = v if v > f32(0) else f32(0)
    v1 = np.floor(relu * scale + f32(0.5))
    v2 = v1 if v1 < f32(255) else f32(255)
    v3 = v2 if v2 > f32(0) else f32(0)
    return int(np.uint8(v3))


def parse_scales(body: str) -> tuple[np.float32, np.float32]:
    inv = re.search(r"\* ([0-9.eE+\-]+)f;", body)
    scale = re.search(r"\* ([0-9.eE+\-]+)f\) \+ 5\.000000e-01f", body)
    if not inv or not scale:
        raise RuntimeError("cannot parse hidden scales")
    return f32(inv[1]), f32(scale[1])


def prove_hidden(path: Path, expect_identity: bool) -> dict:
    code = path.read_text(encoding="utf-8")
    layers = []
    all_ok = True
    for item in parse_hidden_converts(code):
        inv, scale = parse_scales(item["body"])
        mismatches = []
        for u in range(256):
            got = hidden_formula(u, inv, scale)
            if got != u:
                mismatches.append({"u": u, "got": got})
                if len(mismatches) >= 8:
                    break
        identity = not mismatches and inv * scale == f32(1)
        layers.append({
            "name": item["name"],
            "width": item["width"],
            "dequant": float(inv),
            "requant": float(scale),
            "product": float(inv * scale),
            "identity_256": identity,
            "mismatch_count": len(mismatches) if mismatches else 0,
            "mismatch_examples": mismatches[:8],
            "inline_1_over_256": DEQUANT in item["body"],
            "inline_256": REQUANT in item["body"],
            "inline_half": ROUND in item["body"],
        })
        if expect_identity and not identity:
            all_ok = False
        if not expect_identity and identity:
            all_ok = False
    patched = False
    error = None
    if expect_identity:
        try:
            hidden_identity(code)
            patched = True
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            all_ok = False
    else:
        try:
            hidden_identity(code)
            error = "INT4 identity patch unexpectedly succeeded"
            all_ok = False
        except RuntimeError:
            patched = False
    return {
        "path": str(path),
        "expect_identity": expect_identity,
        "ok": all_ok,
        "patch_applied_cleanly": patched,
        "patch_error": error,
        "layers": layers,
    }


def pack_c28(unpacked: list[int], n: int, dest: list[int] | None) -> list[int]:
    words = (n + 1) // 2
    out = list(dest if dest is not None else [0] * words)
    if len(out) < words:
        out.extend([0] * (words - len(out)))
    for i in range(n):
        value = unpacked[i] & 0xFF
        if i % 2 == 0:
            out[i // 2] = (out[i // 2] & 0xFF00) | value
        else:
            out[i // 2] = (out[i // 2] & 0x00FF) | (value << 8)
    return out[:words]


def unpack_unsigned(packed: list[int], n: int) -> list[int]:
    out = []
    for i in range(n):
        word = packed[i // 2]
        out.append(word & 0xFF if i % 2 == 0 else (word >> 8) & 0xFF)
    return out


def copy_packed(source: list[int], n: int) -> list[int]:
    words = n // 2
    out = list(source[:words])
    if n & 1:
        out.append(source[words] & 0x00FF)
    return out


def prove_pack() -> dict:
    rng = np.random.default_rng(20261031)
    cases = []
    ok = True
    for n in (1, 4, 8, 12, 16, 29, 32):
        words = (n + 1) // 2
        for dirty in (0x0000, 0xA5A5, 0xFFFF):
            packed = [int(rng.integers(0, 0x10000)) for _ in range(words + 4)]
            guard = packed[words:]
            unpacked = unpack_unsigned(packed, n)
            dest = [dirty] * (words + 4)
            packed_back = pack_c28(unpacked, n, dest)
            copied = copy_packed(packed, n)
            used = unpack_unsigned(packed_back, n) == unpacked
            pad_zero = True if (n % 2 == 0) else (copied[-1] & 0xFF00) == 0
            # Real IRQ helper: unpack zero-extends into dest, so last-word pad is 0.
            real_dest = [0] * words
            real_pack = pack_c28(unpacked, n, real_dest)
            copy_matches_real = copied == real_pack
            leftover_guard = dest[words:] == [dirty] * 4 if n % 2 == 0 else dest[words + 1:] == [dirty] * 3
            # Isolated pack into dirty dest leaves the high pad byte as dirty; that is
            # NOT the IRQ helper path. Record it so the odd-channel rule stays explicit.
            isolated_pad = packed_back[-1] & 0xFF00 if n % 2 else 0
            case_ok = used and copy_matches_real and pad_zero
            if n == 29 and dirty != 0:
                case_ok = used and copy_matches_real and pad_zero
            ok = ok and case_ok
            cases.append({
                "channels": n,
                "dirty": dirty,
                "used_bytes_roundtrip": used,
                "copy_matches_unpack_identity_pack_zero_dest": copy_matches_real,
                "odd_pad_forced_zero": pad_zero,
                "isolated_pack_pad": isolated_pad,
                "guard_intact": leftover_guard or n % 2 == 1,
                "ok": case_ok,
            })
        # Overlap / residual: copy must not read past words+odd.
        packed = [0xBEEF] * (words + 2)
        copied = copy_packed(packed, n)
        if len(copied) != words:
            ok = False
    return {"ok": ok, "cases": cases, "note": (
        "Odd last-word high byte is forced to 0 so it matches unpack zero-extend "
        "then pack in the generated IRQ helper, not a pack into dirty memory."
    )}


def orig_quant(x) -> int:
    v = np.floor(f32(x) * f32(64.0) + f32(0.5))
    v = v if v < f32(127) else f32(127)
    v = v if v > f32(-128) else f32(-128)
    return int(np.int8(v)) if v >= 0 else int(v)


def skip_normalize_quant(x) -> int:
    # NNC 2.1.1 skip_normalize: (int)((x+0.0078125)*2048)>>5, toward zero.
    return int((f32(x) + f32(0.0078125)) * f32(2048.0)) >> 5


def prequant_vector(vin: float, width: int = 16) -> list[int]:
    row = [0] * width
    row[0] = INPUT_CONST_Q[0]
    row[1] = orig_quant(f32(vin) / f32(140.0))
    row[2] = INPUT_CONST_Q[2]
    return row


def orig_vector(vin: float, width: int = 16) -> list[int]:
    x = np.zeros(width, np.float32)
    x[0] = f32(-0.5)
    x[1] = f32(vin) / f32(140.0)
    x[2] = f32(0.285714)
    return [orig_quant(v) for v in x]


def prove_input() -> dict:
    if orig_quant(-0.5) != INPUT_CONST_Q[0] or orig_quant(0.285714) != INPUT_CONST_Q[2]:
        return {"ok": False, "error": "precomputed constant codes do not match the original formula"}
    if orig_quant(0.0) != 0:
        return {"ok": False, "error": "zero does not quantize to code 0"}
    official = np.round(np.arange(90.0, 140.0 + 1e-9, 0.1), 4)
    mismatches = []
    skip_mismatches = []
    for vin in official:
        a = orig_vector(vin)
        b = prequant_vector(vin)
        if a != b:
            mismatches.append({"vin": float(vin), "orig": a[:4], "pre": b[:4]})
        vin_x = f32(vin) / f32(140.0)
        if orig_quant(vin_x) != skip_normalize_quant(vin_x):
            skip_mismatches.append(float(vin))
    # Quantization jump boundaries: vin where vin/140*64+0.5 crosses an integer.
    edges = []
    for n in range(-32, 128):
        # vin = 140 * (n - 0.5) / 64
        vin = 140.0 * (n - 0.5) / 64.0
        if 90.0 - 0.2 <= vin <= 140.0 + 0.2:
            for delta in (-1e-4, 0.0, 1e-4):
                probe = vin + delta
                if 90.0 <= probe <= 140.0:
                    a = orig_vector(probe)
                    b = prequant_vector(probe)
                    edges.append({
                        "vin": probe,
                        "code": a[1],
                        "match": a == b,
                    })
                    if a != b:
                        mismatches.append({"vin": probe, "orig": a[:4], "pre": b[:4], "edge": True})
    raw = RAW_INT8.read_text(encoding="utf-8") if RAW_INT8.is_file() else INT8_LIB1.read_text(encoding="utf-8")
    patched = input_prequant(raw)
    if "T_cast[0] = (int8_t)-32;" not in patched or "T_cast[2] = (int8_t)18;" not in patched:
        return {"ok": False, "error": "input prequant patch did not emit checked literals"}
    if "p0[1] * 6.400000e+01f" not in patched:
        return {"ok": False, "error": "Vin channel lost the original scale"}
    return {
        "ok": not mismatches,
        "points": int(len(official)),
        "mismatches": mismatches[:16],
        "skip_normalize_mismatch_count": len(skip_mismatches),
        "skip_normalize_mismatch_vins": skip_mismatches[:16],
        "skip_normalize_rejected": True,
        "constant_codes": {"feat0": INPUT_CONST_Q[0], "feat2": INPUT_CONST_Q[2], "zero": 0},
        "edge_samples": len(edges),
        "edge_mismatches": sum(1 for e in edges if not e["match"]),
        "patch_applied_cleanly": True,
    }


def simulate_layer_transition(n: int, packed: list[int]) -> dict:
    words = (n + 1) // 2
    workspace = [0xDEAD] * 80
    src = 32
    dst = 0
    workspace[src:src + len(packed)] = packed
    # Baseline: unpack to 0, identity convert to 32, pack to 0.
    unpacked = unpack_unsigned(workspace[src:], n)
    convert = list(unpacked)  # identity
    packed_out = pack_c28(convert, n, [0] * words)
    copied = copy_packed(packed[:words] if n % 2 == 0 else packed[:words], n)
    if n % 2:
        copied = copy_packed(packed, n)
    return {
        "channels": n,
        "baseline_used": unpack_unsigned(packed_out, n),
        "a2_used": unpack_unsigned(copied, n),
        "match": unpack_unsigned(packed_out, n) == unpack_unsigned(copied, n) == unpacked,
        "packed_match": packed_out == copied,
    }


def prove_intermediates() -> dict:
    rng = np.random.default_rng(7)
    rows = []
    ok = True
    for n in (16, 29):
        for _ in range(64):
            words = (n + 1) // 2
            packed = [int(rng.integers(0, 0x10000)) for _ in range(words)]
            row = simulate_layer_transition(n, packed)
            ok = ok and row["match"] and row["packed_match"]
            if len(rows) < 8:
                rows.append({k: row[k] for k in ("channels", "match", "packed_match")})
    raw = RAW_INT8.read_text(encoding="utf-8") if RAW_INT8.is_file() else INT8_LIB1.read_text(encoding="utf-8")
    a1 = hidden_identity(raw)
    a2 = packed_transitions(raw)
    a3 = input_prequant(raw)
    a4 = input_prequant(packed_transitions(hidden_identity(raw)))
    checks = {
        "a1_has_byte_copy": "T_cast[i] = p0[i]" in a1,
        "a1_keeps_pack": "fused_tinie_c28_pack_1" in a1 and "fused_tinie_c28_unpack(" in a1,
        "a2_has_copy_packed": "dab_npu_copy_packed" in a2,
        "a2_skips_hidden_calls": a2.count("fused_tinie_c28_unpack(sid_3_let") == 0,
        "a2_keeps_four_fc": a2.count("fullyConnectedNHWC_") == 4,
        "a2_keeps_output_unpack": "fused_tinie_c28_unpack_2" in a2,
        "a3_keeps_vin_formula": "p0[1] * 6.400000e+01f" in a3,
        "a4_combines": "dab_npu_copy_packed" in a4 and "T_cast[0] = (int8_t)-32;" in a4,
        "a4_still_four_fc": a4.count("fullyConnectedNHWC_") == 4,
    }
    ok = ok and all(checks.values())
    return {"ok": ok, "random_transitions": rows, "patch_checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "results/stage_a_proofs.json")
    args = parser.parse_args()
    report = {
        "int8_hidden": prove_hidden(INT8_LIB1, True),
        "int4_hidden": prove_hidden(INT4_LIB1, False),
        "packed": prove_pack(),
        "input": prove_input(),
        "intermediates": prove_intermediates(),
    }
    report["ok"] = all(report[k]["ok"] for k in ("int8_hidden", "int4_hidden", "packed", "input", "intermediates"))
    report["admit"] = {
        "A1": report["int8_hidden"]["ok"],
        "A2": report["packed"]["ok"] and report["int8_hidden"]["ok"] and report["intermediates"]["ok"],
        "A3": report["input"]["ok"],
        "INT4_A1": False,
        "skip_normalize": False,
    }
    dump(args.out, report)
    print(json.dumps({"ok": report["ok"], "admit": report["admit"], "out": str(args.out)}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
