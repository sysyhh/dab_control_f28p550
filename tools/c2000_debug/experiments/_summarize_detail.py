import json
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "benchmarks/20261030_155833_exp0_npu_detail/summary.json"
d = json.loads(p.read_text(encoding="utf-8"))
r = d["runs"][0]
t = r["timing"]
print("DETAIL library fields (not official speed):")
for k in ["prepare", "npuSubmit", "npuCompletion", "npuObserved", "publish", "endToEnd"]:
    s = t[k]
    print(f"  {k:14} mean={s['meanUs']:.5f} min={s['minTicks']/150:.5f} max={s['maxTicks']/150:.5f} n={s['samples']}")
print("instrumented", r["detail"]["instrumented"], "calls", r["detail"]["lastCalls"])
names = r["detail"]["stage_names"]
for i, name in enumerate(names):
    s = r["detail"]["stage"][i]
    print(f"  stage[{i:2}] {name:22} mean={s['meanUs']:.5f} n={s['samples']}")
cpu = sum(r["detail"]["stage"][i]["meanUs"] for i in range(7)) + r["detail"]["stage"][11]["meanUs"]
wait = sum(r["detail"]["stage"][i]["meanUs"] for i in range(7, 11))
print("cpu_stages_sum", round(cpu, 5), "wait_stages_sum", round(wait, 5))
