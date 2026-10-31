"""Compile opt_for_space on the frozen B1 ONNX, transplant only checked MMRs."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from common_c import *


def main():
    protect();out=HERE/'generated/compressed_raw';out.mkdir(parents=True,exist_ok=True)
    cgt=stage_b.stage_a.CGT;sdk=stage_b.stage_a.SDK
    includes=[cgt/'include',sdk/'driverlib/f28p55x/driverlib',sdk/'device_support/f28p55x/common/include']
    cross='--abi=eabi -O3 --opt_for_speed=5 --c99 -v28 -ml -mt --gen_func_subsections --float_support=fpu32 '+ ' '.join('-I'+p.as_posix() for p in includes)+' -I.'
    env=dict(os.environ);env.update(C2000WARE_PATH=str(sdk),C2000_CGT_PATH=str(cgt),C2000_DEVICE='f28p55x',C2000_DEVICE_FPU='fpu32',CL2000_OPTIONS=cross,
                 FORCE_NO_TI_C28_SOFT_OFFLOAD='true',PYTHONIOENCODING='utf-8',TINIE_COMPILE_DEBUG='1')
    env['PATH']=str(cgt/'bin')+os.pathsep+env.get('PATH','')
    model=B/'onnx/B1_16_32_16_16_4.onnx'
    cmd=[str(NNC/'python.exe'),'-m','tvm.driver.tvmc','compile','--target=c, ti-npu opt_for_space=true','--target-c-mcpu=c28',str(model),
         '-o',str(out/'mod.a'),'--cross-compiler=cl2000','--cross-compiler-options='+cross]
    p=subprocess.run(cmd,cwd=out,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
    (out/'compile.log').write_text(p.stdout+p.stderr,encoding='utf-8');dump(out/'command.json',dict(command=cmd,model_sha256=sha(model),returncode=p.returncode));assert p.returncode==0,(p.stdout+p.stderr)[-3000:]
    full=(BASE/'lib2.c').read_text(encoding='utf-8');comp=(out/'lib2.c').read_text(encoding='utf-8')
    fa=mapping(BASE);clayers=[]
    for i in range(4):
        cb=body(comp,f'tvmgen_default_ti_npu_fullyConnectedNHWC_{i}')
        assert 'tinie_num_sublayers = 1;' in cb and 'tinie_sublayer_IRQHandler();' in cb
        clayers.append(dict(parameters=re.findall(r'\b(FC_PARAMS\w*)\s*,',cb),mmrs=re.findall(r'\b(FC_MMR\w*)\s*,',cb),
                           instructions=re.findall(r'\b(FC_\w+_INS)\s*,',cb)))
    ca=dict(hardware_tasks=4,layers=clayers);assert fa['hardware_tasks']==4
    fp,cp=arrays(full,'FC_PARAMS'),arrays(comp,'FC_PARAMS');fm,cm=arrays(full,'FC_MMR'),arrays(comp,'FC_MMR')
    rows=[];patched=full
    for i,(fl,cl) in enumerate(zip(fa['layers'],ca['layers'])):
        assert fl['instructions']==cl['instructions']
        assert fp[fl['parameters'][0]]==cp[cl['parameters'][0]],('parameters changed',i)
        old,new=fm[fl['mmrs'][0]],cm[cl['mmrs'][0]];assert len(old)==33 and 2<len(new)<33
        name=fl['mmrs'][0]
        pattern=r'(static const uint32_t '+re.escape(name)+r'\[\] = \{).*?(\};)'
        replacement=r'\1\n'+''.join(f'0x{v:x},\n' for v in new)+r'\2'
        patched,n=re.subn(pattern,replacement,patched,flags=re.S);assert n==1
        rows.append(dict(layer=i,full_name=name,compiled_name=cl['mmrs'][0],full=old,compressed=new,
                         full_bytes=132,compressed_bytes=len(new)*4,parameter_bytes=len(fp[fl['parameters'][0]])*4))
    dest=HERE/'generated/C1B';shutil.copytree(BASE,dest,dirs_exist_ok=True)
    (dest/'lib2.c').write_text(patched,encoding='utf-8',newline='\n')
    # Every byte outside MMR initializers is identical to the already verified B1.
    strip=lambda s:re.sub(r'(static const uint32_t FC_MMR\w*\[\] = \{).*?(\};)',r'\1MMR\2',s,flags=re.S)
    assert strip(patched)==strip(full)
    dump(HERE/'results/mmr_data.json',dict(ok=True,network_sha256=sha(model),hardware_tasks=4,
         only_mmr_initializers_changed=True,weights_and_instructions_exact=True,layers=rows))
    evidence=HERE/'evidence/nnc211';evidence.mkdir(parents=True,exist_ok=True)
    for name in ('common_mmr_defs.py','gen_mmr_fc.py','config_fc.py','common_utils.py'):
        shutil.copy2(TINIE/'hard/pyutils'/name,evidence/name)
    print(json.dumps(dict(ok=True,mmr_bytes_before=528,mmr_bytes_after=sum(r['compressed_bytes'] for r in rows))))
    protect()


if __name__=='__main__':main()
