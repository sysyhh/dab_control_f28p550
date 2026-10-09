"""Replay checks against archived real-board NN snapshots (no board needed)."""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('summaries', nargs='+', type=Path)
    args = parser.parse_args()
    count = 0
    for path in args.summaries:
        report = json.loads(path.read_text(encoding='utf-8'))
        assert report['ok'] and report['runs'], path
        for i, run in enumerate(report['runs']):
            raw = json.loads((path.parent/f'run_{i+1}.json').read_text(encoding='utf-8'))
            assert raw['ok'] and raw['loaded'] and raw['connected'] and raw['state']=='halted'
            assert raw['debugger_closed'] and not raw['errors']
            assert raw['out_sha256']==run['out_sha256']
            assert all(run['checks'].values())
            values, timing, detail = raw['variables'], run['timing'], run['detail']
            assert values['g_nnBenchmarkState']==2 and values['g_nnBenchmarkCompleted']==1000
            assert values['g_nnBenchmarkVin']==90 and values['g_nnBenchmarkWarmupCompleted']==10
            assert values['g_nnTimeoutCount']==values['g_protectFlags.all']==0
            assert values['g_dabState']==1 and values['g_startRequested']==0
            assert values['g_controlHeartbeat']>0 and values['g_backgroundHeartbeat']>0
            assert timing['frozen'] and timing['rejectedOutputs']==0 and timing['timerHz']==150000000
            assert all(raw['registers'][n]&4 for n in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
            assert timing['endToEnd']['samples']==1000 and detail['invalidPairs']==0
            for name, item in timing.items():
                if not isinstance(item,dict): continue
                for field, value in item.items(): assert value==values[f'g_nnTiming.{name}.{field}']
            for item in [v for v in timing.values() if isinstance(v,dict)]+detail['stage']:
                if not item['samples']: continue
                assert item['minTicks'] <= item['totalTicks']/item['samples'] <= item['maxTicks']
                assert abs(item['meanUs']-item['totalTicks']/item['samples']/150)<.001
            if report['backend']=='npu':
                assert run['output']==[.4375,.25,0,1]
                assert timing['npuCompletion']['samples']==1000
                assert bool(detail['instrumented'])==report['model_manifest']['detail_profile']
                if detail['instrumented']:
                    assert detail['lastCalls']==[1,4,1,0,4,4,4,1,1,1,1,1]
                    assert all(s['samples']==1000 for i,s in enumerate(detail['stage']) if i!=3)
            else: assert timing['fpuForward']['samples']==1000
            count += 1
    print(f'PASS: {count} real-board batches; raw snapshots, checks, 1000 samples, timing arithmetic, stage calls and PWM trips')

if __name__=='__main__': main()
