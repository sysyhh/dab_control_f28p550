"""Isolated C candidates, using Stage B's unchanged timing and delay method."""
import argparse
import inspect
import json
from pathlib import Path
import shutil
import sys
from common_c import *

VARIANTS=('C1A','C1B')
DELAYS=stage_b.DELAYS
set_delay=stage_b.set_delay


def prepare(variant,detail=False,capture=False):
    assert variant in ('C1A','C1B','C2','C3','C4','C5','AUDIT','AUDIT_FAST')
    label=variant+('_capture' if capture else '_detail' if detail else '')
    project=HERE/'work'/label/APP.name
    if project.exists():return project
    project.mkdir(parents=True)
    for p in APP.iterdir():
        if p.is_file() and p.suffix in ('.c','.h','.cmd','.syscfg'):shutil.copy2(p,project/p.name)
    for folder in ('device','targetConfigs'):shutil.copytree(APP/folder,project/folder)
    shutil.copytree(APP/BUILD,project/BUILD,ignore=shutil.ignore_patterns('*.obj','*.out','*.map','*.d','*.d_raw','*linkInfo.xml','dab_nn_auto_benchmark.opt'))
    for p in (project/BUILD).rglob('*'):
        if not p.is_file():continue
        try:s=p.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        p.write_text(s.replace(APP.as_posix(),project.as_posix()).replace(str(APP),str(project)),encoding='utf-8',newline='\n')
    lib=project/'model/generated/fc_int8';lib.mkdir(parents=True)
    for name in ('lib0.c','lib1.c','lib2.c','tvmgen_default.h','dab_npu_contract.h','manifest.json','mod.a','dab_tinie_c28.c'):
        shutil.copy2(BASE/name,lib/name)
    if variant in ('C1B','C3'):shutil.copy2(HERE/'generated/C1B/lib2.c',lib/'lib2.c')
    if variant in ('C2','C3','C5','AUDIT_FAST'):
        assert (HERE/'results/parameter_candidate_admission.json').exists()
        from parameter_candidate import patch
        (lib/'dab_tinie_c28.c').write_text(patch((lib/'dab_tinie_c28.c').read_text(encoding='utf-8')),encoding='utf-8')
        shutil.copy2(HERE/'candidates/tinie_mem_write_fast.asm',lib/'tinie_mem_write_fast.asm')
    if variant in ('C4','C5'):
        assert json.loads((HERE/'results/static_mmr_host.json').read_text())['ok']
        from static_mmr import patch as patch_mmr
        p=lib/'dab_tinie_c28.c';p.write_text(patch_mmr(p.read_text(encoding='utf-8')),encoding='utf-8')
    for name in ('lib1.c','dab_tinie_c28.c','dab_npu_contract.h'):
        p=lib/name;p.write_text(p.read_text(encoding='utf-8').replace('#define DAB_NPU_DETAIL_PROFILE 0',f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}'),encoding='utf-8',newline='\n')
    shutil.copy2(BASE/'dab_nn.stage_b.c',project/'dab_nn.c')
    shutil.copy2(BASE/'fc_stage_a_input.h',project/'fc_stage_a_input.h');set_delay(project,0)
    m=json.loads((lib/'manifest.json').read_text(encoding='utf-8'));m.update(stage_c_variant=variant,detail_profile=detail,
        validation_capture=capture,compressed_mmr=variant in ('C1B','C3'),fast_parameter_copy=variant in ('C2','C3','C5'),static_mmr=variant in ('C4','C5'),hardware_tasks=4)
    dump(lib/'manifest.json',m);recompile(project)
    return project


def recompile(project):
    lib=project/'model/generated/fc_int8';a=stage_b.stage_a
    includes=[a.CGT/'include',a.SDK/'driverlib/f28p55x/driverlib',a.SDK/'device_support/f28p55x/common/include',project,a.TVM/'3rdparty/tinie-api',a.TVM/'standalone_crt/include']
    cmd=[a.CGT/'bin/cl2000.exe','--compile_only','--abi=eabi','-O3','--opt_for_speed=5','--c99','-v28','-ml','-mt','--gen_func_subsections','--float_support=fpu32']+[f'--include_path={p}' for p in includes]
    log='';commands=[]
    for name in ('lib0.c','lib1.c','lib2.c','dab_tinie_c28.c'):
        extra=['--output_file=tinie_c28.obj','--keep_asm','--src_interlist','--asm_listing'] if name.startswith('dab_') else []
        full=cmd+extra+[lib/name];commands.append([str(x) for x in full]);log+=run(full,cwd=lib)
    objects=['lib0.obj','lib1.obj','lib2.obj','tinie_c28.obj']
    if (lib/'tinie_mem_write_fast.asm').exists():
        full=cmd+[lib/'tinie_mem_write_fast.asm'];commands.append([str(x) for x in full]);log+=run(full,cwd=lib);objects.append('tinie_mem_write_fast.obj')
    log+=run([a.CGT/'bin/ar2000.exe','r','mod.a']+objects,cwd=lib)
    (lib/'rebuild.log').write_text(log,encoding='utf-8');dump(lib/'build_commands.json',commands)
    m=json.loads((lib/'manifest.json').read_text(encoding='utf-8'))
    for key,name in [('library_sha256','mod.a'),('runtime_sha256','lib1.c'),('kernel_sha256','lib2.c'),('driver_sha256','dab_tinie_c28.c'),('header_sha256','tvmgen_default.h')]:m[key]=sha(lib/name)
    dump(lib/'manifest.json',m)


# Reuse the already tested framework in a Stage C namespace, without editing B.
exec(inspect.getsource(stage_b.debug_cli),globals())
bench_source=inspect.getsource(stage_b.bench).replace('def bench(','def _bench(').replace('import run_stage_b as stage_b','import run_stage_c as stage_b').replace("'fc_stage_b_'","'fc_stage_c_'")
bench_source=bench_source.replace("shutil.copy2(raw['out'],report_dir/f'round_{index+1}.out')", "shutil.copy2(raw['out'],report_dir/f'round_{index+1}.out')\n            shutil.copy2(Path(raw['out']).with_suffix('.map'),report_dir/f'round_{index+1}.map')")
exec(bench_source,globals())


def bench(variant,detail=False):
    assert variant in json.loads((HERE/'results/board_correctness.json').read_text())['variants']
    _bench(variant,detail)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','board','detail'));p.add_argument('--variant',default=None)
    args=p.parse_args();variants=(args.variant,) if args.variant else VARIANTS
    for v in variants:
        if args.action=='prepare':
            for detail in (False,True):print(prepare(v,detail),flush=True)
        else:bench(v,args.action=='detail')
    protect()


if __name__=='__main__':main()
