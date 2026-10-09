from pathlib import Path
import re
import xml.etree.ElementTree as ET

app = Path(__file__).resolve().parents[2] / "dab_control_f28p550"
path = app / ".cproject"
text = path.read_text(encoding="utf-8")
text = re.sub(r'(<entry excluding=")([^\"]*)', lambda m: m[1] + m[2] + ("|model/generated" if "model/generated" not in m[2] else ""), text)
name = "CPU1_LAUNCHXL_NPU_FLASH"
defines = ["DAB_USE_HARDWARE_NPU", "DAB_NPU_DAB16_MODEL", "DAB_AUTO_START=0", "DAB_BOARD_CONFIG_CONFIRMED=0"]
if f'name="{name}"' not in text:
    configs = re.findall(r'        <cconfiguration\b.*?</cconfiguration>', text, re.S)
    block = next(c for c in configs if 'name="CPU1_LAUNCHXL_FLASH"' in c)
    block = block.replace("CPU1_LAUNCHXL_FLASH", name)
    ids = dict((value, str(1900000000+i)) for i, value in enumerate(dict.fromkeys(re.findall(r'\bid="[^\"]*\.(\d+)"', block))))
    block = re.sub(r'(\bid="[^\"]*\.)(\d+)(")', lambda m: m[1] + ids[m[2]] + m[3], block)
    def update_option(match):
        opening, content, closing = match.groups()
        if 'superClass="com.ti.ccstudio.buildDefinitions.C2000_22.6.compilerID.DEFINE"' in opening:
            content += "".join(f'                                    <listOptionValue value="{d}"/>\n' for d in defines)
        if 'superClass="com.ti.ccstudio.buildDefinitions.C2000_22.6.linkerID.LIBRARY"' in opening:
            content += '                                    <listOptionValue value="${PROJECT_ROOT}/model/generated/npu/mod.a"/>\n'
        return opening+content+closing
    block = re.sub(r'(<option\b(?=[^>]*valueType="(?:definedSymbols|libs)")[^>]*>)(.*?)(</option>)', update_option, block, flags=re.S)
    text = text.replace(configs[-1], configs[-1] + "\n" + block)
root=ET.fromstring(text)
npu=next(c for c in root.findall("./storageModule/cconfiguration")
         if c.find("./storageModule").get("name")==name)
for option in npu.iter("option"):
    kind=option.get("superClass", "")
    values=[v.get("value") for v in option.findall("listOptionValue")]
    required=defines if kind.endswith("compilerID.DEFINE") else (["${PROJECT_ROOT}/model/generated/npu/mod.a"] if kind.endswith("linkerID.LIBRARY") else [])
    for value in required:
        if value not in values: ET.SubElement(option,"listOptionValue",{"value":value})
ET.indent(npu,space="    ",level=2)
old=next(c for c in re.findall(r'        <cconfiguration\b.*?</cconfiguration>',text,re.S) if f'name="{name}"' in c)
text=text.replace(old, "        "+ET.tostring(npu,encoding="unicode").rstrip())
path.write_text(text, encoding="utf-8")
# Bootstrap this new output folder from the existing CCS-generated make rules.
# CCS can regenerate the same rules from .cproject on the next project build.
source, target = app / "CPU1_LAUNCHXL_FLASH", app / name
for path in list(source.rglob("*.mk")) + [source / "makefile"]:
    relative = path.relative_to(source)
    dest = target / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8").replace("CPU1_LAUNCHXL_FLASH", name)
    if path.name == "subdir_rules.mk":
        content = content.replace("--define=_LAUNCHXL_F28P55X", "--define=_LAUNCHXL_F28P55X " + " ".join("--define="+d for d in defines))
    if path.name in ("makefile", "objects.mk"):
        content = content.replace("-llibc.a", '-llibc.a -l"../model/generated/npu/mod.a"')
    dest.write_text(content, encoding="utf-8")
print("New CCS configuration and build rules:", target)
