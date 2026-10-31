"""Replay all retained board records and export independently accepted C packages."""
import csv
import inspect
import re
import shutil
import statistics
import hashlib
import struct
from common_c import *
import verify_results_b as previous
from parameter_candidate import patch as param_patch
from static_mmr import patch as mmr_patch

DELAYS=stage_b.DELAYS
stats=previous.stats
exec(inspect.getsource(previous.verify),globals())


def latest(label):
    paths=sorted((HERE/'results/benchmarks').glob('*_fc_stage_c_'+label+'/summary.json'))
    passed=[p for p in paths if json.loads(p.read_text())['ok']]
    assert passed,label
    return passed[-1]


def export(v,formal):
    p=HERE/'work'/v/APP.name;lib=p/'model/generated/fc_int8';dest=HERE/'validated'/v;dest.mkdir(parents=True,exist_ok=True)
    for name in ('lib0.c','lib1.c','lib2.c','dab_tinie_c28.c','tvmgen_default.h','dab_npu_contract.h','manifest.json','mod.a','build_commands.json','rebuild.log'):
        shutil.copy2(lib/name,dest/name)
    for name in ('fc_stage_a_input.h','stage_b_delay.h'):shutil.copy2(p/name,dest/name)
    shutil.copy2(p/'dab_nn.c',dest/'dab_nn.stage_c.c')
    if (lib/'tinie_mem_write_fast.asm').exists():shutil.copy2(lib/'tinie_mem_write_fast.asm',dest/'tinie_mem_write_fast.asm')
    assembly=HERE/'assembly'/v;assembly.mkdir(parents=True,exist_ok=True)
    for glob in ('*.asm','*.lst'):
        for f in lib.glob(glob):shutil.copy2(f,assembly/f.name)
    dump(dest/'acceptance.json',dict(ok=True,variant=v,ordinary_library=True,detail_profile=False,
        formal=formal,correctness='../../results/board_correctness.json',power_output_enabled=False,
        library_sha256=sha(dest/'mod.a'),parameter_residency=False,
        scope='B1-only experimental package; full matching sources and headers required; not installed into production'))


def main():
    protect();board=json.loads((HERE/'results/board_correctness.json').read_text());assert board['ok']
    variants=board['variants'];assert set(('C1A','C1B','C2')).issubset(variants)
    formal={};detail={};sources={}
    reference=json.loads((HERE/'results/capture/C1A.json').read_text())['points'];assert len(reference)==570
    baseline_driver=(BASE/'dab_tinie_c28.c').read_text(encoding='utf-8')
    for v in variants:
        assert json.loads((HERE/f'results/capture/{v}.json').read_text())['points']==reference
        formal[v]=verify(latest(v),v,False);detail[v]=verify(latest(v+'_detail'),v,True)
        p=HERE/'work'/v/APP.name;lib=p/'model/generated/fc_int8'
        expected=baseline_driver
        if v in ('C2','C3','C5'):expected=param_patch(expected)
        if v in ('C4','C5'):expected=mmr_patch(expected)
        assert (lib/'dab_tinie_c28.c').read_text(encoding='utf-8')==expected
        kernel=HERE/'generated/C1B/lib2.c' if v in ('C1B','C3') else BASE/'lib2.c'
        for name in ('lib0.c','lib1.c','tvmgen_default.h','dab_npu_contract.h'):assert sha(lib/name)==sha(BASE/name)
        assert sha(lib/'lib2.c')==sha(kernel)
        assert sha(p/'fc_stage_a_input.h')==sha(BASE/'fc_stage_a_input.h')
        assert (p/'dab_nn.c').read_text(encoding='utf-8')==(BASE/'dab_nn.stage_b.c').read_text(encoding='utf-8')
        m=json.loads((lib/'manifest.json').read_text());assert m['library_sha256']==sha(lib/'mod.a') and not m['detail_profile']
        image=p/BUILD/'dab_control_f28p550.out';assert sha(image)==formal[v]['rows'][-1]['out_sha256']
        for i in range(3):
            path=latest(v).parent/f'round_{i+1}.map';text=path.read_text(encoding='utf-8',errors='replace')
            assert re.search(r'0000e000\s+00000060\s+mod.a\s*:\s*lib0.obj',text,re.I)
            assert re.search(r'0000e060\s+00000008\s+dab_nn.obj\s*\(ramgs1\)',text,re.I)
            assert 'RUN ADDR = 00009000' in text and 'RUN ADDR = 00009800' in text
        sources[v]=dict(network_parameters_instructions_unchanged=True,exact_expected_driver=True,
          input_address='0xe060',workspace_address='0xe000',driver_run_section='LS2 0x9000',constant_run_section='LS3 0x9800',
          library_sha256=sha(lib/'mod.a'),final_image_sha256=sha(image))
        export(v,formal[v])
    base=formal['C1A']['pooled']['mean_us'];best=min(variants,key=lambda v:formal[v]['pooled']['mean_us'])
    for label,values in (('formal',formal),('detail',detail)):
        rows=[row for data in values.values() for row in data['rows']]
        with (HERE/f'results/{label}_performance.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(ok=True,variants=variants,formal=formal,detail=detail,artifact_checks=sources,
      best=best,baseline_mean_us=base,best_mean_us=formal[best]['pooled']['mean_us'],
      best_reduction_percent=100*(1-formal[best]['pooled']['mean_us']/base),
      mean_reduction_percent={v:100*(1-formal[v]['pooled']['mean_us']/base) for v in variants},
      formal_runs=3*len(variants),formal_samples=3000*len(variants),detail_runs=3*len(variants),detail_samples=3000*len(variants),
      correctness_points_each=570,OST_locked=True,power_output_enabled=False,
      production_library_modified=False,stage_A_B_unchanged=True,
      decisions={'C1B':'space saving only; slower, not recommended','C3':'not run: combining rejected compressed decoder has no evidence of benefit',
      'residency':'not attempted: no verified C28 base relocation and lifetime contract'})
    dump(HERE/'results/final_verification.json',result);protect()
    print(json.dumps(dict(ok=True,best=best,means_us={v:formal[v]['pooled']['mean_us'] for v in variants},
      reduction_percent=result['best_reduction_percent'],formal_samples=result['formal_samples']),ensure_ascii=False))


if __name__=='__main__':main()
