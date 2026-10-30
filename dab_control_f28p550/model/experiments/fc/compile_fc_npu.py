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
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
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


def native_features(vin: float, width: int):
    import numpy as np
    features = np.zeros((1, width), np.float32)
    features[0, 0] = np.float32(-0.5)
    features[0, 1] = np.float32(vin) / np.float32(140.0)
    features[0, 2] = np.float32(0.285714)
    return features


def package_firmware(src: Path, out: Path, cgt: Path, sdk: Path, detail: bool,
                     reuse: bool, optimization_level: int, onnx: Path | None) -> dict:
    src = src.resolve()
    out = assert_isolated(out)
    if not (src / "lib1.c").is_file() or not (src / "lib2.c").is_file():
        raise RuntimeError(f"missing generated FC sources in {src}")
    if src != out:
        out.mkdir(parents=True, exist_ok=True)
        for name in ("lib0.c", "lib1.c", "lib2.c", "tvmgen_default.h", "compile.log", "fc_audit.json", "mod.a"):
            if (src / name).is_file():
                shutil.copy2(src / name, out / name)
    audit = json.loads((out / "fc_audit.json").read_text(encoding="utf-8")) if (out / "fc_audit.json").is_file() else {}
    if not audit.get("hardware_fc_mapped"):
        raise RuntimeError("refusing to package a library without hardware FC mapping")
    if audit.get("software_fc_library") or audit.get("cpu_generated_fc") or audit.get("tinie_fullyConnected_soft_calls"):
        raise RuntimeError("refusing to package a library with CPU/software FC fallback")
    header = (out / "tvmgen_default.h").read_text(encoding="utf-8")
    if "#define TVMGEN_DEFAULT_TI_NPU" not in header or "#define TVMGEN_DEFAULT_TI_NPU_SOFT" in header:
        raise RuntimeError("Generated library is not a hardware-NPU model")
    tensors = re.findall(r"Tensor\[\(([^)]*)\),\s*(\w+)\]", header)
    dimensions = [([int(v.strip()) for v in dims.split(",") if v.strip()], kind) for dims, kind in tensors]
    if not dimensions or dimensions[0][1] != "float32" or dimensions[0][0][0] != 1:
        raise RuntimeError(f"unexpected FC ABI {dimensions}")
    input_width = dimensions[0][0][1]
    if input_width not in (8, 16):
        raise RuntimeError(f"FC firmware adapter only accepts input width 8 or 16, got {input_width}")
    kernel = (out / "lib2.c").read_text(encoding="utf-8")
    nhwc = "TINIE_fullyConnectedNHWC" in kernel or "ti_npu_fullyConnectedNHWC" in kernel
    if kernel.count("tinie_curr_layer += 1;") != 4 or not nhwc:
        raise RuntimeError("Expected four hardware-NPU FC stages")
    if re.search(r"\bTINIE_fullyConnected\s*\(", kernel):
        raise RuntimeError("Generated kernel still contains software TINIE_fullyConnected")
    runtime = out / "lib1.c"
    code = runtime.read_text(encoding="utf-8")
    if code.count("  tvmgen_default_finished = 1;") != 1:
        raise RuntimeError("Cannot locate unique final model completion")
    if "DAB_NN_noteNpuCompletion" not in code:
        code = "extern void DAB_NN_noteNpuCompletion(void);\n" + code.replace(
            "  tvmgen_default_finished = 1;",
            "  DAB_NN_noteNpuCompletion(); /* Final output is ready; stamp before publication. */\n  tvmgen_default_finished = 1;")
    sys.path.insert(0, str(APP / "tools"))
    from patch_npu_runtime import instrument, instrument_driver, ram_functions, ram_constants, reuse_instructions
    constant_symbols = []
    code = instrument(code, detail)
    if optimization_level >= 3:
        names = re.findall(r'\b(tvmgen_default_\w+|dab_npu_copy_words|tinie_sublayer_IRQHandler)\([^;{}]*\)\s*\{', code)
        code = ram_functions(code, names)
        kernels = re.findall(r'\b(tvmgen_default_ti_npu_\w+)\([^;{}]*\)\s*\{', kernel)
        kernel = ram_functions(kernel, kernels)
        (out / "lib2.flash_reference.c").write_text(kernel, encoding="utf-8", newline="\n")
        if optimization_level >= 5:
            kernel, constant_symbols = ram_constants(kernel)
        (out / "lib2.c").write_text(kernel, encoding="utf-8", newline="\n")
    runtime.write_text(code, encoding="utf-8", newline="\n")
    from importlib.metadata import version
    nnc_version = version("ti_mcu_nnc")
    import tvm
    root = Path(tvm.__file__).parent
    compiler = cgt.resolve() / "bin/cl2000.exe"
    includes = [cgt / "include", sdk / "driverlib/f28p55x/driverlib",
                sdk / "device_support/f28p55x/common/include"]
    env = dict(os.environ)
    env.update(C2000WARE_PATH=str(sdk.resolve()), C2000_CGT_PATH=str(cgt.resolve()),
               C2000_DEVICE="f28p55x", C2000_DEVICE_FPU="fpu32", PYTHONIOENCODING="utf-8")
    env["PATH"] = str(compiler.parent) + os.pathsep + env.get("PATH", "")
    rebuild = [str(compiler), "--compile_only", "--abi=eabi", "-O3", "--opt_for_speed=5",
               "--c99", "-v28", "-ml", "-mt", "--gen_func_subsections", "--float_support=fpu32"]
    rebuild += [f"--include_path={p.resolve()}" for p in includes + [APP, root / "3rdparty/tinie-api", root / "standalone_crt/include"]]
    subprocess.run(rebuild + [str(runtime)], cwd=out, env=env, check=True, capture_output=True)
    driver = out / "dab_tinie_c28.c"
    driver_code = instrument_driver((root / "3rdparty/tinie-api/hard/src/tinie_c28.c").read_text(), detail)
    if nnc_version == "2.1.1":
        if (driver_code.count('static void TINIE_mem_write(') != 1 or
                'TINIE_mem_write(params, layer->num_params, layer->params);' not in driver_code or
                'TINIE_mem_write(ins, layer->num_ins, layer->ins);' not in driver_code):
            raise RuntimeError("Unexpected NNC 2.1.1 loading implementation")
    if reuse:
        driver_code = reuse_instructions(driver_code)
    if optimization_level >= 3:
        driver_names = ["TINIE_setup", "TINIE_start", "write_configMMR", "TINIE_clearInterruptACK"]
        if nnc_version == "2.1.1":
            driver_names.append("TINIE_mem_write")
        driver_code = ram_functions(driver_code, driver_names)
    driver.write_text(driver_code, encoding="utf-8", newline="\n")
    result = subprocess.run(rebuild + ["--output_file=tinie_c28.obj", str(driver)], cwd=out, env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace"))
    objects = ["lib1.obj", "tinie_c28.obj"]
    if optimization_level >= 3:
        subprocess.run(rebuild + [str(out / "lib2.c")], cwd=out, env=env, check=True, capture_output=True)
        objects.append("lib2.obj")
    subprocess.run([str(compiler.parent / "ar2000.exe"), "r", "mod.a"] + objects, cwd=out, check=True, capture_output=True)
    for obj in objects:
        (out / obj).unlink(missing_ok=True)
    expected_vin90 = None
    model_name = None
    model_sha = None
    in_shape = [1, input_width]
    if onnx is not None and onnx.is_file():
        import numpy as np
        import onnxruntime as ort
        session = ort.InferenceSession(str(onnx), providers=["CPUExecutionProvider"])
        features = native_features(90.0, input_width)
        expected_vin90 = [float(value) for value in session.run(None, {session.get_inputs()[0].name: features})[0].ravel()]
        model_name = onnx.name
        model_sha = sha(onnx)
        in_shape = list(session.get_inputs()[0].shape)
    manifest = {
        "kind": "native_3input_fc",
        "model": model_name,
        "model_sha256": model_sha,
        "source_generated": str(src),
        "ti_mcu_nnc": nnc_version,
        "force_no_c28_soft_offload": True,
        "input_shape": in_shape,
        "output_shape": [1, 4],
        "io_dtype": "float32",
        "input": "features[0]=-0.5; features[1]=Vin/140; features[2]=0.285714; remaining channels zero; no Vin fold",
        "expected_vin90_output": expected_vin90,
        "output_order": ["D1", "D0", "D2", "T"],
        "power_control_approved": False,
        "hardware_stages": 4,
        "completion_hook": "after final output dequantization, before finished=1",
        "detail_profile": detail,
        "optimization_level": optimization_level,
        "vin_channel_quant": False,
        "reuse_instructions": reuse,
        "hidden_identity": False,
        "packed_transitions": False,
        "ram_constant_symbols": constant_symbols,
        "runtime_sha256": sha(runtime),
        "driver_sha256": sha(driver),
        "kernel_sha256": sha(out / "lib2.c"),
        "library_sha256": sha(out / "mod.a"),
        "header_sha256": sha(out / "tvmgen_default.h"),
        "hardware_fc_mapped": True,
        "fc_ins_tables": audit.get("fc_ins_tables"),
        "tinie_layer_increments": audit.get("tinie_layer_increments"),
        "tinie_fullyConnectedNHWC": audit.get("tinie_fullyConnectedNHWC"),
    }
    (out / "dab_npu_contract.h").write_text(
        "/* Generated only after the TI NNC header ABI has been checked. */\n"
        "#ifndef DAB_NPU_CONTRACT_H_\n#define DAB_NPU_CONTRACT_H_\n"
        f"#define DAB_NPU_RUNTIME_INPUT_DIM {input_width}U\n#define DAB_NPU_RUNTIME_OUTPUT_DIM 4U\n"
        "#define DAB_NPU_MIN_VIN 90.0f\n#define DAB_NPU_MAX_VIN 140.0f\n"
        "#define DAB_NPU_POWER_CONTROL_APPROVED 0\n"
        f"#define DAB_NPU_DETAIL_PROFILE {int(detail)}\n"
        f"#define DAB_NPU_RAM_RUNTIME {int(optimization_level >= 3)}\n"
        f"#define DAB_NPU_RAM_CONSTANTS {int(optimization_level >= 5)}\n"
        "#define DAB_NPU_VIN_CHANNEL_QUANT 0\n"
        f"#define DAB_NPU_REUSE_INSTRUCTIONS {int(reuse)}\n"
        "#define DAB_NPU_NATIVE_THREE_INPUT 1\n#endif\n",
        encoding="utf-8", newline="\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onnx", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cgt", type=Path, default=DEFAULT_CGT)
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--force-hw", action="store_true",
                        help="Set FORCE_NO_TI_C28_SOFT_OFFLOAD=true (TI internal C28 hardware-FC flag)")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--package-firmware", action="store_true",
                        help="Rebuild mod.a with completion hook, RAM runtime, and FC contract; never writes live npu/")
    parser.add_argument("--src", type=Path, default=None, help="Existing NNC output to package")
    parser.add_argument("--detail-profile", action="store_true")
    parser.add_argument("--reuse-instructions", action="store_true")
    parser.add_argument("--optimization-level", type=int, choices=range(6), default=5)
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
    if args.package_firmware:
        src = args.src or args.out
        if args.onnx is not None and not (Path(src) / "lib1.c").is_file():
            report = compile_onnx(args.onnx, src, args.cgt, args.sdk, True)
            if report["returncode"]:
                print(json.dumps(report, ensure_ascii=False, indent=2))
                raise SystemExit(report["returncode"])
        manifest = package_firmware(src, args.out, args.cgt, args.sdk, args.detail_profile,
                                    args.reuse_instructions, args.optimization_level, args.onnx)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    report = compile_onnx(args.onnx, args.out, args.cgt, args.sdk, args.force_hw)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["returncode"]:
        raise SystemExit(report["returncode"])


if __name__ == "__main__":
    main()
