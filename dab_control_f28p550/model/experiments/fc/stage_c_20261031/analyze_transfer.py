"""Instruction issue bounds and measured target/source costs; no guessed bus timing."""
import re
import shutil
from common_c import *


def main():
    base=json.loads((HERE/'results/transfer_audit.json').read_text());assert base['ok']
    fast=json.loads((HERE/'results/transfer_fast/transfer_audit.json').read_text());assert fast['ok']
    asm=(HERE/'assembly/baseline/dab_tinie_c28.asm').read_text(encoding='utf-8')
    block=asm[asm.index('RPTB'):asm.index('; repeat block ends')]
    instructions=re.findall(r'^\s+(MOVL|MOVB|ADDB)\s+([^;\n]+)',block,re.M)
    assert len(instructions)==22 and sum(op=='MOVL' for op,_ in instructions)==16
    rows=[]
    for b,f in zip(base['rows'],fast['rows']):
        assert (b['source'],b['target'],b['uint32_count'])==(f['source'],f['target'],f['uint32_count'])
        rows.append(dict(source=b['source'],target=b['target'],uint32_count=b['uint32_count'],
          baseline_min_ticks=b['min_ticks'],candidate_min_ticks=f['min_ticks'],saving_ticks=b['min_ticks']-f['min_ticks']))
    fits={}
    for label,d in [('baseline',base),('candidate',fast)]:
        fits[label]={}
        for target in ('GS0','NPU_PARAMS'):
            r=[r for r in d['rows'] if r['source']=='LS3' and r['target']==target]
            a,b=r[0],r[2];slope=(a['min_ticks']-b['min_ticks'])/(a['uint32_count']-b['uint32_count'])
            intercept=a['min_ticks']-slope*a['uint32_count']
            residuals=[x['min_ticks']-(intercept+slope*x['uint32_count']) for x in r[:3]]
            assert max(abs(x) for x in residuals)<=1
            fits[label][target]=dict(steady_cycles_per_uint32=slope,fitted_fixed_cycles=intercept,
              fit_residual_ticks=residuals,remainder_26word_cycles=r[3]['min_ticks'],
              scope='fit exact sizes 104/168/208 with no remainder; includes wrapper/timer cost; not a hardware latency specification')
    sums={label:sum(r['min_ticks'] for r in d['rows'] if r['source']=='LS3' and r['target']=='NPU_PARAMS') for label,d in [('baseline',base),('candidate',fast)]}
    sources=[hex(r['source_word_address']) for r in base['rows'] if r['source']=='LS3' and r['target']=='NPU_PARAMS']
    for label in ('AUDIT','AUDIT_FAST'):
        p=HERE/'work'/label/APP.name;dest=HERE/'assembly'/label;dest.mkdir(exist_ok=True)
        for name in ('dab_nn.c','dab_main.c','transfer_audit_c.h'):shutil.copy2(p/name,dest/name)
        lib=p/'model/generated/fc_int8'
        for name in ('dab_tinie_c28.c','lib2.c','build_commands.json','rebuild.log'):shutil.copy2(lib/name,dest/name)
        for extension in ('map','out'):shutil.copy2(p/BUILD/f'dab_control_f28p550.{extension}',dest/f'transfer_audit.{extension}')
    result=dict(ok=True,baseline_hot_block=instructions,baseline_issue_instructions_per_uint32=22/8,
      candidate_issue_instructions_per_uint32=9/4,payload_uint32_total=506,payload_logical_octets_total=2024,
      parameter_uint32_counts=[208,168,104,26],parameter_source_word_addresses=sources,
      code_run_ram='LS2 0x9000',parameter_run_ram='LS3 0x9800..0x9fff',source_alignment_C28_units=2,
      target_aperture_word_addresses=['0x55800','0x55fff'],target_payload_stride_C28_units=4,actual_access_width_bits=32,
      baseline_software_issue_floor_cycles=506*22/8,baseline_software_issue_floor_us=506*22/8/150,
      candidate_software_issue_floor_cycles=506*9/4,candidate_software_issue_floor_us=506*9/4/150,
      absolute_payload_issue_floor_cycles=506*2,absolute_payload_issue_floor_us=506*2/150,
      floor_limit='single issue load+store only, excludes address/call/loop and peripheral stalls; not an attainable platform transfer-time promise',
      measured_fits=fits,measured_four_calls_min_ticks=sums,measured_four_calls_min_us={k:v/150 for k,v in sums.items()},
      zero_count_min_ticks={'baseline':min(base['zero_ticks']),'candidate':min(fast['zero_ticks'])},rows=rows,
      source_placement_difference_at_most_one_tick=True,
      empirical_NPU_streaming_cycles_per_uint32=6,empirical_NPU_payload_only_us=506*6/150,
      attribution='Changing target GS0 to NPU_PARAMS at fixed source/loop isolates target-path cost, not its individual bridge/wait-state components. The NPU per-store latency and overlap rules are undocumented here; do not claim an absolute silicon optimum.',
      residency='Stage B evidence unchanged: no verified nonzero parameter base relocation contract or C28 residency API; no experiment attempted')
    dump(HERE/'results/transfer_analysis.json',result);protect()
    print(json.dumps(dict(ok=True,fits=fits,measured_us=result['measured_four_calls_min_us'])))


if __name__=='__main__':main()
