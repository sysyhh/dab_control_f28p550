import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
run = data["runs"][0]
timing = run["timing"]
print("label", data.get("label"))
print("ok", data.get("ok"), "runs", len(data["runs"]))
print("output", run["output"])
manifest = data.get("model_manifest") or {}
print("vin_channel_quant", manifest.get("vin_channel_quant"),
      "reuse_instructions", manifest.get("reuse_instructions"),
      "detail_profile", manifest.get("detail_profile"),
      "optimization_level", manifest.get("optimization_level"))
print("instrumented", run["detail"]["instrumented"], "lastCalls", run["detail"]["lastCalls"])
print("checks_all", all(run["checks"].values()))
keys = ["prepare", "fpuForward", "npuSubmit", "npuCompletion", "npuObserved", "publish", "endToEnd"]
for key in keys:
    stats = timing[key]
    if stats["samples"] == 0:
        continue
    print(f"{key:16} mean={stats['meanUs']:.6f} minUs={stats['minTicks']/150:.6f} maxUs={stats['maxTicks']/150:.6f} n={stats['samples']}")
if run["detail"]["instrumented"]:
    names = run["detail"]["stage_names"]
    for index, name in enumerate(names):
        stats = run["detail"]["stage"][index]
        print(f"  stage[{index:2}] {name:22} mean={stats['meanUs']:.6f} n={stats['samples']}")
