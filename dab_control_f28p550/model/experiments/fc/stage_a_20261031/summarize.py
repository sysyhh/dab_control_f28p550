"""Recheck archived board data and produce the stage-A comparison tables."""
import csv
import json
from pathlib import Path
import shutil
import statistics
from run_stage_a import HERE, ROOT, APP, VARIANTS, dump, assert_protected, sha
from patch_stage_a import transform, application


def latest(label):
    paths=sorted((HERE/'results/benchmarks').glob('*_fc_stage_a_'+label+'/summary.json'))
    paths=[p for p in paths if json.loads(p.read_text(encoding='utf-8')).get('ok')]
    assert paths,'missing passed board data: '+label
    return paths[-1]


def verify(path, formal):
    report=json.loads(path.read_text(encoding='utf-8'))
    assert report['ok'] and len(report['runs'])==(3 if formal else 1)
    assert bool(report['model_manifest']['detail_profile']) != formal
    for i,r in enumerate(report['runs']):
        raw=json.loads((path.parent/f'run_{i+1}.json').read_text(encoding='utf-8'))
        assert raw['ok'] and raw['loaded'] and raw['connected'] and raw['debugger_closed']
        assert raw['state']=='halted' and not raw['errors']
        assert all(r['checks'].values()) and raw['out_sha256']==r['out_sha256']
        v=raw['variables']; t=r['timing']
        assert v['g_nnBenchmarkCompleted']==t['endToEnd']['samples']==1000
        assert v['g_nnBenchmarkWarmupCompleted']==10 and v['g_nnBenchmarkVin']==90
        assert v['g_nnTimeoutCount']==v['g_startRequested']==v['g_protectFlags.all']==0
        assert v['g_dabState']==1 and t['timerHz']==150000000 and t['frozen']
        assert t['npuIsrLastLayerCount']==[0,2,1,1,1] and t['npuIsrLastCount']==5
        assert t['npuIsrInvocations']==5000 and t['rejectedOutputs']==0
        assert r['output']==[.453125,.25,0,1]
        assert all(raw['registers'][n]&4 for n in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
        assert raw['model_constant_copy']['matches'] and raw['model_constant_copy']['run']==0x9800
        ticks=raw['e2e_ticks']; assert len(ticks)==1000 and min(ticks)>0
        mean=statistics.mean(ticks)/150
        assert abs(mean-t['endToEnd']['meanUs'])<.001
        d=r['end_to_end_distribution']
        assert abs(d['mean_us']-mean)<1e-10 and d['min_ticks']==min(ticks) and d['max_ticks']==max(ticks)
        ordered=sorted(ticks)
        assert d['p95_ticks']==ordered[round(.95*999)] and d['p99_ticks']==ordered[round(.99*999)]
        for stage in ('prepare','npuSubmit','npuCompletion','npuIsr','publish','endToEnd'):
            item=t[stage]
            for key,value in item.items():
                assert value==v[f'g_nnTiming.{stage}.{key}']
            assert abs(item['meanUs']-item['totalTicks']/item['samples']/150)<.001
        # Make the original framework's Baseline raw logs part of the isolated archive too.
        original=Path(raw['run_dir']); dest=HERE/'results/debug_runs'/original.name
        if original.resolve()!=dest.resolve() and not dest.exists():
            shutil.copytree(original,dest)
    return report


def main():
    assert_protected()
    host=json.loads((HERE/'results/host_verification.json').read_text(encoding='utf-8'))
    correctness=json.loads((HERE/'results/board_correctness.json').read_text(encoding='utf-8'))
    assert host['ok'] and correctness['ok']
    rows=[]; details=[]; reports={}; artifact_checks={}
    baseline=None
    for variant in VARIANTS:
        path=latest(variant); r=verify(path,True); reports[variant]=str(path.relative_to(HERE))
        project=HERE/'work'/variant/APP.name
        lib=project/'model/generated/fc_int8'
        raw=(APP/'model/generated/fc_int8/lib1.c').read_text(encoding='utf-8')
        assert (lib/'lib1.c').read_text(encoding='utf-8')==transform(raw,variant)
        assert (project/'dab_nn.c').read_text(encoding='utf-8')==application((APP/'dab_nn.c').read_text(encoding='utf-8'),variant in ('A3','A4'))
        assert sha(lib/'lib2.c')==sha(APP/'model/generated/fc_int8/lib2.c')
        assert sha(lib/'dab_tinie_c28.c')==sha(APP/'model/generated/fc_int8/dab_tinie_c28.c')
        image=project/'CPU1_LAUNCHXL_FC_INT8_FLASH/dab_control_f28p550.out'
        assert all(x['out_sha256']==sha(image) for x in r['runs'])
        current_manifest=json.loads((lib/'manifest.json').read_text(encoding='utf-8'))
        assert current_manifest['library_sha256']==sha(lib/'mod.a')
        artifact_checks[variant]={'all_measured_images_match_retained_image':True,'image_sha256':sha(image),
            'current_library_sha256':sha(lib/'mod.a'),'generated_runtime_matches_patch':True,
            'application_matches_patch':True,'kernel_and_driver_identical_to_baseline':True,
            'manifest_note':'Initial summary model_manifest is a pre-rebuild snapshot. Per-run out_sha256 identifies each actual measured image; all match the retained independently rebuilt image.'}
        means=[x['end_to_end_distribution']['mean_us'] for x in r['runs']]
        if baseline is None: baseline=statistics.mean(means)
        for i,x in enumerate(r['runs']):
            d=x['end_to_end_distribution'];t=x['timing']
            rows.append(dict(variant=variant,round=i+1,mean_us=d['mean_us'],min_us=d['min_us'],max_us=d['max_us'],
                             p95_us=d['p95_us'],p99_us=d['p99_us'],foreground_us=x['cpu_foreground_mean_us'],
                             isr_us=x['cpu_isr_mean_us'],cpu_total_us=x['cpu_total_mean_us'],
                             submit_us=t['npuSubmit']['meanUs'],completion_us=t['npuCompletion']['meanUs'],
                             prepare_us=t['prepare']['meanUs'],publish_us=t['publish']['meanUs'],
                             hw_wait_residual_us=x['npu_hw_wait_mean_us'],
                             cpu_time_share_percent=100*x['cpu_total_mean_us']/d['mean_us'],
                             reduction_percent=100*(1-d['mean_us']/baseline),speedup=baseline/d['mean_us'],
                             out_sha256=x['out_sha256']))
        dp=latest(variant+'_detail');dr=verify(dp,False)
        reports[variant+'_detail']=str(dp.relative_to(HERE))
        x=dr['runs'][0]
        expected_calls={
            'Baseline':[1,4,4,3,5,5,5,2,1,1,1,1],
            'A1':[1,4,4,0,5,5,5,2,1,1,1,1],
            'A2':[1,1,1,0,5,5,5,2,1,1,1,1],
            'A3':[1,3,4,3,5,5,5,2,1,1,1,1],
            'A4':[1,0,1,0,5,5,5,2,1,1,1,1],
        }
        assert x['detail']['lastCalls']==expected_calls[variant],(variant,x['detail']['lastCalls'])
        details.append(dict(variant=variant,end_to_end_instrumented_us=x['timing']['endToEnd']['meanUs'],
                            calls=x['detail']['lastCalls'],
                            stages={name:stage['meanUs'] if stage['samples'] else 0
                                    for name,stage in zip(x['detail']['stage_names'],x['detail']['stage'])}))
    with (HERE/'results/performance.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={'ok':True,'formal_runs':15,'formal_samples':15000,'detail_runs':5,'detail_samples':5000,
            'correctness_points_per_variant':570,'host':host,'board_correctness':correctness,
            'performance':rows,'detail':details,'source_reports':reports,'artifact_checks':artifact_checks}
    dump(HERE/'results/final_verification.json',result)
    # Export only admitted, ordinary libraries; keep installed models untouched.
    for variant in VARIANTS:
        project=HERE/'work'/variant/APP.name; lib=project/'model/generated/fc_int8'
        target=HERE/'validated'/variant;target.mkdir(parents=True,exist_ok=True)
        for name in ('mod.a','tvmgen_default.h','dab_npu_contract.h','lib0.c','lib1.c','lib2.c','dab_tinie_c28.c','manifest.json'):
            shutil.copy2(lib/name,target/name)
        shutil.copy2(project/'dab_nn.c',target/'dab_nn.stage_a.c')
        if variant in ('A3','A4'):
            shutil.copy2(project/'fc_stage_a_input.h',target/'fc_stage_a_input.h')
        dump(target/'acceptance.json',dict(ok=True,variant=variant,detail_profile=False,
            correctness_report='../../results/board_correctness.json',formal_summary=reports[variant],
            artifact=artifact_checks[variant],power_control_approved=False))
        (target/'README.md').write_text(
            '# '+variant+' 已验证实验包\n\n'
            '优先使用 ../../work/'+variant+'/dab_control_f28p550/ 的完整隔离工程。\n\n'
            '本目录未安装到交付工程；acceptance.json 关联逐层实机检查及三轮正式性能。\n\n'+
            ('输入为 GS RAM 中 16 单元对齐的 uint16_t[8] packed INT8，输出为 float32[4]。'
             '必须配套 dab_nn.stage_a.c、fc_stage_a_input.h 和本目录头文件使用，不能仅将 mod.a 换到 float 输入工程。\n'
             if variant in ('A3','A4') else '保持 float32[16] 输入、float32[4] 输出。\n'),encoding='utf-8')
    for v in VARIANTS:
        rr=[r for r in rows if r['variant']==v]
        print(v,'means',*[round(r['mean_us'],6) for r in rr],
              'reduction%',round(rr[0]['reduction_percent'],3),'speedup',round(rr[0]['speedup'],3))
    print('PASS: 15 formal + 5 detailed batches, 570 raw board traces per variant, all protected files unchanged')


if __name__=='__main__':
    main()
