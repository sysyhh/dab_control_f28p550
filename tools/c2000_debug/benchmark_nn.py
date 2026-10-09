"""Read finite NN benchmarks through the existing real-board debug CLI.

Requires firmware's initialization to request the finite benchmark automatically.
No expression writes, power-start commands or pauses inside the measured batch.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'dab_control_f28p550'
FIELDS = ('samples', 'lastTicks', 'minTicks', 'maxTicks', 'totalTicks', 'meanUs')
TIMES = ('prepare', 'fpuForward', 'npuSubmit', 'npuObserved', 'npuCompletion', 'publish', 'endToEnd')
STAGES = ('input', 'packedCopyAndPack', 'unpack', 'hiddenConvert', 'parameters',
          'instructions', 'registers', 'layer0Wait', 'layer1Wait', 'layer2Wait', 'layer3Wait', 'output')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('fpu', 'npu'), required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--run-ms', type=int, default=1000)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10: parser.error('repeats must be 1..10')
    report_dir = ROOT / 'tools/c2000_debug/benchmarks' / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + args.label)
    report_dir.mkdir(parents=True)
    report = {'ok': False, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'backend': args.backend, 'label': args.label, 'continuous_run_ms': args.run_ms,
              'firmware_sources_sha256': {p: sha(APP/p) for p in ('dab_nn.c', 'dab_main.c', 'dab_board_config.h')},
              'runs': []}
    if args.backend == 'npu':
        report['model_manifest'] = json.loads((APP/'model/generated/npu/manifest.json').read_text(encoding='utf-8'))
        if sha(APP/'model/generated/npu/mod.a') != report['model_manifest']['library_sha256']:
            raise RuntimeError('Model archive differs from manifest; compile the model again')
    meta = ['g_debugBuildId', 'g_dabState', 'g_protectFlags.all', 'g_startRequested',
            'g_controlHeartbeat', 'g_backgroundHeartbeat', 'g_nnBenchmarkState',
            'g_nnBenchmarkCompleted', 'g_nnBenchmarkWarmupCompleted', 'g_nnBenchmarkIterations',
            'g_nnBenchmarkWarmup', 'g_nnBenchmarkVin', 'g_nnBenchmarkRejectReason', 'g_nnTimeoutCount']
    expressions = meta + [f'g_nnLastOutput[{i}]' for i in range(4)]
    heads = ('timerHz', 'timerReadOverheadTicks', 'backend', 'revision', 'frozen', 'rejectedOutputs')
    expressions += ['g_nnTiming.'+x for x in heads]
    expressions += [f'g_nnTiming.{t}.{f}' for t in TIMES for f in FIELDS]
    expressions += ['g_nnNpuDetail.instrumented', 'g_nnNpuDetail.invalidPairs']
    expressions += [f'g_nnNpuDetail.lastCalls[{i}]' for i in range(12)]
    expressions += [f'g_nnNpuDetail.stage[{i}].{f}' for i in range(12) for f in FIELDS]
    try:
        for index in range(args.repeats):
            command = [sys.executable, str(ROOT/'c2000_debug.py'), '--run-test', '--rebuild-nn', '--build-dir',
                       'CPU1_LAUNCHXL_NPU_FLASH' if args.backend == 'npu' else 'CPU1_LAUNCHXL_FLASH',
                       '--run-ms', str(args.run_ms), '--samples', '1', '--timeout-ms', '60000']
            for expression in expressions: command += ['--expr', expression]
            if args.backend == 'npu' and report['model_manifest'].get('optimization_level',0) >= 5:
                command.append('--verify-npu-const')
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=240)
            (report_dir/f'run_{index+1}.json').write_text(process.stdout, encoding='utf-8', newline='\n')
            raw = json.loads(process.stdout)
            if process.returncode or not raw['ok']: raise RuntimeError(f'Debug CLI failed: {raw.get("errors")}')
            values = raw['variables']
            timing = {key: values['g_nnTiming.'+key] for key in heads}
            for t in TIMES: timing[t] = {f: values[f'g_nnTiming.{t}.{f}'] for f in FIELDS}
            detail = {'instrumented': values['g_nnNpuDetail.instrumented'],
                      'invalidPairs': values['g_nnNpuDetail.invalidPairs'],
                      'lastCalls': [values[f'g_nnNpuDetail.lastCalls[{i}]'] for i in range(12)],
                      'stage': [{f: values[f'g_nnNpuDetail.stage[{i}].{f}'] for f in FIELDS} for i in range(12)],
                      'stage_names': list(STAGES)}
            checks = {
                'benchmark_done': values['g_nnBenchmarkState'] == 2,
                'samples_1000': values['g_nnBenchmarkCompleted'] == timing['endToEnd']['samples'] == 1000,
                'warmup_10': values['g_nnBenchmarkWarmupCompleted'] == 10,
                'vin_90': values['g_nnBenchmarkVin'] == 90,
                'backend_matches': timing['backend'] == (args.backend == 'npu'),
                'frozen': bool(timing['frozen']),
                'no_rejections': timing['rejectedOutputs'] == values['g_nnBenchmarkRejectReason'] == 0,
                'no_timeout': values['g_nnTimeoutCount'] == 0,
                'standby': values['g_dabState'] == 1,
                'no_fault_or_start': values['g_protectFlags.all'] == values['g_startRequested'] == 0,
                'all_power_pwm_ost_latched': all(raw['registers'][name] & 4 for name in
                                               ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG')),
                'trace_pairs': detail['invalidPairs'] == 0,
                'timer_150mhz': timing['timerHz'] == 150000000,
                'foreground_and_control_running': values['g_controlHeartbeat'] > 0 and values['g_backgroundHeartbeat'] > 0,
            }
            statistics = [timing[t] for t in TIMES] + detail['stage']
            checks['tick_statistics_consistent'] = all(not s['samples'] or
                (s['minTicks'] <= s['totalTicks']/s['samples'] <= s['maxTicks'] and
                 abs(s['meanUs'] - s['totalTicks']*1.e6/s['samples']/timing['timerHz']) < .001)
                for s in statistics)
            if args.backend == 'fpu': checks['forward_samples'] = timing['fpuForward']['samples'] == 1000
            if args.backend == 'npu':
                if report['model_manifest'].get('optimization_level',0) >= 5:
                    checks['ram_constants_match_flash'] = raw.get('model_constant_copy',{}).get('matches') is True
                checks['detail_mode_matches_library'] = bool(detail['instrumented']) == report['model_manifest']['detail_profile']
                checks['completion_samples'] = timing['npuCompletion']['samples'] == 1000
                checks['known_vin90_output'] = [values[f'g_nnLastOutput[{i}]'] for i in range(4)] == [.4375,.25,0.,1.]
                if detail['instrumented']:
                    checks['four_layers'] = detail['lastCalls'][4:7] == [4,4,4] and detail['lastCalls'][7:11] == [1,1,1,1]
                    checks['no_hidden_conversion'] = detail['lastCalls'][3] == 0
            report['runs'].append({'raw_result': str(Path(raw['run_dir'])/'result.json'),
                                   'out_sha256': raw['out_sha256'], 'metadata': {k:values[k] for k in meta},
                                   'output': [values[f'g_nnLastOutput[{i}]'] for i in range(4)],
                                   'timing': timing, 'detail': detail, 'checks': checks})
            if not all(checks.values()): raise RuntimeError(f'Board checks failed: {checks}')
        report['ok'] = True
    except Exception as error:
        report['error'] = str(error)
    finally:
        report['report_path'] = str(report_dir/'summary.json')
        (report_dir/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8', newline='\n')
        print(json.dumps({'ok':report['ok'], 'report':report['report_path'], 'runs':len(report['runs']),
                          'endToEndMeanUs':[r['timing']['endToEnd']['meanUs'] for r in report['runs']],
                          'error':report.get('error')},ensure_ascii=False))
    return 0 if report['ok'] else 1

if __name__ == '__main__': sys.exit(main())
