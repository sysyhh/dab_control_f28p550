"""Executable final checks; board measurements are deliberately not inferred."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]/"dab_control_f28p550"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

project=ET.parse(APP/".cproject")
configs=project.findall("./storageModule/cconfiguration")
assert len(configs)==5
for config in configs:
    assert "model/generated" in config.find(".//sourceEntries/entry").get("excluding")
npu=next(c for c in configs if c.find("storageModule").get("name")=="CPU1_LAUNCHXL_NPU_FLASH")
def options(suffix):
    option=next(o for o in npu.iter("option") if o.get("superClass","").endswith(suffix))
    return [x.get("value") for x in option.findall("listOptionValue")]
assert set(["DAB_USE_HARDWARE_NPU","DAB_NPU_DAB16_MODEL","DAB_AUTO_START=0","DAB_BOARD_CONFIG_CONFIRMED=0"]) <= set(options("compilerID.DEFINE"))
assert "${PROJECT_ROOT}/model/generated/npu/mod.a" in options("linkerID.LIBRARY")
folder=APP/"model/generated/npu"
manifest=json.loads((folder/"manifest.json").read_text())
for key,path in [("model_sha256",APP/"model"/manifest["model"]),("library_sha256",folder/"mod.a"),("header_sha256",folder/"tvmgen_default.h")]:
    assert manifest[key]==sha(path),key
runtime=(folder/"lib1.c").read_text()
assert runtime.count("DAB_NN_noteNpuCompletion();")==1
assert runtime.index("DAB_NN_noteNpuCompletion();") < runtime.index("tvmgen_default_finished = 1;")
assert (folder/"lib2.c").read_text().count("tinie_curr_layer += 1;")==4
maptext=(APP/"CPU1_LAUNCHXL_NPU_FLASH/dab_control_f28p550.map").read_text()
assert re.search(r"\.bss.noinit.tvm\s+\*?\s*\d+\s+0000e000\s+00000060",maptext)
assert "DAB_NN_noteNpuCompletion" in maptext and "mod.a : lib2.obj" in maptext
assert "g_nnLastOutput" in maptext
for config in ("CPU1_LAUNCHXL_NPU_FLASH", "CPU1_LAUNCHXL_FLASH"):
    completed=subprocess.run(["E:/Software_Download/ti/ccs2020/ccs/utils/bin/gmake.exe","-W","../dab_nn.c","-j4","all"],cwd=APP/config,capture_output=True,text=True,errors="replace")
    (HERE/(config+"_final_build.log")).write_text(completed.stdout+completed.stderr,encoding="utf-8")
    assert completed.returncode==0,config
    assert (APP/config/"dab_control_f28p550.out").is_file()
logs=["dab16_test.log","timing_regression.log","followup_regression.log","legacy_npu_regression.log"]
passes=[]
for name in logs:
    text=(HERE/name).read_text(encoding="utf-8",errors="replace")
    assert "PASS" in text and "Assertion failed" not in text and "error C" not in text,name
    passes += [line for line in text.splitlines() if "PASS" in line]
validation=json.loads((APP/"model/dab_npu_conv_validation.json").read_text())
assert validation["samples"]==501 and validation["max_abs_difference_from_dense_quantized"]==0
assert validation["invalid_output_vin"]==[92.2,92.3,92.4,92.5]

class Links(HTMLParser):
    def __init__(self): super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ("href","src"): self.urls.append(value)
for name in ("NPU_integration_guide_zh","NN_timing_guide_zh","DAB_F28P550_guide_zh"):
    source=APP/"docs"/(name+".md")
    rendered=APP/"docs"/(name+".html")
    text=rendered.read_text(encoding="utf-8")
    assert sha(source) in text
    assert "CPU1_LAUNCHXL_NPU_FLASH" in text
    links=Links();links.feed(text)
    for url in links.urls:
        parts=urlsplit(url)
        if not parts.scheme and parts.path:
            assert (rendered.parent/unquote(parts.path)).exists(),url
report={"date":"2026-10-09","ccs_configuration":"CPU1_LAUNCHXL_NPU_FLASH",
        "real_ti_nnc_library":True,"ti_nnc":manifest["ti_mcu_nnc"],"hardware_stages":4,
        "library_sha256":manifest["library_sha256"],"final_output_timestamp_hook":True,
        "builds":["CPU1_LAUNCHXL_NPU_FLASH","CPU1_LAUNCHXL_FLASH"],
        "npu_workspace":{"address":"0xE000","c28_words":96,"bytes":192},
        "conversion_validation":validation,"host_regressions":passes,
        "ccs_settings_and_artifact_hashes_checked":True,"document_links_and_source_hashes_checked":True,
        "application_sources_sha256":{name:sha(APP/name) for name in ("dab_nn.c","dab_nn.h","dab_control.c","dab_control.h",".cproject")},
        "forced_nn_recompile":True,
        "power_control_approved":False,"board_numeric_and_timing_validation":"pending"}
(HERE/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS: real library hashes, four hardware stages, final completion hook, GS1 placement, two TI builds, host regressions, model comparison, CCS settings, document links")
