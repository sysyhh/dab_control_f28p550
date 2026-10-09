"""Compare actual generated C functions with their unmodified reference on host."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
from patch_npu_runtime import IDENTITY

APP=Path(__file__).resolve().parents[1]

def extract(code,name,rename):
    match=re.search(r'(?:TVM_DLL|static) int32_t '+re.escape(name)+r'\([^;{}]*\)\s*\{',code)
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
    body+='puts("PASS: generated C hidden-layer identity; all 256 values at all 64 channel positions; boundary guards");\n'
    if 'int32_t dab_npu_copy_words(' in current:
        code+=extract(current,'dab_npu_copy_words','copy_words')+'\n'
        # Exhaust every possible packed 16-bit word. Actual old unpack and pack
        # functions are compiled against C28 storage semantics, not host bytes.
        code+='''
#define uint8_t uint16_t
static void c28_unpack_unsigned(uint16_t *src,uint16_t *dst,int i) {dst[i]=(src[i/2]>>((i%2)*8))&255;}
static void c28_pack(uint16_t *src,uint16_t *dst,int i) {unsigned shift=(i%2)*8; dst[i/2]=(uint16_t)((dst[i/2]&~(255U<<shift))|((src[i]&255U)<<shift));}
'''
        for suffix in ('','_1'):
            code+=extract(original,'tvmgen_default_fused_tinie_c28_unpack'+suffix,'unpack'+suffix)+'\n'
        for suffix in ('_1','_2'):
            code+=extract(original,'tvmgen_default_fused_tinie_c28_pack'+suffix,'pack'+suffix)+'\n'
        code+='#undef uint8_t\n'
        body+='''{ uint16_t src[18],old[18],now[18],expanded[32]; unsigned value,words,j;
for(words=8;words<=16;words+=8) for(value=0;value<65536;++value) {
 for(j=0;j<18;++j) {src[j]=(uint16_t)(value+j*257U); old[j]=now[j]=0xA55A;}
 if(words==16) {unpack(src+1,expanded,0,0); pack_1(expanded,old+1,0,0);}
 else {unpack_1(src+1,expanded,0,0); pack_2(expanded,old+1,0,0);}
 copy_words(src+1,now+1,(uint16_t)words);
 assert(memcmp(old,now,sizeof(old))==0);
 assert(now[0]==0xA55A && now[words+1]==0xA55A);
 copy_words(now+1,now+1,(uint16_t)words); assert(memcmp(old,now,sizeof(old))==0);
} puts("PASS: generated packed copy versus original unpack/pack; all 65536 word values; 8/16 words; boundary guards"); }
'''
    driver=(args.generated/'dab_tinie_c28.c').read_text(encoding='utf-8')
    kernel=(args.generated/'lib2.c').read_text(encoding='utf-8')
    if '.dab_npu_const' in kernel:
        stripped=re.sub(r'#pragma DATA_SECTION\([^\n]+\)\n','',kernel)
        assert stripped==(args.generated/'lib2.flash_reference.c').read_text(encoding='utf-8')
        print('PASS: RAM constant placement only adds directives; kernel and constant data unchanged')
    if 'int32_t dab_npu_load_words(' in driver:
        code+=extract(driver,'dab_npu_load_words','load_words')+'\n'
        body+='''{ uint32_t src[516],old[1034],now[1034]; unsigned n,j;
for(n=0;n<=516;++n) {
 for(j=0;j<516;++j) src[j]=0xAC128765U^(j*0x019DE1F3U);
 for(j=0;j<1034;++j) old[j]=now[j]=0xA5A5A5A5U;
 for(j=0;j<n;++j) old[1+j*2]=src[j];
 load_words(now+1,src,n);
 assert(memcmp(old,now,sizeof(now))==0);
} puts("PASS: real generated loading helper; lengths 0..516; all tails; MMIO stride and untouched guards"); }
'''
    body+='return 0;}\n'
    with tempfile.TemporaryDirectory(prefix='dab_npu_verify_') as directory:
        folder=Path(directory)
        (folder/'test.c').write_text(code+body,encoding='utf-8')
        (folder/'run.cmd').write_text('@echo off\ncall "E:\\Software_Download\\VS2017\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\ncl /nologo /utf-8 /TC /O2 /fp:strict test.c /Fe:test.exe\nif errorlevel 1 exit /b %errorlevel%\ntest.exe\n',encoding='utf-8')
        subprocess.run(['cmd','/c','run.cmd'],cwd=folder,check=True)

if __name__=='__main__': main()
