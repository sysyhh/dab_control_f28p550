"""Compile the exact original C transfer routine and check its footprint."""
from common_c import *


def main():
    protect();h=HERE/'host';h.mkdir(exist_ok=True)
    original=body((BASE/'dab_tinie_c28.c').read_text(encoding='utf-8'),'TINIE_mem_write')
    source='''#include <stdint.h>
#include <assert.h>
#include <stdio.h>
static void copy(volatile uint32_t *dst,uint32_t num,const uint32_t *src){
'''+original+'''}
int main(void){
 uint32_t s[512],d[1032];
 for(unsigned n=0;n<=512;++n){
  for(unsigned i=0;i<512;++i)s[i]=i*1234567u+n;
  for(unsigned i=0;i<1032;++i)d[i]=0xa5a5a5a5;
  copy(d+4,n,s);
  for(unsigned i=0;i<1032;++i){
   if(i>=4 && i<4+2*n && !(i&1))assert(d[i]==s[(i-4)/2]);
   else assert(d[i]==0xa5a5a5a5);
  }
 }
 puts("PASS: original copier n=0..512, all data, stride holes and guards");return 0;
}
'''
    p=h/'copy_baseline.c';p.write_text(source,encoding='utf-8')
    run([A/'host_tools/ziglang/zig.exe','cc',p,'-o',h/'copy_baseline.exe','-O2'],cwd=h,timeout=180)
    print(run([h/'copy_baseline.exe']))
    dump(HERE/'results/transfer_host_baseline.json',dict(ok=True,counts=list(range(513)),stride_uint32_slots=2,
         all_data_holes_and_guards=True,source_sha256=sha(p)))
    protect()


if __name__=='__main__':main()
