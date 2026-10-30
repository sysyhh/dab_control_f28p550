"""Clone the LaunchPad NPU FLASH makefile tree into isolated FC test builds.

Does not modify CPU1_LAUNCHXL_NPU_FLASH or model/generated/npu.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
SRC = APP / "CPU1_LAUNCHXL_NPU_FLASH"
IGNORE = shutil.ignore_patterns(
    "*.obj", "*.out", "*.map", "*.d", "*.d_raw", "*linkInfo.xml",
    "dab_nn_auto_benchmark.opt", ".clangd",
)


def clone(name: str, define: str, library: str) -> Path:
    dst = APP / name
    if not SRC.is_dir() or not (SRC / "makefile").is_file():
        raise FileNotFoundError(f"missing CCS NPU makefile tree {SRC}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst, ignore=IGNORE)
    replacements = (
        ("CPU1_LAUNCHXL_NPU_FLASH", name),
        ("DAB_NPU_DAB16_MODEL", define),
        ("model/generated/npu/mod.a", library),
        ("model\\generated\\npu\\mod.a", library.replace("/", "\\")),
    )
    for path in dst.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
    if define not in (dst / "makefile").read_text(encoding="utf-8"):
        raise RuntimeError(f"failed to inject {define} into {dst / 'makefile'}")
    if "DAB_NPU_DAB16_MODEL" in (dst / "makefile").read_text(encoding="utf-8"):
        raise RuntimeError(f"{dst} still references DAB_NPU_DAB16_MODEL")
    if "generated/npu/mod.a" in (dst / "makefile").read_text(encoding="utf-8"):
        raise RuntimeError(f"{dst} still links the live NPU archive")
    return dst


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("int8", "int4", "all"), default="all")
    args = parser.parse_args()
    jobs = []
    if args.variant in ("int8", "all"):
        jobs.append(("CPU1_LAUNCHXL_FC_INT8_FLASH", "DAB_NPU_FC_INT8",
                     "model/generated/fc_int8/mod.a"))
    if args.variant in ("int4", "all"):
        jobs.append(("CPU1_LAUNCHXL_FC_INT4_FLASH", "DAB_NPU_FC_INT4",
                     "model/generated/fc_int4/mod.a"))
    for name, define, library in jobs:
        path = clone(name, define, library)
        print(path)


if __name__ == "__main__":
    main()
