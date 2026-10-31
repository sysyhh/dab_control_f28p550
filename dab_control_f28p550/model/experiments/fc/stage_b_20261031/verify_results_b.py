"""Replay raw board records, phase variation, retained images and source proofs."""
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import struct
from audit_stage_b import HERE,APP,STAGE_A,sha,dump,protect,mapping
from run_stage_b import DELAYS,BUILD,phase_application,adapt_stage_a


def latest(label):
    paths=sorted((HERE/'results/benchmarks').glob('*_fc_stage_b_'+label+'/summary.json'))
    passed=[p for p in paths if json.loads(p.read_text(encoding='utf-8')).get('ok')]
    assert passed,'missing successful benchmark: '+label
    return passed[-1]


def stats(ticks):
    ordered=sorted(ticks);n=len(ticks)
    return dict(samples=n,mean_us=statistics.mean(ticks)/150,min_us=ordered[0]/150,max_us=ordered[-1]/150,
                p95_us=ordered[round(.95*(n-1))]/150,p99_us=ordered[round(.99*(n-1))]/150)


def verify(path,variant,detail):
    r=json.loads(path.read_text(encoding='utf-8'));assert r['ok'] and len(r['runs'])==3
    assert r['model_manifest']['detail_profile']==detail
    tasks=5 if variant=='A4' else 4;rows=[];all_ticks=[];hashes=[];pooled_stage=[]
    for i,x in enumerate(r['runs']):
        raw=json.loads((path.parent/f'run_{i+1}.json').read_text(encoding='utf-8'));v=raw['variables'];t=x['timing']
        assert raw['ok'] and raw['connected'] and raw['loaded'] and raw['state']=='halted' and raw['debugger_closed']
        assert not raw['errors'] and all(x['checks'].values())
        assert v['g_nnBenchmarkState']==2 and v['g_nnBenchmarkCompleted']==1000 and v['g_nnBenchmarkWarmupCompleted']==10
        assert v['g_nnBenchmarkVin']==90 and t['timerHz']==150000000
        assert v['g_nnTimeoutCount']==v['g_startRequested']==v['g_protectFlags.all']==0 and v['g_dabState']==1
        assert t['npuIsrLastCount']==tasks and t['npuIsrInvocations']==1000*tasks
        assert t['npuIsrLastLayerCount']==([0,2,1,1,1] if variant=='A4' else [0,1,1,1,1])
        assert t['rejectedOutputs']==0 and t['frozen'] and raw['model_constant_copy']['matches']
        assert all(raw['registers'][n]&4 for n in ('EPWM7_TZFLG','EPWM4_TZFLG','EPWM5_TZFLG','EPWM10_TZFLG'))
        assert x['output']==[.453125,.25,0,1]
        assert bool(x['detail']['instrumented'])==detail and x['detail']['invalidPairs']==0
        assert v['g_fcStageBDelayTicks']==DELAYS[i] and v['g_fcStageBActualDelayTicks']>=DELAYS[i]
        assert raw['out_sha256']==x['out_sha256']==sha(path.parent/f'round_{i+1}.out')
        source=json.loads((path.parent/f'round_{i+1}_source_manifest.json').read_text(encoding='utf-8'))
        assert f'FC_STAGE_B_DELAY_TICKS {DELAYS[i]}UL' in source['delay_header']
        assert source['library']==x['round_manifest']
        ticks=raw['e2e_ticks'];assert len(ticks)==1000 and min(ticks)>0
        digest=hashlib.sha256(struct.pack('<1000I',*ticks)).hexdigest();hashes.append(digest);all_ticks.extend(ticks)
        st=stats(ticks);assert abs(st['mean_us']-t['endToEnd']['meanUs'])<.001
        for f in ('min_us','max_us','p95_us','p99_us'):
            assert abs(st[f]-x['end_to_end_distribution'][f])<1e-10
        for field in ('prepare','npuSubmit','npuCompletion','npuIsr','publish','endToEnd'):
            item=t[field];assert item['samples']==1000
            assert item['minTicks']<=item['totalTicks']/1000<=item['maxTicks']
            assert abs(item['meanUs']-item['totalTicks']/150000)<.001
            assert all(value==v[f'g_nnTiming.{field}.{key}'] for key,value in item.items())
        row=dict(variant=variant,round=i+1,detail_profile=detail,delay_requested_us=DELAYS[i]/150,
             delay_actual_us=v['g_fcStageBActualDelayTicks']/150,first_formal_timer_tick=v['g_fcStageBFirstFormalTick'],
             **st,cpu_foreground_us=x['cpu_foreground_mean_us'],npu_isr_us=x['cpu_isr_mean_us'],
             cpu_total_us=x['cpu_total_mean_us'],prepare_us=t['prepare']['meanUs'],submit_us=t['npuSubmit']['meanUs'],
             completion_us=t['npuCompletion']['meanUs'],publish_us=t['publish']['meanUs'],
             npu_interrupts_per_inference=tasks,out_sha256=raw['out_sha256'],tick_sequence_sha256=digest)
        rows.append(row)
        if detail:
            expected=[1,0,1,0,tasks,tasks,tasks,2 if variant=='A4' else 1,1,1,1,1]
            assert x['detail']['lastCalls']==expected
            pooled_stage.append({name:item['meanUs'] if item['samples'] else 0
                                for name,item in zip(x['detail']['stage_names'],x['detail']['stage'])})
    assert len(set(hashes))==3,'phase changes produced duplicate timing sequences'
    assert len({x['out_sha256'] for x in r['runs']})==3,'delay configurations were not independently compiled'
    stages={k:statistics.mean(p[k] for p in pooled_stage) for k in pooled_stage[0]} if detail else {}
    return dict(rows=rows,pooled=stats(all_ticks),stage_means_us=stages,source_report=str(path.relative_to(HERE)),
                three_distinct_tick_sequences=True,phase_tick_hashes=hashes)


