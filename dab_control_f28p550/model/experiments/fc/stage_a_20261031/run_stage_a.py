"""Reproducible isolated FC stage-A packages and real-board runs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from patch_stage_a import transform, application, INPUT_HEADER

HERE = Path(__file__).resolve().parent
APP = HERE.parents[3]
ROOT = APP.parent
NNC = ROOT / 'review_20261003/npu_integration_20261009/nnc211_env'
TVM = NNC / 'Lib/site-packages/tvm'
CGT = Path('E:/Software_Download/ti/ccs2020/ccs/tools/compiler/ti-cgt-c2000_22.6.2.LTS')
SDK = Path('E:/Software_Download/ti/c2000/C2000Ware_DigitalPower_SDK_5_05_01_00/c2000ware')
BASE = APP / 'model/generated/fc_int8'
BUILD = 'CPU1_LAUNCHXL_FC_INT8_FLASH'
VARIANTS = ('Baseline', 'A1', 'A2', 'A3', 'A4')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def run(cmd, cwd=None, timeout=240):
    p = subprocess.run([str(v) for v in cmd], cwd=cwd or ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if p.returncode:
        raise RuntimeError(f'{cmd[0]} returned {p.returncode}\n{p.stdout[-6000:]}\n{p.stderr[-6000:]}')
    return p.stdout


def provenance():
    sources = [p for folder in ('model/generated/npu', 'model/generated/fc_int8', 'model/generated/fc_int4')
               for p in (APP/folder).iterdir() if p.is_file()]
    sources += [APP/'dab_nn.c', APP/'.cproject', APP/'.settings/org.eclipse.core.resources.prefs',
                HERE.parent/'patch_fc_runtime.py', HERE.parent/'prove_fc_stage_a.py']
    data = {'head': run(['git', 'rev-parse', 'HEAD']).strip(),
            'status_before': run(['git', 'status', '--short']),
            'protected_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
            'criteria': ['host compiled actual CPU helpers: exhaustive uint8 identity',
                         'all 65536 packed words, odd/even lengths, live buffer guards',
                         '501 Vin points and adjacent binary32 transition values',
                         'actual IRQ graph and layer input/output equality under deterministic NPU stub',
                         'identical lib2, driver, parameters and instruction configuration',
                         'board layer snapshots equal; normal and detail builds kept separate',
                         '5 variants x 3 independent builds/loads x 1000 samples; 10 warmups',
                         '150 MHz, Vin=90, standby and four OST locks on every run']}
    dump(HERE/'provenance.json', data)
    (HERE/'original_drafts').mkdir(exist_ok=True)
    for p in sources[-2:]:
        shutil.copy2(p, HERE/'original_drafts'/p.name)


def assert_protected():
    data = json.loads((HERE/'provenance.json').read_text(encoding='utf-8'))
    changes = [p for p, h in data['protected_sha256'].items() if sha(ROOT/p) != h]
    dump(HERE/'results/protected_files.json', {'ok': not changes, 'changed': changes})
    if changes:
        raise RuntimeError('protected inputs changed: ' + str(changes))


def prepare(variant, detail=False, capture=False):
    label = variant + ('_capture' if capture else '_detail' if detail else '')
    project = HERE/'work'/label/APP.name
    if project.exists():
        if (project/'model/generated/fc_int8/manifest.json').exists():
            prior = json.loads((project/'model/generated/fc_int8/manifest.json').read_text(encoding='utf-8'))
            if prior.get('stage_a_variant') == variant:
                return project
        raise RuntimeError('refuse overwrite incomplete experiment: ' + str(project))
    project.mkdir(parents=True)
    for p in APP.iterdir():
        if p.is_file() and p.suffix in ('.c', '.h', '.cmd', '.syscfg'):
            shutil.copy2(p, project/p.name)
    for name in ('device', 'targetConfigs'):
        shutil.copytree(APP/name, project/name)
    build = project/BUILD
    shutil.copytree(APP/BUILD, build, ignore=shutil.ignore_patterns('*.obj', '*.out', '*.map', '*.d', '*.d_raw', '*linkInfo.xml', 'dab_nn_auto_benchmark.opt'))
    for p in build.rglob('*'):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        text = text.replace(APP.as_posix(), project.as_posix()).replace(str(APP), str(project))
        p.write_text(text, encoding='utf-8', newline='\n')
    lib = project/'model/generated/fc_int8'
    shutil.copytree(BASE, lib)
    code = transform((BASE/'lib1.c').read_text(encoding='utf-8'), variant)
    if capture:
        # Separate validation image: one completed inference's layer images, never timed as a score.
        code = '#include "fc_capture.h"\n' + code
        for layer in range(1, 5):
            if variant in ('A2', 'A4'):
                source = {1: '&global_workspace_0_var[32]', 2: '&global_workspace_0_var[0]',
                          3: '&global_workspace_0_var[32]', 4: '&global_workspace_0_var[16]'}[layer]
            else:
                source = {1: 'sid_3_let', 2: 'sid_7_let', 3: 'sid_11_let', 4: 'sid_15_let'}[layer]
            code = code.replace(f'case {layer}:', f'case {layer}:\n  FC_capture({layer-1}U, (uint16_t*){source});', 1)
        (project/'fc_capture.h').write_text('''#include <stdint.h>
volatile uint16_t g_fcLayerWords[4][16];
static void FC_capture(uint16_t layer, uint16_t *source) {
    uint16_t n = layer == 0 ? 15U : layer == 3 ? 2U : 8U;
    for (uint16_t i=0; i<n; ++i) g_fcLayerWords[layer][i] = source[i];
    if (layer == 0) g_fcLayerWords[0][14] &= 0x00ffU;
}
''', encoding='utf-8')
    code = code.replace('#define DAB_NPU_DETAIL_PROFILE 0', f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'lib1.c').write_text(code, encoding='utf-8', newline='\n')
    driver = (BASE/'dab_tinie_c28.c').read_text(encoding='utf-8')
    driver = driver.replace('#define DAB_NPU_DETAIL_PROFILE 0', f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'dab_tinie_c28.c').write_text(driver, encoding='utf-8', newline='\n')
    app = application((APP/'dab_nn.c').read_text(encoding='utf-8'), variant in ('A3', 'A4'))
    (project/'dab_nn.c').write_text(app, encoding='utf-8', newline='\n')
    (project/'fc_stage_a_input.h').write_text(INPUT_HEADER, encoding='utf-8', newline='\n')
    contract = (lib/'dab_npu_contract.h').read_text(encoding='utf-8').replace(
        '#define DAB_NPU_DETAIL_PROFILE 0', f'#define DAB_NPU_DETAIL_PROFILE {int(detail)}')
    (lib/'dab_npu_contract.h').write_text(contract, encoding='utf-8')
    if variant in ('A3', 'A4'):
        header = (lib/'tvmgen_default.h').read_text(encoding='utf-8').replace(
            'Tensor[(1, 16), float32]', 'C28 packed int8: uint16_t[8], low byte first; input quantization in application')
        (lib/'tvmgen_default.h').write_text(header, encoding='utf-8')
    includes = [CGT/'include', SDK/'driverlib/f28p55x/driverlib', SDK/'device_support/f28p55x/common/include',
                project, TVM/'3rdparty/tinie-api', TVM/'standalone_crt/include']
    cmd = [CGT/'bin/cl2000.exe', '--compile_only', '--abi=eabi', '-O3', '--opt_for_speed=5',
           '--c99', '-v28', '-ml', '-mt', '--gen_func_subsections', '--float_support=fpu32']
    cmd += [f'--include_path={p}' for p in includes]
    log = run(cmd+[lib/'lib1.c'], cwd=lib)
    objects = ['lib1.obj']
    if detail:
        log += run(cmd+['--output_file=tinie_c28.obj', lib/'dab_tinie_c28.c'], cwd=lib)
        objects += ['tinie_c28.obj']
    log += run([CGT/'bin/ar2000.exe', 'r', 'mod.a']+objects, cwd=lib)
    (lib/'rebuild.log').write_text(log, encoding='utf-8')
    manifest = json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    manifest.update(stage_a_variant=variant, detail_profile=detail, validation_capture=capture,
                    hidden_identity=variant in ('A1', 'A2', 'A4'), packed_transitions=variant in ('A2', 'A4'),
                    application_prequant=variant in ('A3', 'A4'), library_sha256=sha(lib/'mod.a'),
                    runtime_sha256=sha(lib/'lib1.c'), driver_sha256=sha(lib/'dab_tinie_c28.c'),
                    kernel_sha256=sha(lib/'lib2.c'), header_sha256=sha(lib/'tvmgen_default.h'))
    if variant in ('A3', 'A4'):
        manifest.update(io_dtype='packed_int8_input_float32_output')
    assert sha(lib/'lib2.c') == sha(BASE/'lib2.c')
    dump(lib/'manifest.json', manifest)
    return project


def bench(project, label, repeats):
    cli = make_debug_cli()
    source = (ROOT/'tools/c2000_debug/benchmark_nn.py').read_text(encoding='utf-8')
    source = source.replace("ROOT = Path(__file__).resolve().parents[2]", f'ROOT = Path({str(ROOT)!r})')
    source = source.replace("APP = ROOT / 'dab_control_f28p550'", f'APP = Path({str(project)!r})')
    source = source.replace("ROOT / 'tools/c2000_debug/benchmarks'", f'Path({str(HERE / "results/benchmarks")!r})')
    source = source.replace("'--nn-auto-benchmark', '--build-dir', spec['build'],",
                            "'--nn-auto-benchmark', '--project', str(APP), '--build-dir', spec['build'],")
    source = source.replace("str(ROOT/'c2000_debug.py')", repr(str(cli)))
    # Independent full build each round, including archive recompile and all application objects.
    source = source.replace('        for index in range(args.repeats):',
        f'''        for index in range(args.repeats):
            for obj in (APP/spec['build']).rglob('*.obj'):
                obj.unlink()
            import importlib.util
            sys.path.insert(0, {str(HERE)!r})
            mspec = importlib.util.spec_from_file_location('stage_runner', {str(Path(__file__).resolve())!r})
            module = importlib.util.module_from_spec(mspec)
            mspec.loader.exec_module(module)
            module.recompile_library(APP)
            round_manifest = json.loads((APP/'model/generated/fc_int8/manifest.json').read_text(encoding='utf-8'))
''')
    source = source.replace("report['runs'].append({'raw_result':", "report['runs'].append({'round_manifest': round_manifest, 'raw_result':")
    script = project/'benchmark_stage_a.py'
    script.write_text(source, encoding='utf-8')
    result = run([sys.executable, script, '--backend', 'fc_int8', '--label', label, '--repeats', repeats], timeout=repeats*240+60)
    print(result.strip(), flush=True)
    report = json.loads(result)
    if not report['ok']:
        raise RuntimeError(report)
    return report


def recompile_library(project):
    lib = project/'model/generated/fc_int8'
    includes = [CGT/'include', SDK/'driverlib/f28p55x/driverlib', SDK/'device_support/f28p55x/common/include',
                project, TVM/'3rdparty/tinie-api', TVM/'standalone_crt/include']
    cmd = [CGT/'bin/cl2000.exe', '--compile_only', '--abi=eabi', '-O3', '--opt_for_speed=5', '--c99',
           '-v28', '-ml', '-mt', '--gen_func_subsections', '--float_support=fpu32']
    cmd += [f'--include_path={p}' for p in includes]
    for filename in ('lib1.c', 'lib2.c', 'dab_tinie_c28.c'):
        args = ['--output_file=tinie_c28.obj'] if filename.startswith('dab_') else []
        run(cmd+args+[lib/filename], cwd=lib)
    run([CGT/'bin/ar2000.exe', 'r', 'mod.a', 'lib1.obj', 'lib2.obj', 'tinie_c28.obj'], cwd=lib)
    manifest = json.loads((lib/'manifest.json').read_text(encoding='utf-8'))
    manifest['library_sha256'] = sha(lib/'mod.a')
    for key, filename in (('runtime_sha256','lib1.c'),('kernel_sha256','lib2.c'),('driver_sha256','dab_tinie_c28.c')):
        manifest[key] = sha(lib/filename)
    dump(lib/'manifest.json', manifest)


def make_debug_cli(capture=False):
    source = (ROOT/'c2000_debug.py').read_text(encoding='utf-8')
    source = source.replace('ROOT = Path(__file__).resolve().parent', f'ROOT = Path({str(ROOT)!r})')
    source = source.replace("ROOT / 'tools/c2000_debug/runs'", f'Path({str(HERE/"results/debug_runs")!r})')
    if capture:
        source = source.replace("ROOT / 'tools/c2000_debug/debug_worker.js'", f'Path({str(HERE/"capture_worker.js")!r})')
    path = HERE/('capture_cli.py' if capture else 'debug_cli.py')
    path.write_text(source, encoding='utf-8')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'board', 'detail', 'protected'))
    parser.add_argument('--variant', choices=VARIANTS)
    args = parser.parse_args()
    variants = (args.variant,) if args.variant else VARIANTS
    if args.action == 'prepare':
        if not (HERE/'provenance.json').exists():
            provenance()
        for variant in variants:
            for detail in (False, True):
                p = prepare(variant, detail)
                print(p, flush=True)
    elif args.action in ('board', 'detail'):
        host = json.loads((HERE/'results/host_verification.json').read_text(encoding='utf-8'))
        if not host['ok']:
            raise RuntimeError('host verification has not passed')
        for variant in variants:
            label = variant + ('_detail' if args.action == 'detail' else '')
            project = HERE/'work'/label/APP.name
            bench(project, 'fc_stage_a_'+label, 1 if args.action == 'detail' else 3)
    assert_protected()


if __name__ == '__main__':
    main()
