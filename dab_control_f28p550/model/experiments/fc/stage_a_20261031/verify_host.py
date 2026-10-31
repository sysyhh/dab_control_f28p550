"""Compile actual generated FC CPU code on host with C28 word/byte emulation.

The NPU stub tests graph/data transport only; it is never a hardware performance
claim. Unchanged NPU kernels plus identical layer inputs prove induction across
real kernels. Separate board capture validates actual hardware layer images.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import numpy as np
from patch_stage_a import checked_identity, transform, INPUT_HEADER
from run_stage_a import HERE, APP, BASE, VARIANTS, sha, dump, run

HOST = HERE/'host'
ZIG = HERE/'host_tools/ziglang/zig.exe'

PREFIX = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#define TVM_DLL
#define __attribute__(x)
#define DAB_NPU_DETAIL_PROFILE 0
typedef struct {int dummy;} TINIE_layer_t;
static void TINIE_setup(TINIE_layer_t *p) {(void)p;}
static void TINIE_start(void) {}
static void TINIE_registerInterrupt(void (*p)(void)) {(void)p;}
static void TINIE_clearInterruptACK(void) {}
static void DAB_NN_isrEnter(void) {}
static void DAB_NN_isrExit(uint16_t p) {(void)p;}
static void DAB_NN_noteNpuCompletion(void) {}
static unsigned getbyte(const void *p, unsigned i) {return (((const uint16_t*)p)[i/2]>>(8*(i%2)))&255;}
static void putbyte(void *p, unsigned i, unsigned v) {
    uint16_t *w=p; unsigned shift=8*(i%2);
    w[i/2]=(w[i/2]&~(255u<<shift))|((v&255u)<<shift);
}
static void c28_pack(const void *src, void *dst, unsigned i) {putbyte(dst,i,((const uint16_t*)src)[i]);}
static void c28_unpack_unsigned(const void *src, void *dst, unsigned i) {((uint16_t*)dst)[i]=getbyte(src,i);}
static void c28_unpack_signed(const void *src, void *dst, unsigned i) {unsigned v=getbyte(src,i); ((int16_t*)dst)[i]=v&128?v-256:v;}
static uint16_t transcript[256];
static unsigned used;
static uint32_t seed;
static void stub(unsigned layer, void *src, void *dst) {
    const unsigned ni[]={16,29,16,16}, no[]={29,16,16,4};
    uintptr_t a=(uintptr_t)src, b=(uintptr_t)dst;
    assert(a+(ni[layer]+1)/2*2<=b || b+(no[layer]+1)/2*2<=a);
    for(unsigned i=0;i<ni[layer];++i) transcript[used++]=getbyte(src,i);
    uint32_t sum=seed+layer*97;
    for(unsigned i=0;i<ni[layer];++i) sum=sum*33+getbyte(src,i)*(i+1);
    for(unsigned i=0;i<no[layer];++i) {unsigned v=(sum>>(i%17))+(i*83); putbyte(dst,i,v); transcript[used++]=v&255;}
    extern volatile int32_t tinie_curr_layer;
    tinie_curr_layer++;
}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int16_t*a,int16_t*b,uint16_t*c){stub(0,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int16_t*a,int16_t*b,uint16_t*c){stub(1,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int16_t*a,int16_t*b,uint16_t*c){stub(2,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int16_t*a,int16_t*b,uint16_t*c){stub(3,a,b);return 0;}
'''

SUFFIX = r'''
static void check_hidden(void) {
    uint16_t in[33], out[33], ws[100];
    for(unsigned u=0;u<256;++u) {
        for(unsigned i=0;i<33;++i) in[i]=u, out[i]=0xdead;
        tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast(in,out,ws);
        for(unsigned i=0;i<29;++i) assert(out[i]==u);
        for(unsigned i=29;i<33;++i) assert(out[i]==0xdead);
        memset(out,0xef,sizeof out);
        tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast_1(in,out,ws);
        for(unsigned i=0;i<16;++i) assert(out[i]==u);
        for(unsigned i=16;i<33;++i) assert(out[i]==0xefef);
    }
}
static void check_packed(void) {
    // Exercise all pairs and every channel length 1..65, in-place and disjoint.
    for(unsigned n=1;n<=65;++n) for(unsigned value=0;value<65536;++value) {
        uint16_t mem[160], before[160];
        for(unsigned i=0;i<160;++i) mem[i]=0xa5a5;
        for(unsigned i=0;i<n;++i) mem[4+i]=(value>>(8*(i%2)))&255;
        memcpy(before,mem,sizeof mem);
        for(unsigned i=0;i<n;++i) c28_pack(mem+4,mem+80,i);
        for(unsigned i=0;i<n;++i) assert(getbyte(mem+80,i)==before[4+i]);
        for(unsigned i=0;i<80;++i) assert(mem[i]==before[i]);
        for(unsigned i=80+(n+1)/2;i<160;++i) assert(mem[i]==before[i]);
        // In-place forward pack, as used by A1. Odd pad equals original zero extension.
        memcpy(mem,before,sizeof mem);
        for(unsigned i=0;i<n;++i) c28_pack(mem+4,mem+4,i);
        for(unsigned i=0;i<n;++i) assert(getbyte(mem+4,i)==before[4+i]);
        for(unsigned i=0;i<4;++i) assert(mem[i]==before[i]);
        for(unsigned i=4+n;i<160;++i) assert(mem[i]==before[i]);
        if(n&1) assert((mem[4+n/2]&0xff00)==0);
        // A2 aliases a dirty NPU output; only its unused high byte may change.
        if(n&1) mem[4+n/2] |= (value&255u)<<8;
        memcpy(before,mem,sizeof mem);
        if(n&1) mem[4+n/2]&=255;
        for(unsigned i=0;i<n;++i) assert(getbyte(mem+4,i)==getbyte(before+4,i));
        for(unsigned i=0;i<160;++i) {
            if((n&1) && i==4+n/2) assert(mem[i]==(before[i]&255));
            else assert(mem[i]==before[i]);
        }
    }
}
int main(int argc,char **argv) {
    assert(argc==3);
    check_hidden(); check_packed();
    FILE *f=fopen(argv[1],"rb"),*g=fopen(argv[2],"wb"); assert(f&&g);
    float vin;
    while(fread(&vin,4,1,f)==1) for(unsigned trial=0;trial<8;++trial) {
        uint16_t memory[125]; float out[4], features[16]={0};
        uint16_t packed[8]={0xe0,0x12,0,0,0,0,0,0};
        for(unsigned i=0;i<125;++i) memory[i]=(uint16_t)(0xa500+trial);
        features[0]=-.5f; features[1]=vin/140.0f; features[2]=.285714f;
        DAB_FC_preparePackedInput(vin,packed);
        uint16_t original[16];
        tvmgen_default_fused_multiply_add_floor_clip_cast(features,(int16_t*)original,memory+16);
        for(unsigned i=0;i<16;++i) assert((original[i]&255)==getbyte(packed,i));
        used=0; seed=trial*1234567u;
#if PREQUANT
        tvmgen_default___tvm_main__(packed,out,memory+16);
#else
        tvmgen_default___tvm_main__(features,out,memory+16);
#endif
        for(unsigned layer=1;layer<=4;++layer) tvmgen_default_IRQHandlerHelper();
        assert(tvmgen_default_finished==1 && tinie_curr_layer==4);
        for(unsigned i=0;i<16;++i) assert(memory[i]==(uint16_t)(0xa500+trial));
        for(unsigned i=109;i<125;++i) assert(memory[i]==(uint16_t)(0xa500+trial));
        fwrite(transcript,2,used,g); fwrite(out,4,4,g);
    }
    fclose(f); fclose(g); puts("all assertions passed"); return 0;
}
'''


def main():
    HOST.mkdir(exist_ok=True)
    vins = list(np.float32(np.arange(501)/10+90))
    # Each exact Vin transition and its immediate predecessor/successor in binary32.
    for q in range(-129,130):
        edge=np.float32(140*(q-.5)/64)
        vins += [np.nextafter(edge,np.float32(-np.inf)),edge,np.nextafter(edge,np.float32(np.inf))]
    # Generic input clamp extremes, subnormals, zero and ties; beyond application range is host-only.
    vins += [np.float32(x) for x in (-1e8,-.1,0,.1,1e8)]
    probes=np.array(vins,dtype=np.float32)
    probes.tofile(HOST/'vins.bin')
    (HOST/'fc_stage_a_input.h').write_text(INPUT_HEADER,encoding='utf-8')
    raw=(BASE/'lib1.c').read_text(encoding='utf-8')
    checked_identity(raw)
    rejected=[]
    for name, changed in [('int4',(APP/'model/generated/fc_int4/lib1.c').read_text(encoding='utf-8')),
                          ('clip254',raw.replace('2.550000e+02f','2.540000e+02f')),
                          ('roundquarter',raw.replace('5.000000e-01f','2.500000e-01f'))]:
        try:
            transform(changed,'A1')
        except ValueError:
            rejected.append(name)
    assert len(rejected)==3
    try:
        transform(raw.replace('6.400000e+01f','6.300000e+01f'),'A3')
    except ValueError:
        rejected.append('input_scale63')
    assert len(rejected)==4
    results={}
    for variant in VARIANTS:
        lib=HERE/'work'/variant/APP.name/'model/generated/fc_int8'
        code=(lib/'lib1.c').read_text(encoding='utf-8')
        code=re.sub(r'^#(?:include|pragma|define DAB_NPU_DETAIL_PROFILE).*\n','',code,flags=re.M)
        # C28 TVM typedefs use a 16-bit storage unit for both logical int8 types.
        code=re.sub(r'\buint8_t\b','uint16_t',code)
        code=re.sub(r'\bint8_t\b','int16_t',code)
        suffix=SUFFIX
        if variant in ('A3','A4'):
            app=(HERE/'work'/variant/APP.name/'dab_nn.c').read_text(encoding='utf-8')
            init=app.split('void DAB_NN_init(void)\n{\n',1)[1].split('#ifndef DAB_USE_HARDWARE_NPU',1)[0]
            init=init.replace('s_input','packed')
            suffix=suffix.replace('uint16_t packed[8]={0xe0,0x12,0,0,0,0,0,0};',
                'uint16_t packed[8];\n'+init)
        src=HOST/(variant+'.c')
        src.write_text(PREFIX+'\n#include "fc_stage_a_input.h"\n'+code+suffix,encoding='utf-8')
        exe=HOST/(variant+'.exe')
        cmd=[ZIG,'cc',src,'-o',exe,'-O2','-ffp-contract=off', '-Wno-incompatible-pointer-types',
             f'-DPREQUANT={int(variant in ("A3","A4"))}']
        log=run(cmd,cwd=HOST,timeout=180)
        (HOST/(variant+'_build.log')).write_text(log,encoding='utf-8')
        output=HOST/(variant+'.bin')
        message=run([exe,HOST/'vins.bin',output],cwd=HOST,timeout=180)
        results[variant]={'ok':True,'output_sha256':sha(output),'source_sha256':sha(src),
                          'kernel_unchanged':sha(lib/'lib2.c')==sha(BASE/'lib2.c'),
                          'driver_unchanged':sha(lib/'dab_tinie_c28.c')==sha(BASE/'dab_tinie_c28.c'),
                          'message':message.strip()}
        assert results[variant]['kernel_unchanged'] and results[variant]['driver_unchanged']
        if variant!='Baseline':
            assert output.read_bytes()==(HOST/'Baseline.bin').read_bytes(),variant+' layer input/output mismatch'
        print(variant+': host passed',flush=True)
    report={'ok':True,'compiler':run([ZIG,'version']).strip(),'variants':results,
            'official_vin_points':501,'total_input_probes':len(probes),'graph_trials_per_probe':8,
            'hidden_inputs_per_function':256,'packed_pairs_per_length':65536,'packed_lengths':list(range(1,66)),
            'rejected_unsafe_transforms':rejected,
            'limitations':'Host NPU is a deterministic transport stub, not a hardware arithmetic emulator or performance result.'}
    dump(HERE/'results/host_verification.json',report)
    print(json.dumps({'ok':True,'probes':len(probes),'report':str(HERE/'results/host_verification.json')}))


if __name__=='__main__':
    main()