def export(variant,data):
    project=HERE/'work'/variant/APP.name;lib=project/'model/generated/fc_int8';target=HERE/'validated'/variant
    target.mkdir(parents=True,exist_ok=True)
    for name in ('lib0.c','lib1.c','lib2.c','dab_tinie_c28.c','tvmgen_default.h','dab_npu_contract.h','manifest.json','mod.a'):
        shutil.copy2(lib/name,target/name)
    for name in ('fc_stage_a_input.h','stage_b_delay.h'):shutil.copy2(project/name,target/name)
    shutil.copy2(project/'dab_nn.c',target/'dab_nn.stage_b.c')
    dump(target/'acceptance.json',dict(ok=True,stage_b_variant=variant,ordinary_library=True,
         library_sha256=sha(target/'mod.a'),correctness='../../results/board_correctness.json',
         formal_statistics=data['formal'][variant],parameter_residency=False,power_control_approved=False))
    (target/'README.md').write_text('# '+variant+' Stage B 实验包\n\n'
        '本包未覆盖正式工程；优先使用 ../../work/'+variant+'/dab_control_f28p550/ 的完整隔离工程。\n\n'
        '输入 ABI 为 GS RAM 中 16 单元对齐的 uint16_t[8] packed INT8，输出 float32[4]；'
        '必须配套应用源码、fc_stage_a_input.h、stage_b_delay.h 及生成头文件，不能只替换 mod.a。\n\n'
        'stage_b_delay.h 只控制有限测试预热后的启动延迟，计时样本不包含这段等待；功率输出保持关闭。\n',encoding='utf-8')


