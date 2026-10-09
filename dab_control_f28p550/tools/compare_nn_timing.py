"""Compare two paused CCS g_nnTiming JSON snapshots; no third-party packages."""
import argparse
import json
from pathlib import Path


def load(path, backend):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    data = data.get("g_nnTiming", data)
    if data.get("backend") != backend or not data.get("frozen"):
        raise ValueError(f"{path}: backend must be {backend} and frozen must be true")
    if not isinstance(data.get("timerHz"), int) or data["timerHz"] <= 0:
        raise ValueError(f"{path}: invalid timerHz")
    if data.get("rejectedOutputs", 0):
        raise ValueError(f"{path}: rejected outputs present; do not compare an invalid run")
    return data


def metric(data, name):
    stats = data[name]
    n = stats["samples"]
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"{name}: no measured samples")
    low, high, total = stats["minTicks"], stats["maxTicks"], stats["totalTicks"]
    if not (0 < low <= high and low * n <= total <= high * n):
        raise ValueError(f"{name}: inconsistent or zero timing; refresh the complete CCS snapshot")
    factor = 1_000_000 / data["timerHz"]
    return n, low * factor, total / n * factor, high * factor


def report(fpu, npu):
    names = [("FPU 前向调用", fpu, "fpuForward"),
             ("FPU 输入到结果发布", fpu, "endToEnd"),
             ("NPU 提交调用", npu, "npuSubmit"),
             ("NPU 提交到后台发现完成", npu, "npuObserved"),
             ("NPU 输入到结果发布", npu, "endToEnd")]
    if npu.get("npuCompletion", {}).get("samples", 0):
        names.insert(4, ("NPU 提交到完成通知", npu, "npuCompletion"))
    rows = ["| 测量区间 | 样本数 | 最短 μs | 平均 μs | 最长 μs |",
            "|---|---:|---:|---:|---:|"]
    for label, data, name in names:
        n, low, mean, high = metric(data, name)
        rows.append(f"| {label} | {n} | {low:.6f} | {mean:.6f} | {high:.6f} |")
    speedup = metric(fpu, "endToEnd")[2] / metric(npu, "endToEnd")[2]
    rows += ["", f"输入准备到结果发布的平均耗时比 FPU/NPU = **{speedup:.6f}**。大于 1 表示本次 NPU 路径较快，小于 1 表示较慢。",
             "", "NPU 提交时间不能当作完成时间；后台发现完成包含查询延迟，完成通知也包含运行库及中断响应时间。",
             "", "只有相同输入、相同工作负载、相同预热/样本设置且数值误差通过验证时，这个比值才有可比意义；本工具不能从计时快照独立验证模型、接线或编译条件。"]
    return "\n".join(rows) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fpu", help="FPU g_nnTiming JSON snapshot")
    parser.add_argument("npu", help="NPU g_nnTiming JSON snapshot")
    parser.add_argument("--out", help="Optional Markdown output path")
    args = parser.parse_args()
    try:
        text = report(load(args.fpu, 0), load(args.npu, 1))
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
