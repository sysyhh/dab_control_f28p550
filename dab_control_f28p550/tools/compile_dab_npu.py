"""Compile the existing DAB16 candidate with TI NNC; run with its Python 3.10."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cgt", type=Path, default=Path("E:/Software_Download/ti/ccs2020/ccs/tools/compiler/ti-cgt-c2000_22.6.2.LTS"))
    parser.add_argument("--sdk", type=Path, default=Path("E:/Software_Download/ti/c2000/C2000Ware_DigitalPower_SDK_5_05_01_00/c2000ware"))
    parser.add_argument("--out", type=Path, default=APP / "model/generated/npu")
    parser.add_argument("--detail-profile", action="store_true", help="Enable intrusive stage timing; off for performance comparison")
    parser.add_argument("--optimization-level", type=int, choices=range(6), default=5,
                        help="0: original; 1: hidden identity; 2: packed transitions; 3: RAM runtime; 4: unrolled loads; 5: RAM constants")
    parser.add_argument("--skip-normalize", action="store_true",
                        help="Ask NNC 2.1.1 to prune float input normalization; kept independent of level 0-5")
    parser.add_argument("--vin-channel-quant", action="store_true",
                        help="Quantize only the live Vin channel; other inputs stay the original zero code")
    parser.add_argument("--reuse-instructions", action="store_true",
                        help="Reload NPU instructions only when the table pointer or length changes")
    parser.add_argument("--onnx", type=Path, default=None,
                        help="Existing 1x1-conv ONNX; default rebuilds the DAB16 candidate")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if args.onnx is None:
        from prepare_npu_conv import prepare
        model = prepare()
    else:
        model = args.onnx.resolve()
        if not model.exists():
            raise RuntimeError(f"Missing ONNX: {model}")
    import onnx
    from importlib.metadata import version
    nnc_version = version("ti_mcu_nnc")
    if nnc_version not in ("2.1.0", "2.1.1"):
        raise RuntimeError("This integration has only checked NNC 2.1.0/2.1.1; review the runtime and SDK contract before upgrading")
    network = onnx.load(str(model))
    onnx.checker.check_model(network)
    inp, out = network.graph.input, network.graph.output
    shape = lambda tensor: [d.dim_value for d in tensor.type.tensor_type.shape.dim]
    in_shape, out_shape = shape(inp[0]), shape(out[0])
    if len(inp) != 1 or len(out) != 1 or out_shape != [1, 1, 1, 4] or in_shape not in ([1, 16], [1, 4]):
        raise RuntimeError(f"This adapter only accepts checked DAB conv models, got {in_shape} -> {out_shape}")
    if inp[0].type.tensor_type.elem_type != 1 or out[0].type.tensor_type.elem_type != 1:
        raise RuntimeError("Adapter requires FLOAT32 model input and output")
    compiler = args.cgt.resolve() / "bin/cl2000.exe"
    if not compiler.exists() or not (args.sdk / "device_support/f28p55x/common/include/driverlib.h").exists():
        raise RuntimeError("C2000 compiler or F28P55x SDK is missing")
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out.resolve()
    includes = [args.cgt / "include", args.sdk / "driverlib/f28p55x/driverlib",
                args.sdk / "device_support/f28p55x/common/include"]
    cross = "--abi=eabi -O3 --opt_for_speed=5 --c99 -v28 -ml -mt --gen_func_subsections --float_support=fpu32 "
    cross += " ".join(f'-I{p.resolve().as_posix()}' for p in includes) + " -I."
    env = dict(os.environ)
    env.update(C2000WARE_PATH=str(args.sdk.resolve()), C2000_CGT_PATH=str(args.cgt.resolve()),
               C2000_DEVICE="f28p55x", C2000_DEVICE_FPU="fpu32", CL2000_OPTIONS=cross,
               PYTHONIOENCODING="utf-8")
    env["PATH"] = str(compiler.parent) + os.pathsep + env.get("PATH", "")
    target = "c, ti-npu skip_normalize=true" if args.skip_normalize else "c, ti-npu"
    command = [sys.executable, "-m", "tvm.driver.tvmc", "compile", f"--target={target}",
               "--target-c-mcpu=c28", str(model), "-o", str(output / "mod.a"),
               "--cross-compiler=cl2000", f"--cross-compiler-options={cross}"]
    completed = subprocess.run(command, cwd=APP, env=env, capture_output=True, text=True, errors="replace")
    (output / "compile.log").write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
    if completed.returncode:
        print(completed.stdout + completed.stderr)
        raise SystemExit(completed.returncode)
    header = output / "tvmgen_default.h"
    text = header.read_text(encoding="utf-8")
    if "#define TVMGEN_DEFAULT_TI_NPU" not in text or "#define TVMGEN_DEFAULT_TI_NPU_SOFT" in text:
        raise RuntimeError("Generated library is not a hardware-NPU model")
    tensors = re.findall(r"Tensor\[\(([^)]*)\),\s*(\w+)\]", text)
    dimensions = [([int(v.strip()) for v in dims.split(",") if v.strip()], kind) for dims, kind in tensors]
    skip_normalize_applied = False
    float_ok = (dimensions[0][1] == "float32" and dimensions[1] == ([1, 1, 1, 4], "float32")
                and dimensions[0][0] in ([1, 16], [1, 4]))
    int_abi = dimensions[0][1] in ("int8", "uint8") and dimensions[1] == ([1, 1, 1, 4], "float32")
    int_shape_ok = dimensions[0][0] in ([1, 16], [1, 16, 1, 1], [1, 4], [1, 4, 1, 1])
    if args.skip_normalize:
        if float_ok:
            skip_normalize_applied = False
        elif int_abi and int_shape_ok:
            skip_normalize_applied = True
        else:
            raise RuntimeError(f"skip_normalize produced an unexpected ABI: {dimensions}")
    elif not float_ok:
        raise RuntimeError(f"Generated ABI does not match a checked DAB adapter: {dimensions}")
    input_width = dimensions[0][0][1]
    if skip_normalize_applied and args.out.resolve() == (APP / "model/generated/npu").resolve():
        raise RuntimeError("skip_normalize integer ABI is not wired to dab_nn.c; compile to a side directory or use --vin-channel-quant")
    # A hardware macro alone is insufficient: dense graphs can fall back to CPU.
    kernel = (output / "lib2.c").read_text(encoding="utf-8")
    if kernel.count("tinie_curr_layer += 1;") != 4 or "TINIE_layer_t" not in kernel:
        raise RuntimeError("Expected four hardware-NPU convolution stages")
    runtime = output / "lib1.c"
    code = runtime.read_text(encoding="utf-8")
    if code.count("  tvmgen_default_finished = 1;") != 1:
        raise RuntimeError("Cannot locate unique final model completion")
    code = "extern void DAB_NN_noteNpuCompletion(void);\n" + code.replace(
        "  tvmgen_default_finished = 1;",
        "  DAB_NN_noteNpuCompletion(); /* Final output is ready; stamp before publication. */\n  tvmgen_default_finished = 1;")
    (output / "lib1.reference.c").write_text(code, encoding="utf-8", newline="\n")
    from patch_npu_runtime import (instrument, instrument_driver, hidden_identity, packed_transitions,
                                   ram_functions, load_unroll, ram_constants, vin_channel_quant, reuse_instructions)
    constant_symbols=[]
    if args.optimization_level >= 1:
        code = hidden_identity(code, (output / "lib0.c").read_text())
    if args.optimization_level >= 2:
        code = packed_transitions(code)
    if args.vin_channel_quant:
        code = vin_channel_quant(code)
    code = instrument(code, args.detail_profile)
    if args.optimization_level >= 3:
        names=re.findall(r'\b(tvmgen_default_\w+|dab_npu_copy_words|tinie_sublayer_IRQHandler)\([^;{}]*\)\s*\{',code)
        code=ram_functions(code,names)
        kernels=re.findall(r'\b(tvmgen_default_ti_npu_\w+)\([^;{}]*\)\s*\{',kernel)
        kernel=ram_functions(kernel,kernels)
        (output / "lib2.flash_reference.c").write_text(kernel,encoding="utf-8",newline="\n")
        if args.optimization_level >= 5:
            kernel,constant_symbols=ram_constants(kernel)
        (output / "lib2.c").write_text(kernel,encoding="utf-8", newline="\n")
    runtime.write_text(code, encoding="utf-8", newline="\n")
    import tvm
    root = Path(tvm.__file__).parent
    if args.optimization_level >= 2:
        packing=(root / "standalone_crt/include/tvm/runtime/contrib/tvm_tinie_c28.h").read_text()
        if "__byte(packed, i) = to_pack[i];" not in packing or "unpacked[i] = __byte(to_unpack, i);" not in packing:
            raise RuntimeError("Unexpected TI C28 packing semantics")
    rebuild = [str(compiler), "--compile_only", "--abi=eabi", "-O3", "--opt_for_speed=5",
               "--c99", "-v28", "-ml", "-mt", "--gen_func_subsections", "--float_support=fpu32"]
    rebuild += [f"--include_path={p.resolve()}" for p in includes + [APP, root / "3rdparty/tinie-api", root / "standalone_crt/include"]]
    subprocess.run(rebuild + [str(runtime)], cwd=output, env=env, check=True, capture_output=True)
    driver = output / "dab_tinie_c28.c"
    driver_code=instrument_driver((root / "3rdparty/tinie-api/hard/src/tinie_c28.c").read_text(), args.detail_profile)
    if args.optimization_level >= 4 and nnc_version == "2.1.0":
        driver_code=load_unroll(driver_code)
    if nnc_version == "2.1.1":
        # 保留新版 TI 的四项展开装载；不再套用仅适用于 2.1.0 的循环替换。
        if (driver_code.count('static void TINIE_mem_write(')!=1 or
                'TINIE_mem_write(params, layer->num_params, layer->params);' not in driver_code or
                'TINIE_mem_write(ins, layer->num_ins, layer->ins);' not in driver_code):
            raise RuntimeError("Unexpected NNC 2.1.1 loading implementation")
    if args.reuse_instructions:
        driver_code = reuse_instructions(driver_code)
    if args.optimization_level >= 3:
        driver_names=["TINIE_setup","TINIE_start","write_configMMR","TINIE_clearInterruptACK"]
        if nnc_version == "2.1.1": driver_names.append("TINIE_mem_write")
        driver_code=ram_functions(driver_code,driver_names)
    driver.write_text(driver_code, encoding="utf-8", newline="\n")
    result=subprocess.run(rebuild + ["--output_file=tinie_c28.obj", str(driver)], cwd=output, env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace")+result.stderr.decode(errors="replace"))
    objects=["lib1.obj", "tinie_c28.obj"]
    if args.optimization_level >= 3:
        subprocess.run(rebuild + [str(output / "lib2.c")],cwd=output,env=env,check=True,capture_output=True)
        objects.append("lib2.obj")
    subprocess.run([str(compiler.parent / "ar2000.exe"), "r", "mod.a"]+objects,
                   cwd=output, check=True, capture_output=True)
    for obj in objects: (output / obj).unlink()
    import numpy as np
    import onnxruntime as ort
    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    features = np.zeros((1, in_shape[1]), np.float32)
    features[0, 1] = np.float32(90) / np.float32(25) - np.float32(4.6)
    expected_vin90 = [float(value) for value in session.run(None, {session.get_inputs()[0].name: features})[0].ravel()]
    manifest = {"model": model.name, "model_sha256": sha(model), "ti_mcu_nnc": nnc_version,
                "target": "c, ti-npu", "cgt": str(args.cgt), "sdk": str(args.sdk), "cross_options": cross,
                "input_shape": list(in_shape), "output_shape": [1, 1, 1, 4], "io_dtype": "float32",
                "input": "features[1]=Vin/25-4.6; all other features zero; Vin 90..140 V",
                "expected_vin90_output": expected_vin90,
                "output_order": ["D1", "D0", "D2", "T"], "power_control_approved": False,
                "hardware_stages": 4, "completion_hook": "after final output dequantization, before finished=1",
                "detail_profile": args.detail_profile,
                "optimization_level": args.optimization_level,
                "skip_normalize_requested": args.skip_normalize,
                "skip_normalize_applied": skip_normalize_applied,
                "vin_channel_quant": args.vin_channel_quant,
                "reuse_instructions": args.reuse_instructions,
                "loading_implementation": "ti_2.1.1_native" if nnc_version == "2.1.1" else ("dab_unroll4" if args.optimization_level >= 4 else "ti_2.1.0_original"),
                "ram_constant_symbols": constant_symbols,
                "runtime_sha256": sha(runtime), "driver_sha256": sha(driver),
                "kernel_sha256": sha(output / "lib2.c"),
                "library_sha256": sha(output / "mod.a"), "header_sha256": sha(header)}
    (output / "dab_npu_contract.h").write_text(
        "/* Generated only after the TI NNC header ABI has been checked. */\n"
        "#ifndef DAB_NPU_CONTRACT_H_\n#define DAB_NPU_CONTRACT_H_\n"
        f"#define DAB_NPU_RUNTIME_INPUT_DIM {input_width}U\n#define DAB_NPU_RUNTIME_OUTPUT_DIM 4U\n"
        "#define DAB_NPU_MIN_VIN 90.0f\n#define DAB_NPU_MAX_VIN 140.0f\n"
        "#define DAB_NPU_POWER_CONTROL_APPROVED 0\n#endif\n", encoding="utf-8", newline="\n")
    contract=output / "dab_npu_contract.h"
    contract.write_text(contract.read_text().replace(
        "#endif",
        f"#define DAB_NPU_DETAIL_PROFILE {int(args.detail_profile)}\n"
        f"#define DAB_NPU_RAM_RUNTIME {int(args.optimization_level >= 3)}\n"
        f"#define DAB_NPU_RAM_CONSTANTS {int(args.optimization_level >= 5)}\n"
        f"#define DAB_NPU_VIN_CHANNEL_QUANT {int(args.vin_channel_quant)}\n"
        f"#define DAB_NPU_REUSE_INSTRUCTIONS {int(args.reuse_instructions)}\n#endif"),
        encoding="utf-8", newline="\n")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()


