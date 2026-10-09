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
    parser.add_argument("--optimization-level", type=int, choices=range(2), default=1,
                        help="0: original runtime; 1: checked hidden-layer identity")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from prepare_npu_conv import prepare
    model = prepare()
    import onnx
    from importlib.metadata import version
    network = onnx.load(str(model))
    onnx.checker.check_model(network)
    inp, out = network.graph.input, network.graph.output
    shape = lambda tensor: [d.dim_value for d in tensor.type.tensor_type.shape.dim]
    if len(inp) != 1 or len(out) != 1 or shape(inp[0]) != [1, 16] or shape(out[0]) != [1, 1, 1, 4]:
        raise RuntimeError("This adapter is only for the checked DAB16 candidate, not arbitrary models")
    if inp[0].type.tensor_type.elem_type != 1 or out[0].type.tensor_type.elem_type != 1:
        raise RuntimeError("DAB16 adapter requires FLOAT32 model input and output")
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
    command = [sys.executable, "-m", "tvm.driver.tvmc", "compile", "--target=c, ti-npu",
               "--target-c-mcpu=c28", str(model), "-o", str(output / "mod.a"),
               "--cross-compiler=cl2000", f"--cross-compiler-options={cross}"]
    completed = subprocess.run(command, cwd=APP, env=env, capture_output=True, text=True, errors="replace")
    (output / "compile.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        print(completed.stdout + completed.stderr)
        raise SystemExit(completed.returncode)
    header = output / "tvmgen_default.h"
    text = header.read_text(encoding="utf-8")
    if "#define TVMGEN_DEFAULT_TI_NPU" not in text or "#define TVMGEN_DEFAULT_TI_NPU_SOFT" in text:
        raise RuntimeError("Generated library is not a hardware-NPU model")
    tensors = re.findall(r"Tensor\[\(([^)]*)\),\s*(\w+)\]", text)
    dimensions = [([int(v.strip()) for v in dims.split(",") if v.strip()], kind) for dims, kind in tensors]
    if dimensions != [([1, 16], "float32"), ([1, 1, 1, 4], "float32")]:
        raise RuntimeError(f"Generated ABI does not match the DAB16 adapter: {dimensions}")
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
    (output / "lib1.reference.c").write_text(code, encoding="utf-8")
    from patch_npu_runtime import instrument, instrument_driver, hidden_identity
    if args.optimization_level >= 1:
        code = hidden_identity(code, (output / "lib0.c").read_text())
    code = instrument(code, args.detail_profile)
    runtime.write_text(code, encoding="utf-8")
    import tvm
    root = Path(tvm.__file__).parent
    rebuild = [str(compiler), "--compile_only", "--abi=eabi", "-O3", "--opt_for_speed=5",
               "--c99", "-v28", "-ml", "-mt", "--gen_func_subsections", "--float_support=fpu32"]
    rebuild += [f"--include_path={p.resolve()}" for p in includes + [APP, root / "3rdparty/tinie-api", root / "standalone_crt/include"]]
    subprocess.run(rebuild + [str(runtime)], cwd=output, env=env, check=True, capture_output=True)
    driver = output / "dab_tinie_c28.c"
    driver.write_text(instrument_driver((root / "3rdparty/tinie-api/hard/src/tinie_c28.c").read_text(), args.detail_profile), encoding="utf-8")
    result=subprocess.run(rebuild + ["--output_file=tinie_c28.obj", str(driver)], cwd=output, env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace")+result.stderr.decode(errors="replace"))
    subprocess.run([str(compiler.parent / "ar2000.exe"), "r", "mod.a", "lib1.obj", "tinie_c28.obj"],
                   cwd=output, check=True, capture_output=True)
    (output / "lib1.obj").unlink()
    (output / "tinie_c28.obj").unlink()
    manifest = {"model": model.name, "model_sha256": sha(model), "ti_mcu_nnc": version("ti_mcu_nnc"),
                "target": "c, ti-npu", "cgt": str(args.cgt), "sdk": str(args.sdk), "cross_options": cross,
                "input_shape": [1, 16], "output_shape": [1, 1, 1, 4], "io_dtype": "float32",
                "input": "features[1]=Vin/25-4.6; all other features zero; Vin 90..140 V",
                "output_order": ["D1", "D0", "D2", "T"], "power_control_approved": False,
                "hardware_stages": 4, "completion_hook": "after final output dequantization, before finished=1",
                "detail_profile": args.detail_profile,
                "optimization_level": args.optimization_level,
                "library_sha256": sha(output / "mod.a"), "header_sha256": sha(header)}
    (output / "dab_npu_contract.h").write_text(
        "/* Generated only after the TI NNC header ABI has been checked. */\n"
        "#ifndef DAB_NPU_CONTRACT_H_\n#define DAB_NPU_CONTRACT_H_\n"
        "#define DAB_NPU_RUNTIME_INPUT_DIM 16U\n#define DAB_NPU_RUNTIME_OUTPUT_DIM 4U\n"
        "#define DAB_NPU_MIN_VIN 90.0f\n#define DAB_NPU_MAX_VIN 140.0f\n"
        "#define DAB_NPU_POWER_CONTROL_APPROVED 0\n#endif\n", encoding="utf-8")
    contract=output / "dab_npu_contract.h"
    contract.write_text(contract.read_text().replace("#endif", f"#define DAB_NPU_DETAIL_PROFILE {int(args.detail_profile)}\n#endif"), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()


