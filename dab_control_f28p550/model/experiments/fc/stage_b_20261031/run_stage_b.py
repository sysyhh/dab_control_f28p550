"""Stage B isolated builds. Reuses Stage A's verified application and transform."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from audit_stage_b import HERE,FC,APP,ROOT,STAGE_A,NNC,sha,dump,protect
sys.path.insert(0,str(STAGE_A))
import run_stage_a as stage_a
from patch_stage_a import transform,replace_once

BUILD=stage_a.BUILD
VARIANTS=('A4','B1')
DELAYS=(0,2550,6450) # 0,17,43 us at 150 MHz, applied after warmup.


def run(cmd,cwd=None,timeout=240):
    p=subprocess.run([str(x) for x in cmd],cwd=cwd or ROOT,capture_output=True,
                     text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if p.returncode:
        raise RuntimeError(f'{cmd[0]} exit {p.returncode}\n{p.stdout[-6000:]}\n{p.stderr[-6000:]}')
    return p.stdout


def adapt_stage_a(code):
    # Only adapt the established optimizer's checked hidden width and odd padding.
    # Its actual identity/input/dataflow transformations are reused unchanged.
    wide='for (int32_t ax1 = 0; ax1 < 32; ++ax1)'
    narrow='for (int32_t ax1 = 0; ax1 < 29; ++ax1)'
    code=replace_once(code,wide,narrow)
    code=transform(code,'A4')
    code=replace_once(code,narrow,wide)
    code=replace_once(code,'  ((uint16_t*)global_workspace_0_var)[46] &= 0x00ffU;\n','')
    return code


def phase_application(code):
    prefix='''#include "stage_b_delay.h"
volatile uint32_t g_fcStageBDelayTicks = FC_STAGE_B_DELAY_TICKS;
volatile uint32_t g_fcStageBActualDelayTicks;
volatile uint32_t g_fcStageBFirstFormalTick;
static bool s_fcStageBPhaseApplied;
'''
    # Insert after the real includes so C28 typedefs and bool are available.
    code=replace_once(code,'static volatile bool s_busy;',prefix+'static volatile bool s_busy;')
    target='    s_benchJob = true;\n    serviceInference(s_benchVin, true);'
    insertion='''    if (!s_fcStageBPhaseApplied && !s_busy &&
        g_nnBenchmarkWarmupCompleted == s_benchWarmup && g_nnBenchmarkCompleted == 0U)
    {
        uint32_t begin = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        while (begin - CPUTimer_getTimerCount(CPUTIMER2_BASE) < g_fcStageBDelayTicks) {}
        g_fcStageBActualDelayTicks = begin - CPUTimer_getTimerCount(CPUTIMER2_BASE);
        g_fcStageBFirstFormalTick = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        s_fcStageBPhaseApplied = true;
    }
'''
    return replace_once(code,target,insertion+target)


def prepare(variant,detail=False,capture=False):
    assert variant in VARIANTS
    gate=json.loads((HERE/'results/mapping_gate.json').read_text())
    assert gate['ok'] and gate['B1']['hardware_tasks']==4
    label=variant+('_capture' if capture else '_detail' if detail else '')
    project=HERE/'work'/label/APP.name
    if project.exists():
        assert (project/'model/generated/fc_int8/manifest.json').exists(),project
        return project
    project.mkdir(parents=True)
    for p in APP.iterdir():
        if p.is_file() and p.suffix in ('.c','.h','.cmd','.syscfg'):shutil.copy2(p,project/p.name)
    for folder in ('device','targetConfigs'):shutil.copytree(APP/folder,project/folder)
    origin=APP/BUILD;build=project/BUILD
    shutil.copytree(origin,build,ignore=shutil.ignore_patterns('*.obj','*.out','*.map','*.d','*.d_raw','*linkInfo.xml','dab_nn_auto_benchmark.opt'))
    for p in build.rglob('*'):
        if not p.is_file():continue
        try:s=p.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        s=s.replace(APP.as_posix(),project.as_posix()).replace(str(APP),str(project))
        p.write_text(s,encoding='utf-8',newline='\n')
    source=STAGE_A/'validated/A4' if variant=='A4' else HERE/'generated/B1_packaged'
    lib=project/'model/generated/fc_int8';lib.mkdir(parents=True)
    for name in ('lib0.c','lib1.c','lib2.c','tvmgen_default.h','dab_npu_contract.h','manifest.json','mod.a'):
        shutil.copy2(source/name,lib/name)
    # Allocate the same workspace capacity for both shapes, including reserve.
    lib0=(lib/'lib0.c').read_text(encoding='utf-8')
    lib0=lib0.replace('TINIE_NPU_EXTRA_BUF_PADDING + 61','TINIE_NPU_EXTRA_BUF_PADDING + 64')
    (lib/'lib0.c').write_text(lib0,encoding='utf-8',newline='\n')
    code=(lib/'lib1.c').read_text(encoding='utf-8')
    if variant=='B1':code=adapt_stage_a(code)
    code=code.replace('#define DAB_NPU_DETAIL_PROFILE 0',f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'lib1.c').write_text(code,encoding='utf-8',newline='\n')
    driver=(STAGE_A/'validated/A4/dab_tinie_c28.c').read_text(encoding='utf-8')
    driver=driver.replace('#define DAB_NPU_DETAIL_PROFILE 0',f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'dab_tinie_c28.c').write_text(driver,encoding='utf-8',newline='\n')
    contract=(lib/'dab_npu_contract.h').read_text(encoding='utf-8').replace('#define DAB_NPU_DETAIL_PROFILE 0',f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'dab_npu_contract.h').write_text(contract,encoding='utf-8',newline='\n')
    header=(lib/'tvmgen_default.h').read_text(encoding='utf-8').replace('Tensor[(1, 16), float32]',
        'C28 packed int8: uint16_t[8], low byte first; input quantization in application')
    (lib/'tvmgen_default.h').write_text(header,encoding='utf-8',newline='\n')
    app=(STAGE_A/'validated/A4/dab_nn.stage_a.c').read_text(encoding='utf-8')
    (project/'dab_nn.c').write_text(phase_application(app),encoding='utf-8',newline='\n')
    shutil.copy2(STAGE_A/'validated/A4/fc_stage_a_input.h',project/'fc_stage_a_input.h')
    set_delay(project,0)
    m=json.loads((lib/'manifest.json').read_text(encoding='utf-8'))
    m.update(stage_b_variant=variant,detail_profile=detail,validation_capture=capture,
             io_dtype='packed_int8_input_float32_output',hardware_tasks=5 if variant=='A4' else 4,
             expected_vin90_output=[.453125,.25,0.,1.],application_prequant=True,
             hidden_identity=True,packed_transitions=True,resident_parameters=False)
    dump(lib/'manifest.json',m)
    recompile(project)
    return project


def set_delay(project,index):
    (project/'stage_b_delay.h').write_text(f'#define FC_STAGE_B_DELAY_TICKS {DELAYS[index]}UL\n',encoding='utf-8')


def recompile(project):
    lib=project/'model/generated/fc_int8'
    includes=[stage_a.CGT/'include',stage_a.SDK/'driverlib/f28p55x/driverlib',stage_a.SDK/'device_support/f28p55x/common/include',
              project,stage_a.TVM/'3rdparty/tinie-api',stage_a.TVM/'standalone_crt/include']
    cmd=[stage_a.CGT/'bin/cl2000.exe','--compile_only','--abi=eabi','-O3','--opt_for_speed=5','--c99',
         '-v28','-ml','-mt','--gen_func_subsections','--float_support=fpu32']+[f'--include_path={p}' for p in includes]
    log=''
    for name in ('lib0.c','lib1.c','lib2.c','dab_tinie_c28.c'):
        out=['--output_file=tinie_c28.obj'] if name.startswith('dab_') else []
        log+=run(cmd+out+[lib/name],cwd=lib)
    log+=run([stage_a.CGT/'bin/ar2000.exe','r','mod.a','lib0.obj','lib1.obj','lib2.obj','tinie_c28.obj'],cwd=lib)
    (lib/'rebuild.log').write_text(log,encoding='utf-8')
    m=json.loads((lib/'manifest.json').read_text(encoding='utf-8'))
    for key,name in [('library_sha256','mod.a'),('runtime_sha256','lib1.c'),('kernel_sha256','lib2.c'),
                     ('driver_sha256','dab_tinie_c28.c'),('header_sha256','tvmgen_default.h')]:m[key]=sha(lib/name)
    dump(lib/'manifest.json',m)


def debug_cli(capture=False):
    source=(ROOT/'c2000_debug.py').read_text(encoding='utf-8')
    source=source.replace('ROOT = Path(__file__).resolve().parent',f'ROOT = Path({str(ROOT)!r})')
    source=source.replace("ROOT / 'tools/c2000_debug/runs'",f'Path({str(HERE/"results/debug_runs")!r})')
    if capture:source=source.replace("ROOT / 'tools/c2000_debug/debug_worker.js'",f'Path({str(HERE/"capture_worker.js")!r})')
    path=HERE/('capture_cli.py' if capture else 'debug_cli.py');path.write_text(source,encoding='utf-8');return path


def bench(variant,detail=False):
    assert json.loads((HERE/'results/host_verification.json').read_text())['ok']
    assert json.loads((HERE/'results/cpu_graph_host.json').read_text())['ok']
    assert json.loads((HERE/'results/board_correctness.json').read_text())['ok']
    project=prepare(variant,detail=detail);cli=debug_cli()
    source=(ROOT/'tools/c2000_debug/benchmark_nn.py').read_text(encoding='utf-8')
    source=source.replace("ROOT = Path(__file__).resolve().parents[2]",f'ROOT = Path({str(ROOT)!r})')
    source=source.replace("APP = ROOT / 'dab_control_f28p550'",f'APP = Path({str(project)!r})')
    source=source.replace("ROOT / 'tools/c2000_debug/benchmarks'",f'Path({str(HERE/"results/benchmarks")!r})')
    source=source.replace("str(ROOT/'c2000_debug.py')",repr(str(cli)))
    source=source.replace("'--nn-auto-benchmark', '--build-dir', spec['build'],",
        "'--nn-auto-benchmark', '--project', str(APP), '--build-dir', spec['build'],")
    source=source.replace("    expressions = meta +", "    meta += ['g_fcStageBDelayTicks','g_fcStageBActualDelayTicks','g_fcStageBFirstFormalTick']\n    expressions = meta +")
    source=source.replace('        for index in range(args.repeats):',f'''        for index in range(args.repeats):
            sys.path.insert(0,{str(HERE)!r})
            import run_stage_b as stage_b
            stage_b.set_delay(APP,index)
            for obj in (APP/spec['build']).rglob('*.obj'): obj.unlink()
            stage_b.recompile(APP)
            round_manifest=json.loads((APP/'model/generated/fc_int8/manifest.json').read_text(encoding='utf-8'))
            (report_dir/f'round_{{index+1}}_library_rebuild.log').write_text((APP/'model/generated/fc_int8/rebuild.log').read_text(encoding='utf-8'),encoding='utf-8')
''')
    source=source.replace("report['runs'].append({'raw_result':", "report['runs'].append({'round_manifest':round_manifest, 'raw_result':")
    source=source.replace("checks['hardware_isr_count'] = timing['npuIsrLastCount'] >= 4",f"checks['hardware_isr_count'] = timing['npuIsrLastCount'] == {5 if variant=='A4' else 4}")
    # Retain each independently built image, not just its checksum.
    source=source.replace("            values = raw['variables']",'''            import shutil
            shutil.copy2(raw['out'],report_dir/f'round_{index+1}.out')
            (report_dir/f'round_{index+1}_source_manifest.json').write_text(json.dumps(dict(application_sha256=sha(APP/'dab_nn.c'),delay_header=(APP/'stage_b_delay.h').read_text(),library=round_manifest),indent=2),encoding='utf-8')
            values = raw['variables']''')
    script=project/'benchmark_stage_b.py';script.write_text(source,encoding='utf-8')
    label='fc_stage_b_'+variant+('_detail' if detail else '')
    out=run([sys.executable,script,'--backend','fc_int8','--label',label,'--repeats',3],timeout=900)
    print(out.strip(),flush=True)
    result=json.loads(out);assert result['ok'],result
    protect();return result


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','board','detail'));p.add_argument('--variant',choices=VARIANTS)
    args=p.parse_args();variants=(args.variant,) if args.variant else VARIANTS
    for variant in variants:
        if args.action=='prepare':
            for detail in (False,True):print(prepare(variant,detail),flush=True)
        else:bench(variant,detail=args.action=='detail')
    protect()


if __name__=='__main__':main()
