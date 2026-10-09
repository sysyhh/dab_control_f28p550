import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
bench=root/'tools/c2000_debug/benchmarks'
names=['20261010_000058_p5_release','20261010_000252_p5_profile','20261010_014928_p5_final_verified']
reports=[json.loads((bench/n/'summary.json').read_text(encoding='utf-8')) for n in names]
assert all(r['ok'] and all(all(run['checks'].values()) for run in r['runs']) for r in reports)
release=reports[0]['runs'][0]['timing']
detail=reports[1]['runs'][0]['detail']
old=json.loads((root/'tools/c2000_debug/p4_benchmark_verification.json').read_text())
old_end=old['reports'][0]['end_to_end_mean_us'][0]
data={'ok':True,'date':'2026-10-10','optimization_level':5,
      'successful_real_board_batches':sum(len(r['runs']) for r in reports),
      'formal_samples_per_batch':1000,'warmup_per_batch':10,'vin':90,
      'reports':[{'label':r['label'],'summary':(bench/n/'summary.json').relative_to(root).as_posix(),
                  'batches':len(r['runs']),'end_to_end_mean_us':[x['timing']['endToEnd']['meanUs'] for x in r['runs']],
                  'all_checks_passed':True} for n,r in zip(names,reports)],
      'ordinary_timing_mean_us':{k:v['meanUs'] for k,v in release.items() if isinstance(v,dict)},
      'p4_to_p5_end_to_end_reduction_percent':(1-release['endToEnd']['meanUs']/old_end)*100,
      'p5_over_fpu_end_to_end_ratio':release['endToEnd']['meanUs']/28.715497970581055,
      'profile_stage_mean_us':{name:stage['meanUs'] for name,stage in zip(detail['stage_names'],detail['stage'])},
      'ram_constants':{'section':'.dab_npu_const','run_address':'0x9800','c28_words':1592,'capacity_words':2048,
                       'all_successful_batches_compared_with_flash':True},
      'known_vin90_output':[.4375,.25,0,1],
      'layer_constant_comparison':{'reference_commit':'f5d5f41','all_four_layer_parameters_configs_and_instruction_selections_match':True,
                                   'script':'review_20261003/npu_integration_20261009/compare_p5_constants.py'},
      'final_library_sha256':reports[-1]['model_manifest']['library_sha256'],
      'final_detail_profile':False,'power_control_approved':False,
      'scope':'Vin=90 only; no standalone power-cycle test or full-range hardware precision acceptance',
      'excluded_attempt':'20261009_235723_p5_release: linker-symbol expression failed after benchmark; not accepted'}
assert data['successful_real_board_batches']==7
assert reports[-1]['model_manifest']['detail_profile'] is False
(root/'tools/c2000_debug/p5_benchmark_verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(data,ensure_ascii=False,indent=2))
