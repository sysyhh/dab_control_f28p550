"""Run the actual Stage-A-reused CPU graph with decoded golden NPU images."""
import json
import re
import sys
from audit_stage_b import HERE,APP,STAGE_A,dump,sha,protect
from run_stage_b import run
sys.path.insert(0,str(STAGE_A))
from verify_host import PREFIX


def main():
    protect();h=HERE/'host';h.mkdir(exist_ok=True)
    data=json.loads((HERE/'results/reachable_input_traces.json').read_text())
    results={}
    for variant in ('A4','B1'):
        project=HERE/'work'/variant/APP.name
        runtime=(project/'model/generated/fc_int8/lib1.c').read_text(encoding='utf-8')
        runtime=re.sub(r'^#(?:include|pragma|define DAB_NPU_DETAIL_PROFILE).*\n','',runtime,flags=re.M)
        runtime=re.sub(r'\buint8_t\b','uint16_t',runtime);runtime=re.sub(r'\bint8_t\b','int16_t',runtime)
        records=[];bits=[]
        for q,row in data.items():
            bits.append(row['first_bits'])
            layers=[list(x) for x in row['layers']]
            records.append('{'+','.join('{'+','.join(map(str,l+[0]*(32-len(l))))+'}' for l in layers)+'}')
        pre=PREFIX[:PREFIX.index('static uint16_t transcript')]
        pre+='\nstatic const int16_t expected[24][4][32] = {'+','.join(records)+'};\n'
        pre+='static const uint32_t vin_bits[24] = {'+','.join(map(str,bits))+'};\n'
        pre+=f'static const unsigned widths[5]={{16,{32 if variant=="B1" else 29},16,16,4}};\n'
        pre+=r'''
static unsigned sample,step;
static void stub(unsigned layer,void *src,void *dst) {
    assert(step++==layer);
    uintptr_t a=(uintptr_t)src,b=(uintptr_t)dst;
    assert(a+(widths[layer]+1)/2*2<=b || b+(widths[layer+1]+1)/2*2<=a);
    for(unsigned i=0;i<widths[layer];++i) {
        int16_t v=layer==0?(i==0?-32:i==1?(int16_t)(sample+41):i==2?18:0):expected[sample][layer-1][i];
        assert(getbyte(src,i)==(unsigned)(v&255));
    }
    for(unsigned i=0;i<widths[layer+1];++i) putbyte(dst,i,expected[sample][layer][i]);
    extern volatile int32_t tinie_curr_layer;
    tinie_curr_layer++;
}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_0(int16_t*a,int16_t*b,uint16_t*c){stub(0,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_1(int16_t*a,int16_t*b,uint16_t*c){stub(1,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_2(int16_t*a,int16_t*b,uint16_t*c){stub(2,a,b);return 0;}
int32_t tvmgen_default_ti_npu_fullyConnectedNHWC_3(int16_t*a,int16_t*b,uint16_t*c){stub(3,a,b);return 0;}
'''
        suffix=r'''
int main(void) {
    for(sample=0;sample<24;++sample) for(unsigned dirty=0;dirty<8;++dirty) {
        uint16_t memory[128],packed[8]={0xe0,0x12,0,0,0,0,0,0};float output[4],vin;
        memcpy(&vin,&vin_bits[sample],4);
        DAB_FC_preparePackedInput(vin,packed);
        for(unsigned i=0;i<128;++i)memory[i]=(uint16_t)(0xa5f0+dirty);
        step=0;tvmgen_default___tvm_main__(packed,output,memory+16);
        for(unsigned layer=0;layer<4;++layer)tvmgen_default_IRQHandlerHelper();
        assert(step==4&&tvmgen_default_finished==1);
        for(unsigned i=0;i<4;++i) {
            float v=expected[sample][3][i]*.015625f;
            assert(memcmp(&v,output+i,4)==0);
        }
        for(unsigned i=0;i<16;++i)assert(memory[i]==(uint16_t)(0xa5f0+dirty));
        for(unsigned i=112;i<128;++i)assert(memory[i]==(uint16_t)(0xa5f0+dirty));
    }
    puts("PASS: 24 reachable codes x 8 dirty workspaces, exact four-layer transport and final float bits");
    return 0;
}
'''
        header=(project/'fc_stage_a_input.h').read_text(encoding='utf-8')
        src=h/(variant+'_cpu.c');src.write_text(pre+'\n'+header+'\n'+runtime+suffix,encoding='utf-8')
        exe=h/(variant+'_cpu.exe');zig=STAGE_A/'host_tools/ziglang/zig.exe'
        log=run([zig,'cc',src,'-o',exe,'-O2','-ffp-contract=off','-Wno-incompatible-pointer-types'],cwd=h,timeout=180)
        message=run([exe],cwd=h)
        results[variant]=dict(ok=True,source_sha256=sha(src),message=message.strip())
        print(variant+': '+message.strip(),flush=True)
    dump(HERE/'results/cpu_graph_host.json',dict(ok=True,variants=results,protect_guard_words_each_side=16,
          runtime_workspace_units=96,source='actual compiled lib1, Stage A input helper and C28 word/byte emulation'))
    protect()


if __name__=='__main__':main()
