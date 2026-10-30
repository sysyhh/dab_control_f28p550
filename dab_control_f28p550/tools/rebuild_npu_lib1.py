"""Recompile patched lib1.c into the existing NPU archive. Does not re-run NNC."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import tvm

APP = Path(__file__).resolve().parents[1]
output = APP / "model/generated/npu"
cgt = Path("E:/Software_Download/ti/ccs2020/ccs/tools/compiler/ti-cgt-c2000_22.6.2.LTS")
sdk = Path("E:/Software_Download/ti/c2000/C2000Ware_DigitalPower_SDK_5_05_01_00/c2000ware")
compiler = cgt / "bin/cl2000.exe"
root = Path(tvm.__file__).parent
includes = [cgt / "include", sdk / "driverlib/f28p55x/driverlib",
            sdk / "device_support/f28p55x/common/include", APP,
            root / "3rdparty/tinie-api", root / "standalone_crt/include"]
cmd = [str(compiler), "--compile_only", "--abi=eabi", "-O3", "--opt_for_speed=5", "--c99",
       "-v28", "-ml", "-mt", "--gen_func_subsections", "--float_support=fpu32"]
cmd += [f"--include_path={path.resolve()}" for path in includes]
result = subprocess.run(cmd + [str(output / "lib1.c")], cwd=output, capture_output=True, text=True, errors="replace")
(output / "lib1_rebuild.log").write_text(result.stdout + result.stderr, encoding="utf-8")
if result.returncode:
    print(result.stdout + result.stderr)
    raise SystemExit(result.returncode)
archive = subprocess.run([str(cgt / "bin/ar2000.exe"), "r", "mod.a", "lib1.obj"],
                         cwd=output, capture_output=True, text=True, errors="replace")
if archive.returncode:
    print(archive.stdout + archive.stderr)
    raise SystemExit(archive.returncode)
(output / "lib1.obj").unlink(missing_ok=True)
manifest_path = output / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["runtime_sha256"] = hashlib.sha256((output / "lib1.c").read_bytes()).hexdigest()
manifest["library_sha256"] = hashlib.sha256((output / "mod.a").read_bytes()).hexdigest()
manifest["isr_cpu_timing"] = True
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"ok": True, "library_sha256": manifest["library_sha256"],
                  "runtime_sha256": manifest["runtime_sha256"]}, indent=2))
