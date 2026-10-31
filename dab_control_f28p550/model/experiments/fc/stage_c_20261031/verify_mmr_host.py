"""Official encoder replay, dirty four-layer state, actual C28 decoder host C."""
from types import SimpleNamespace
import json
import re
import sys
import numpy as np
from common_c import *

SET=(3,5,8,9,12,18,21,24,25,27)
DYNAMIC=(4,29,30)


def decode(v):
    if len(v)==33:return {i:v[i] for i in (3,*range(5,29),31,32)}
    out={};pos=2
    for bit in range(32):
        if v[0]>>bit&1:out[bit+1]=v[pos];pos+=1
    packed=b''.join(int(x).to_bytes(4,'little') for x in v[pos:]);k=0
    for bit in range(32):
        if v[1]>>bit&1:out[bit+1]=packed[k];k+=1
    assert pos+(k+3)//4==len(v)
    return out


def main():
    protect();j=json.loads((HERE/'results/mmr_data.json').read_text());assert j['ok']
    sys.path.insert(0,str(TINIE/'hard/pyutils'));from common_mmr_defs import MMR
    host=HERE/'host';host.mkdir(exist_ok=True);rows=[]
    previous=None
    for row in j['layers']:
        mmr=MMR(SimpleNamespace(opt_for_space=1),[18,24])
        for reg in SET:mmr[reg]=row['full'][reg]
        file=host/f'official_{row["layer"]}.bin';mmr.tofile(file,prev_mmr=None)
        assert np.fromfile(file,np.uint32).tolist()==row['compressed']
        # Optional prev_mmr demonstrates exactly what NNC could skip, but B1
        # never passes it across FC calls. It is NOT installed as an optimization.
        delta=host/f'delta_demo_{row["layer"]}.bin';mmr.tofile(delta,prev_mmr=previous)
        dd=decode(row['compressed']);assert set(dd)==set(SET)
        assert all(dd[r]==row['full'][r] for r in SET)
        rows.append(dict(layer=row['layer'],encoded_words=len(row['compressed']),full_writes=30,compressed_writes=13,
             explicit_registers=sorted(dd),dynamic_registers=list(DYNAMIC),
             omitted_registers=[r for r in range(33) if r not in SET and r not in DYNAMIC],
             previous_mmr_in_actual_B1=None,delta_demo_words=delta.stat().st_size//4,
             constant_defs=list(mmr.constant_defs)))
        previous=mmr
    driver=(BASE/'dab_tinie_c28.c').read_text(encoding='utf-8')
    dec=body(driver,'write_configMMR')
    dec=re.sub(r'mmrs\[([^\]\n]+)\]\s*=\s*(.*?);',r'writeMmr(\1,\2);',dec,flags=re.S)
    dec=dec.replace('uint8_t','C28_u8')
    prefix=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
