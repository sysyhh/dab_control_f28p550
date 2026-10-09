import re
import subprocess
from pathlib import Path

path='dab_control_f28p550/model/generated/npu/lib2.c'
old=subprocess.check_output(['git','show','f5d5f41:'+path],text=True)
new=Path(path).read_text()
pattern=r'static const uint32_t (PWCONV_\w+)\[\]\s*=\s*\{(.*?)\};'
def arrays(code):
    return {name:re.sub(r'\s+','',body) for name,body in re.findall(pattern,code,re.S)}
assert sorted(arrays(old).values())==sorted(arrays(new).values()) and len(arrays(new))==8
assert sorted(re.findall(r'#include "hard/ins_asm/([^"]+)"',old))==sorted(re.findall(r'#include "hard/ins_asm/([^"]+)"',new))
def layers(code):
    data=arrays(code)
    bodies=re.findall(r'TVM_DLL int32_t (tvmgen_default_ti_npu_convolve1x1NHWC_\d+)\([^\n]+\) \{(.*?)(?=TVM_DLL int32_t|\Z)',code,re.S)
    result={}
    for name,body in bodies:
        mmr,params,ins=re.findall(r'sizeof\((PWCONV_\w+)\)/sizeof',body)
        result[name]=(data[mmr],data[params],ins)
    return result
assert len(layers(new))==4 and layers(old)==layers(new)
print('PASS: all four layers retain identical parameter/configuration data and instruction selection despite generated declaration reordering')