def main():
    protect()
    for name in ('mapping_gate','host_verification','cpu_graph_host','board_correctness'):
        assert json.loads((HERE/f'results/{name}.json').read_text(encoding='utf-8'))['ok']
    a,b=[json.loads((HERE/f'results/capture/{v}.json').read_text(encoding='utf-8'))['points'] for v in ('A4','B1')]
    assert a==b and len(a)==570
    formal={};detail={};artifact={}
    for v in ('A4','B1'):
        formal[v]=verify(latest(v),v,False);detail[v]=verify(latest(v+'_detail'),v,True)
        project=HERE/'work'/v/APP.name;lib=project/'model/generated/fc_int8'
        assert sha(lib/'dab_tinie_c28.c')==sha(STAGE_A/'validated/A4/dab_tinie_c28.c')
        assert sha(project/'fc_stage_a_input.h')==sha(STAGE_A/'validated/A4/fc_stage_a_input.h')
        assert (project/'dab_nn.c').read_text(encoding='utf-8')==phase_application((STAGE_A/'validated/A4/dab_nn.stage_a.c').read_text(encoding='utf-8'))
        source=STAGE_A/'validated/A4' if v=='A4' else HERE/'generated/B1_packaged'
        assert sha(lib/'lib2.c')==sha(source/'lib2.c')
        expected=(source/'lib1.c').read_text(encoding='utf-8')
        if v=='B1':expected=adapt_stage_a(expected)
        assert (lib/'lib1.c').read_text(encoding='utf-8')==expected
        assert mapping(lib)['hardware_tasks']==(5 if v=='A4' else 4)
        assert 'TINIE_NPU_EXTRA_BUF_PADDING + 64' in (lib/'lib0.c').read_text(encoding='utf-8')
        image=project/BUILD/'dab_control_f28p550.out'
        assert sha(image)==formal[v]['rows'][-1]['out_sha256']
        m=json.loads((lib/'manifest.json').read_text(encoding='utf-8'));assert m['library_sha256']==sha(lib/'mod.a')
        # Exact same GS workspace and integer input addresses in the two ordinary images.
        maptext=(project/BUILD/'dab_control_f28p550.map').read_text(encoding='utf-8',errors='replace')
        assert re.search(r'0000e000\s+00000060\s+mod.a\s*:\s*lib0.obj',maptext,re.I)
        assert re.search(r'0000e060\s+00000008\s+dab_nn.obj\s*\(ramgs1\)',maptext,re.I)
        artifact[v]=dict(driver_equal_to_A4=True,input_quantizer_equal_to_A4=True,
            active_kernel_parameters_verified=True,instruction_tables_unmodified=True,
            workspace_word_address='0xe000',workspace_storage_units=96,input_word_address='0xe060',input_storage_units=8,
            library_sha256=sha(lib/'mod.a'),last_ordinary_image_sha256=sha(image))
    reduction=100*(1-formal['B1']['pooled']['mean_us']/formal['A4']['pooled']['mean_us'])
    result=dict(ok=True,formal_runs=6,formal_samples=6000,detail_runs=6,detail_samples=6000,
         correctness_points_per_variant=570,formal=formal,detail=detail,artifact_checks=artifact,
         mean_reduction_percent=reduction,speedup=formal['A4']['pooled']['mean_us']/formal['B1']['pooled']['mean_us'],
         experiments={'A4':'admitted baseline','B1':'correctness and performance admitted',
                      'B2':'not run: residency rebase contract not proved','B3':'not run: residency rebase contract not proved'},
         stage_A_untouched=True,installed_library_untouched=True,power_output_enabled=False)
    for label,values in [('formal',formal),('detail',detail)]:
        rows=[row for item in values.values() for row in item['rows']]
        with (HERE/f'results/{label}_performance.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    dump(HERE/'results/final_verification.json',result)
    for v in ('A4','B1'):export(v,result)
    protect()
    print(json.dumps(dict(ok=True,A4=formal['A4']['pooled'],B1=formal['B1']['pooled'],reduction_percent=reduction,
                         phase_variation_verified=True,ordinary_and_detail_batches=12),ensure_ascii=False))


if __name__=='__main__':main()
