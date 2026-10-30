"""Compile a MatMul/FC ONNX with TI NNC 2.1.1 and audit real hardware mapping.

Writes only under the directory given by --out. Refuses to touch the live
dab_control_f28p550/model/generated/npu tree. Does not rewrite MatMul as Conv,
does not patch dab_nn.c, and does not produce a CCS firmware image.
Run this file with the NNC 2.1.1 interpreter.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
LIVE_NPU = (APP / "model/generated/npu").resolve()
DEFAULT_CGT = Path("E:/Software_Download/ti/ccs2020/ccs/tools/compiler/ti-cgt-c2000_22.6.2.LTS")
DEFAULT_SDK = Path("E:/Software_Download/ti/c2000/C2000Ware_DigitalPower_SDK_5_05_01_00/c2000ware")


def sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_isolated(out: Path) -> Path:
    resolved = out.resolve()
    if resolved == LIVE_NPU or LIVE_NPU in resolved.parents:
        raise RuntimeError(f"refusing to write into the live NPU directory {LIVE_NPU}")
    return resolved


def inspect_onnx(path: Path) -> dict:
    import onnx
    from collections import Counter
    model = onnx.load(str(path))
    onnx.checker.check_model(model)
    ops = Counter(node.op_type for node in model.graph.node)
    shape = lambda tensor: [d.dim_value for d in tensor.type.tensor_type.shape.dim]
    return {
        "path": str(path),
        "ops": dict(ops),
        "matmul": int(ops.get("MatMul", 0) + ops.get("Gemm", 0)),
        "conv": int(ops.get("Conv", 0) + ops.get("ConvTranspose", 0)),
        "relu": int(ops.get("Relu", 0)),
        "pad": int(ops.get("Pad", 0) + ops.get("Concat", 0)),
        "input_shape": shape(model.graph.input[0]) if model.graph.input else [],
        "output_shape": shape(model.graph.output[0]) if model.graph.output else [],
        "node_names": [f"{node.op_type}:{node.name}" for node in model.graph.node if node.op_type in
                       ("MatMul", "Gemm", "Conv", "Relu", "Pad", "Concat")],
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def audit_dir(out: Path, onnx_info: dict, force_hw: bool, returncode: int) -> dict:
    log = read_text(out / "compile.log")
    lib0 = read_text(out / "lib0.c")
    lib1 = read_text(out / "lib1.c")
    lib2 = read_text(out / "lib2.c")
    header = read_text(out / "tvmgen_default.h")
    blob = "\n".join((log, lib0, lib1, lib2, header))
    marked = re.findall(r"INFO:ti_mcu_nnc:\s+(\S+)\s+(\[[ X]\])", log)
    offloaded = {}
    cpu_fallback = {}
    for name, mark in marked:
        bucket = offloaded if mark == "[X]" else cpu_fallback
        bucket[name] = bucket.get(name, 0) + 1
    nhwc = blob.count("TINIE_fullyConnectedNHWC") + blob.count("ti_npu_fullyConnectedNHWC")
    soft_calls = len(re.findall(r"\bTINIE_fullyConnected\s*\(", blob))
    fc_ins = sorted(set(re.findall(r"FC_iB8_oB8_kB[48]_[A-Za-z0-9_]+", blob)))
    pwconv_ins = sorted(set(re.findall(r"PWCONV_[A-Za-z0-9_]+", blob)))
    params = sorted(set(re.findall(r"\b((?:FC|PWCONV)_PARAMS(?:_\d+)?)\b", blob)))
    setup = blob.count("TINIE_setup")
    start = blob.count("TINIE_start")
    layer_inc = lib2.count("tinie_curr_layer += 1;")
    host_post = bool(re.search(r"host_postproc|w_host_postproc", blob))
    hardware_fc = nhwc > 0 and bool(fc_ins) and layer_inc > 0 and setup > 0 and start > 0
    software_fc = soft_calls > 0 and nhwc == 0
    cpu_fc = (not hardware_fc) and (not software_fc) and returncode == 0
    sizes = {name: (out / name).stat().st_size for name in
             ("lib0.c", "lib1.c", "lib2.c", "mod.a", "tvmgen_default.h", "compile.log")
             if (out / name).exists()}
    return {
        "out": str(out),
        "returncode": returncode,
        "force_no_c28_soft_offload": force_hw,
        "onnx": onnx_info,
        "header_ti_npu": bool(re.search(r"(?m)^#define TVMGEN_DEFAULT_TI_NPU$", header)),
        "header_ti_npu_soft": "#define TVMGEN_DEFAULT_TI_NPU_SOFT" in header,
        "offloaded_log": offloaded,
        "cpu_fallback_log": cpu_fallback,
        "log_fc_offloaded": offloaded.get("FC", 0),
        "log_fc_cpu": cpu_fallback.get("FC", 0),
        "log_relu_cpu": cpu_fallback.get("nn.relu", 0) + cpu_fallback.get("relu", 0) + cpu_fallback.get("Relu", 0),
        "log_pad_offloaded": offloaded.get("PAD", 0),
        "log_pad_cpu": cpu_fallback.get("PAD", 0) + cpu_fallback.get("nn.pad", 0) + cpu_fallback.get("concatenate", 0),
        "tinie_fullyConnectedNHWC": nhwc,
        "tinie_fullyConnected_soft_calls": soft_calls,
        "fc_ins_tables": fc_ins,
        "pwconv_symbols": pwconv_ins,
        "params_arrays": params,
        "tinie_setup": setup,
        "tinie_start": start,
        "tinie_layer_increments": layer_inc,
        "host_postproc": host_post,
        "hardware_fc_mapped": hardware_fc,
        "software_fc_library": software_fc,
        "cpu_generated_fc": cpu_fc,
        "conv_rewrite_detected": onnx_info.get("conv", 0) > 0 or bool(pwconv_ins),
        "iC_warnings": re.findall(r"does not support iC less than \d+", log),
        "fc_offload_info": re.findall(r"FC layer (?:NOT )?offloaded to [^\n]+", log),
        "file_bytes": sizes,
        "sha256": {name: sha(out / name) for name in sizes},
        "abi": re.findall(r"Tensor\[\(([^)]*)\),\s*(\w+)\]", header),
        "note": (
            "FC [X] in the NNC log is not hardware proof: C28 default maps "
            "TINIE_fullyConnected (software/DMAC). Hardware requires "
            "TINIE_fullyConnectedNHWC, FC_*_INS tables, and tinie_curr_layer."
        ),
    }


def compile_onnx(model: Path, out: Path, cgt: Path, sdk: Path, force_hw: bool) -> dict:
    out = assert_isolated(out)
    out.mkdir(parents=True, exist_ok=True)
    info = inspect_onnx(model)
    if info["conv"]:
        raise RuntimeError(f"ONNX still contains Conv; FC experiment forbids MatMul->Conv rewrite: {info['ops']}")
    if info["matmul"] < 1:
        raise RuntimeError(f"ONNX has no MatMul/Gemm: {info['ops']}")
    from importlib.metadata import version
    nnc_version = version("ti_mcu_nnc")
    if nnc_version not in ("2.1.0", "2.1.1"):
        raise RuntimeError(f"unexpected NNC {nnc_version}")
    compiler = cgt.resolve() / "bin/cl2000.exe"
    if not compiler.exists() or not (sdk / "device_support/f28p55x/common/include/driverlib.h").exists():
        raise RuntimeError("C2000 compiler or F28P55x SDK is missing")
    includes = [cgt / "include", sdk / "driverlib/f28p55x/driverlib",
                sdk / "device_support/f28p55x/common/include"]
    cross = "--abi=eabi -O3 --opt_for_speed=5 --c99 -v28 -ml -mt --gen_func_subsections --float_support=fpu32 "
    cross += " ".join(f"-I{p.resolve().as_posix()}" for p in includes) + " -I."
    env = dict(os.environ)
    env.update(C2000WARE_PATH=str(sdk.resolve()), C2000_CGT_PATH=str(cgt.resolve()),
               C2000_DEVICE="f28p55x", C2000_DEVICE_FPU="fpu32", CL2000_OPTIONS=cross,
               PYTHONIOENCODING="utf-8")
    env["PATH"] = str(compiler.parent) + os.pathsep + env.get("PATH", "")
    if force_hw:
        env["FORCE_NO_TI_C28_SOFT_OFFLOAD"] = "true"
    else:
        env.pop("FORCE_NO_TI_C28_SOFT_OFFLOAD", None)
    command = [sys.executable, "-m", "tvm.driver.tvmc", "compile", "--target=c, ti-npu",
               "--target-c-mcpu=c28", str(model.resolve()), "-o", str(out / "mod.a"),
               "--cross-compiler=cl2000", f"--cross-compiler-options={cross}"]
    completed = subprocess.run(command, cwd=out, env=env, capture_output=True, text=True, errors="replace")
    (out / "compile.log").write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
    report = audit_dir(out, info, force_hw, completed.returncode)
    report["ti_mcu_nnc"] = nnc_version
    report["command"] = command[:6] + [str(model.name)]
    (out / "fc_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if completed.returncode:
        report["compile_error_tail"] = (completed.stdout + completed.stderr)[-4000:]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onnx", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cgt", type=Path, default=DEFAULT_CGT)
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--force-hw", action="store_true",
                        help="Set FORCE_NO_TI_C28_SOFT_OFFLOAD=true (TI internal C28 hardware-FC flag)")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    if args.audit_only:
        previous = {}
        audit_path = args.out / "fc_audit.json"
        if audit_path.exists():
            previous = json.loads(audit_path.read_text(encoding="utf-8"))
        if args.onnx is None and not previous.get("onnx"):
            raise RuntimeError("--audit-only needs an existing fc_audit.json or --onnx")
        info = previous.get("onnx") or inspect_onnx(args.onnx)
        report = audit_dir(args.out, info, args.force_hw or bool(previous.get("force_no_c28_soft_offload")),
                           int(previous.get("returncode", 0)))
        report["ti_mcu_nnc"] = previous.get("ti_mcu_nnc")
        (args.out / "fc_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    report = compile_onnx(args.onnx, args.out, args.cgt, args.sdk, args.force_hw)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["returncode"]:
        raise SystemExit(report["returncode"])


if __name__ == "__main__":
    main()
