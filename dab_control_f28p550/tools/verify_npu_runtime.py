"""Compare actual generated C functions with their unmodified reference on host."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
from patch_npu_runtime import IDENTITY

APP=Path(__file__).resolve().parents[1]

def extract(code,name,rename):
    match=re.search(r'TVM_DLL int32_t '+re.escape(name)+r'\([^;{}]*\)\s*\{',code)
    if not match: raise RuntimeError('Missing function '+name)
    depth=1; end=match.end()
    while depth:
        depth+=(code[end]=='{')-(code[end]=='}'); end+=1
    return code[match.start():end].replace(name,rename)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated',type=Path,default=APP/'model/generated/npu')
    args=parser.parse_args()
    original=(args.generated/'lib1.reference.c').read_text(encoding='utf-8')
    current=(args.generated/'lib1.c').read_text(encoding='utf-8')
    constants=(args.generated/'lib0.c').read_text(encoding='utf-8')
    code='#include <stdint.h>\n#include <math.h>\n#include <stdio.h>\n#include <string.h>\n#include <assert.h>\n#define TVM_DLL\n#define DAB_NPU_DETAIL_PROFILE 0\n'
    body='int main(void) { float storage[40]={0}; uint8_t *c=(uint8_t*)storage; uint8_t input[32],a[34],b[34],scratch[256]; unsigned v,i;\n'
    for k,(suffix,n) in enumerate([('',32),('_1',16),('_2',16)]):
        name=IDENTITY+suffix
        for source,label in [(original,'ref'),(current,'opt')]:
            code+=extract(source,name,label+str(k))+'\n'
        ref=extract(original,name,'unused')
        for var,offset in re.findall(r'void\* (\w+) = \(&\(\w+\[(\d+)\]\)\);',ref):
            value=re.search(r'\.'+var+r'\s*=\s*\{\s*([^\s}]+)',constants)
            if not value: raise RuntimeError('Missing constant '+var)
            body+=f'{{float value={float.fromhex(value[1])}f; memcpy(c+{offset},&value,sizeof(value));}}\n'
        body+=f'''for(v=0;v<256;++v) {{
 for(i=0;i<{n};++i) input[i]=(uint8_t)(v+i);
 memset(a,0xA5,sizeof(a)); memset(b,0xA5,sizeof(b));
 ref{k}(input,a+1,c,scratch); opt{k}(input,b+1,c,scratch);
 assert(memcmp(a,b,sizeof(a))==0);
 assert(a[0]==0xA5 && a[{n+1}]==0xA5);
 assert(memcmp(a+1,input,{n})==0);
}}\n'''
    body+='puts("PASS: generated C hidden-layer identity; all 256 values at all 64 channel positions; boundary guards"); return 0;}\n'
    with tempfile.TemporaryDirectory(prefix='dab_npu_verify_') as directory:
        folder=Path(directory)
        (folder/'test.c').write_text(code+body,encoding='utf-8')
        (folder/'run.cmd').write_text('@echo off\ncall "E:\\Software_Download\\VS2017\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\ncl /nologo /utf-8 /TC /O2 /fp:strict test.c /Fe:test.exe\nif errorlevel 1 exit /b %errorlevel%\ntest.exe\n',encoding='utf-8')
        subprocess.run(['cmd','/c','run.cmd'],cwd=folder,check=True)

if __name__=='__main__': main()
