#!/usr/bin/env python3
"""One-shot build/load/run/halt/read for the local F28P550 LaunchPad. Stdlib only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DEFAULT_EXPRESSIONS = ['g_debugBuildId', 'g_backgroundHeartbeat', 'g_controlHeartbeat', 'g_dabState',
                       'g_protectFlags.all',
                       'g_startRequested', 'g_stopRequested', 'g_sensing.vout_n_ave',
                       'g_sensing.il_ave']
# F28P55x word addresses from C2000Ware hw_memmap.h + EPWM_O_TZFLG (0x93).
PWM_TRIP_REGISTERS = {'EPWM7_TZFLG': 0x4693, 'EPWM4_TZFLG': 0x4393,
                      'EPWM5_TZFLG': 0x4493, 'EPWM10_TZFLG': 0x4993}


def attach_configuration(source, destination):
    # 默认 F28P55x GEL 的 OnTargetConnect/OnPreFileLoaded 会复位。
    # 仅当前取数会话覆盖 CPU GEL，原工程的目标配置保持不变。
    tree = ET.parse(source)
    device = tree.find('.//device')
    if device is None:
        raise ValueError('Attach requires an explicit F28P550 device configuration')
    router = device.find("router[@id='IcePick_C_0']")
    if router is None:
        raise ValueError('Attach requires the F28P550 IcePick_C_0 router')
    subpath = router.find("subpath[@id='Subpath_0']")
    if subpath is None:
        subpath = ET.SubElement(router, 'subpath', {'id':'Subpath_0'})
        ET.SubElement(subpath, 'property', {'Type':'numericfield','Value':'0x10','id':'Port Number'})
    cpu = subpath.find("cpu[@id='C28xx_CPU1']")
    if cpu is None:
        cpu = ET.SubElement(subpath, 'cpu', {'HW_revision':'1.0','XML_version':'1.0',
                            'description':'C28xxCPU','id':'C28xx_CPU1','isa':'TMS320C28xx'})
    gel = cpu.find("property[@id='GEL File']")
    if gel is None:
        gel = ET.SubElement(cpu, 'property', {'Type':'filepathfield','id':'GEL File'})
    gel.set('Value','')
    tree.write(destination, encoding='utf-8', xml_declaration=True)


def execute(command, cwd, log, timeout):
    with log.open('w', encoding='utf-8') as stream:
        process = subprocess.Popen([str(x) for x in command], cwd=cwd,
                                   stdout=stream, stderr=subprocess.STDOUT)
        try:
            return process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Kill only the process tree started by this invocation, never CCS UI.
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           capture_output=True, timeout=15)
            process.wait(timeout=15)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run-test', action='store_true', help='Build, load RAM, run, halt and read two snapshots')
    mode.add_argument('--build-only', action='store_true')
    mode.add_argument('--attach-only', action='store_true', help='Halt/read current target with existing symbols; never build, reset, load or run')
    parser.add_argument('--ccs', type=Path, default=Path(os.environ.get('CCS_ROOT', 'C:/ti/ccs2020/ccs')))
    parser.add_argument('--project', type=Path, default=ROOT / 'dab_control_f28p550')
    parser.add_argument('--build-dir', default='CPU1_RAM', help='Existing CCS-generated build directory')
    parser.add_argument('--rebuild-nn', action='store_true',
                        help='Force NN recompile/relink after restoring a generated model archive or contract')
    parser.add_argument('--nn-auto-benchmark', action='store_true',
                        help='Test build only: compile with DAB_NN_AUTO_BENCHMARK=1. Official firmware defaults to 0.')
    parser.add_argument('--verify-npu-const', action='store_true', help='Compare the LS3 model constants with their Flash load image')
    parser.add_argument('--read-e2e-ticks', action='store_true',
                        help='After halt, read g_nnBenchmarkE2eTicks[1000] from ramgs0')
    parser.add_argument('--ccxml', type=Path)
    parser.add_argument('--expr', action='append', help='Read scalar GEL expression; repeat for multiple expressions')
    parser.add_argument('--register', action='append', help='Register name; PC is always included')
    parser.add_argument('--run-ms', type=int, default=250)
    parser.add_argument('--samples', type=int, default=2)
    parser.add_argument('--timeout-ms', type=int, default=20000)
    args = parser.parse_args()
    if not (1 <= args.run_ms <= 60000 and 1 <= args.samples <= 20 and args.timeout_ms >= 1000):
        parser.error('run-ms: 1..60000; samples: 1..20; timeout-ms >= 1000')
    run_dir = ROOT / 'tools/c2000_debug/runs' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    run_dir.mkdir(parents=True)
    result = {'ok': False, 'build': 'NOT_RUN', 'connected': False, 'state': 'unknown',
              'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'run_dir': str(run_dir), 'errors': []}
    lock = ROOT / 'tools/c2000_debug/.lock'
    locked = False
    started = time.monotonic()
    try:
        # Prevent overlapping invocations from competing for the single probe.
        with lock.open('x') as stream:
            stream.write(str(os.getpid()))
        locked = True
        ccs, project = args.ccs.resolve(), args.project.resolve()
        build_dir = project / args.build_dir
        out = build_dir / (project.name + '.out')
        ccxml = (args.ccxml or project / 'targetConfigs/TMS320F28P550SJ9_LaunchPad.ccxml').resolve()
        make = ccs / 'utils/bin/gmake.exe'
        node = ccs / 'ccs_base/cloudagent/node.exe'
        for item in ([node, ccxml, out] if args.attach_only else [make, node, build_dir / 'makefile', ccxml]):
            if not item.is_file():
                raise FileNotFoundError(str(item))
        result.update(ccs=str(ccs), project=str(project), build_dir=str(build_dir), ccxml=str(ccxml))
        if args.attach_only:
            original_ccxml = ccxml
            ccxml = run_dir / 'attach_no_gel.ccxml'
            attach_configuration(original_ccxml, ccxml)
            result.update(source_ccxml=str(original_ccxml), ccxml=str(ccxml), attach_only=True)
        build_command = [make, '-j', '8']
        if args.rebuild_nn:
            if not (project / 'dab_nn.c').is_file():
                raise FileNotFoundError('rebuild-nn requires dab_nn.c in the selected project')
            # A restored archive/header may have older timestamps than the .out.
            # Recompiling this consumer also forces relink with the current archive.
            build_command += ['-W', '../dab_nn.c']
        if args.nn_auto_benchmark:
            makefile = (build_dir / 'makefile').read_text(encoding='utf-8', errors='replace')
            match = re.search(r'^GEN_OPTS__FLAG\s*:=\s*(.*)$', makefile, re.M)
            if not match:
                raise RuntimeError('CCS makefile missing GEN_OPTS__FLAG; cannot enable the NN benchmark test build')
            extra_opt = build_dir / 'dab_nn_auto_benchmark.opt'
            extra_opt.write_text('--define=DAB_NN_AUTO_BENCHMARK=1\n', encoding='utf-8')
            # Independent test build: official CCS FLASH/NPU_FLASH configs keep AUTO_BENCHMARK=0.
            build_command.append(
                'GEN_OPTS__FLAG=' + match.group(1).strip() + ' --cmd_file="dab_nn_auto_benchmark.opt"')
            if not args.rebuild_nn:
                build_command += ['-W', '../dab_nn.c']
        if not args.attach_only:
            rc = execute(build_command + ['all'], build_dir, run_dir / 'build.log', 180)
            result['build'] = 'PASS' if rc == 0 and out.is_file() else 'FAIL'
        if not args.attach_only and result['build'] != 'PASS':
            raise RuntimeError('Build failed; see build.log. No program loaded.')
        result.update(out=str(out), out_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
        if args.build_only:
            result['ok'] = True
        else:
            request = dict(ccs=str(ccs), ccxml=str(ccxml), out=str(out),
                           result=str(run_dir / 'hardware.json'),
                           expressions=args.expr or DEFAULT_EXPRESSIONS,
                           registers=list(dict.fromkeys(['PC'] + (args.register or []))),
                           memory_registers=PWM_TRIP_REGISTERS,
                           verify_npu_const=args.verify_npu_const,
                           read_e2e_ticks=args.read_e2e_ticks,
                           attach_only=args.attach_only,
                           run_ms=args.run_ms, samples=args.samples, timeout_ms=args.timeout_ms)
            request_file = run_dir / 'request.json'
            request_file.write_text(json.dumps(request, indent=2), encoding='utf-8')
            rc = execute([node, ROOT / 'tools/c2000_debug/debug_worker.js', request_file],
                         ROOT, run_dir / 'debug.log',
                         60 + args.samples * (args.run_ms / 1000 + args.timeout_ms / 1000))
            if not (run_dir / 'hardware.json').is_file():
                raise RuntimeError('Debugger returned no result; see debug.log')
            result.update(json.loads((run_dir / 'hardware.json').read_text(encoding='utf-8')))
            result['ok'] = rc == 0 and result['connected'] and (result.get('symbols_loaded') if args.attach_only else result['loaded']) and result['state'] == 'halted' and not result['errors']
            checks = {}
            samples = result.get('samples', [])
            if len(samples) >= 2:
                for name in ['g_backgroundHeartbeat', 'g_controlHeartbeat']:
                    first, last = samples[0]['values'].get(name), samples[-1]['values'].get(name)
                    if isinstance(first, int) and isinstance(last, int):
                        checks[name + '_advanced'] = 0 < ((last - first) & 0xffffffff) < 0x80000000
            if not args.attach_only and args.expr is None and 'g_debugBuildId' in result.get('variables', {}):
                checks['build_id_matches'] = result['variables']['g_debugBuildId'] == 0x20261030
                checks['standby'] = result['variables'].get('g_dabState') == 1
                checks['all_power_pwm_ost_latched'] = all(
                    result.get('registers', {}).get(name, 0) & 4 for name in PWM_TRIP_REGISTERS)
            result['checks'] = checks
            result['ok'] = result['ok'] and all(checks.values())
    except (Exception, KeyboardInterrupt) as exc:
        result['errors'].append({'stage': 'cli', 'message': str(exc) or type(exc).__name__})
    finally:
        if locked:
            lock.unlink(missing_ok=True)
        result['elapsed_s'] = round(time.monotonic() - started, 3)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        (run_dir / 'result.json').write_text(text, encoding='utf-8')
        print(text)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