typedef uint16_t C28_u8;
typedef struct {uint32_t num_mmrs,num_params,num_ins;const uint32_t*mmrs,*params,*ins;void*in_fmap,*residual_fmap,*out_fmap;} TINIE_layer_t;
static volatile uint32_t hw[66];static unsigned writes,mask[33];
#define TINIE_BASE_ADDR ((uintptr_t)hw)
#define TINIE_MMR_OFS 0
#define TINIE_TOTAL_MMRS 33
#define TINIE_CTL2_INDEX 3
#define TINIE_CTL0_INDEX 5
#define TINIE_CTL1_INDEX 4
#define TINIE_MMR0_INDEX 29
#define TINIE_MMR1_INDEX 30
#define TINIE_MMR2_INDEX 31
#define TINIE_MMR3_INDEX 32
#define __byte(p,i) (((const uint8_t*)(const void*)(p))[i])
#define __norm32(v,p) (*(p)=__builtin_clz((unsigned)(v))-1)
static void writeMmr(unsigned offset,uint32_t value){assert(offset%2==0&&offset<66);hw[offset]=value;writes++;mask[offset/2]++;}
static void TINIE_mem_write(volatile uint32_t*dst,uint32_t n,const uint32_t*src){for(unsigned i=0;i<n;++i){writeMmr((unsigned)(dst-hw),*src++);dst+=2;}}
static C28_u8 find_and_clear_lsb_in_31b(uint32_t *val) {
'''+body(driver,'find_and_clear_lsb_in_31b')+r'''
}
static void write_configMMR(TINIE_layer_t*layer){
'''+dec+'\n}\n'
    prefix+='static const uint32_t full[4][33]={'+','.join('{'+','.join(str(x)+'u' for x in r['full'])+'}' for r in j['layers'])+'};\n'
    prefix+='static const uint32_t packed[4][6]={'+','.join('{'+','.join(str(x)+'u' for x in r['compressed'])+'}' for r in j['layers'])+'};\n'
    suffix=r'''
int main(void){
 const unsigned live[]={3,5,8,9,12,18,21,24,25,27,4,29,30};
 for(unsigned trial=0;trial<1000;++trial){
  for(unsigned r=0;r<66;++r)hw[r]=0xdead0000u+trial*17+r;
  for(unsigned layer=0;layer<4;++layer){
   uint32_t before[66],expected[66];memcpy(before,(const void*)hw,sizeof before);
   TINIE_layer_t l={0};l.in_fmap=(void*)(uintptr_t)(layer==0?0xe060:layer==2?0xe000:0xe020);
   l.out_fmap=(void*)(uintptr_t)(layer==0?0xe020:layer==1?0xe000:layer==2?0xe020:0xe010);
   l.num_mmrs=33;l.mmrs=full[layer];writes=0;memset(mask,0,sizeof mask);write_configMMR(&l);assert(writes==30);
   memcpy(expected,(const void*)hw,sizeof expected);memcpy((void*)hw,before,sizeof before);
   l.num_mmrs=6;l.mmrs=packed[layer];writes=0;memset(mask,0,sizeof mask);write_configMMR(&l);assert(writes==13);
   for(unsigned k=0;k<sizeof(live)/sizeof(live[0]);++k)assert(hw[2*live[k]]==expected[2*live[k]]);
   for(unsigned r=0;r<33;++r)if(!mask[r])assert(hw[2*r]==before[2*r]);
   // Adversarial execution state between FC layers. All required initial values
   // must be re-established, even if prior hardware mutated an address register.
   for(unsigned r=0;r<33;++r)if(r==12||r==21||r==25||r==27||r==15||r==22)hw[2*r]^=0xa5a50000u+trial+layer;
  }
 }
 uint32_t test[3]={0x80000000u,0,0x12345678};TINIE_layer_t l={0};l.num_mmrs=3;l.mmrs=test;
 write_configMMR(&l);assert(hw[64]==0x12345678);
 test[0]=0;test[1]=0x80000000u;test[2]=0x000000fe;write_configMMR(&l);assert(hw[64]==254);
 puts("PASS: actual decoder, 1000 dirty four-layer chains, all live registers, unchanged omissions, high-mask boundary");return 0;
}
'''
    src=host/'actual_decoder.c';src.write_text(prefix+suffix,encoding='utf-8');exe=host/'actual_decoder.exe'
    run([A/'host_tools/ziglang/zig.exe','cc',src,'-o',exe,'-O2','-Wno-pointer-to-int-cast'],cwd=host,timeout=180)
    message=run([exe],cwd=host).strip();print(message)
    dump(HERE/'results/mmr_host_verification.json',dict(ok=True,layers=rows,dirty_four_layer_chains=1000,
      actual_decoder_source_sha256=sha(src),message=message,
      full_raw_state_equality_required=False,
      equivalence_rule='All explicitly initialized FC registers and runtime address fields are exact; unused/not-initialized registers are intentionally retained, not falsely required to match zero. Before/after retention is checked.',
      cross_layer_reuse='Actual NNC B1 prev_mmr resets at each FC. constant_defs only permits skipping previous-set unchanged immutable fields within a supplied chain. Mutable PC/weight/bias/scale pointers always reinitialize.'))
    # Network and CPU graph remain literal B1. No new numeric approximation.
    for v in ('C1A','C1B'):
        p=HERE/'work'/v/APP.name/'model/generated/fc_int8'
        assert sha(p/'lib1.c')==sha(BASE/'lib1.c') and sha(p/'dab_tinie_c28.c')==sha(BASE/'dab_tinie_c28.c')
        assert arrays((p/'lib2.c').read_text(),'FC_PARAMS')==arrays((BASE/'lib2.c').read_text(),'FC_PARAMS')
    for name in ('host_verification','cpu_graph_host'):
        dump(HERE/f'results/{name}.json',dict(ok=True,variants=['C1A','C1B'],basis='unchanged B1 network/parameters/instruction/runtime hashes plus actual compressed decoder replay'))
    dump(HERE/'results/mapping_gate.json',dict(ok=True,board_allowed=True,hardware_tasks=4,network_parameters_and_instructions_unchanged=True))
    protect()


if __name__=='__main__':main()
