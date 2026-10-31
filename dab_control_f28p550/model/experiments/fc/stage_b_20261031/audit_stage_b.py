"""Read-only mapping/parameter audit and immutable Stage-A provenance."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
FC=HERE.parent
APP=FC.parents[2]
ROOT=APP.parent
STAGE_A=FC/'stage_a_20261031'
NNC=ROOT/'review_20261003/npu_integration_20261009/nnc211_env'
TINIE=NNC/'Lib/site-packages/tvm/3rdparty/tinie-api'
sys.path.insert(0,str(STAGE_A))
from patch_stage_a import body


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8',newline='\n')


def protect():
    path=HERE/'provenance.json'
    if not path.exists():
        tracked=subprocess.check_output(['git','ls-files',str(STAGE_A.relative_to(ROOT))],cwd=ROOT,text=True).splitlines()
        extra=[APP/'dab_nn.c',APP/'.cproject',APP/'.settings/org.eclipse.core.resources.prefs']
        extra += [p for d in ('npu','fc_int8','fc_int4') for p in (APP/'model/generated'/d).iterdir() if p.is_file()]
        paths=[ROOT/p for p in tracked]+extra
        dump(path,dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             protected_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
             criteria=['hardware FC, no software fallback, exactly 4 B1 tasks before board',
                       'frozen active tensors and quantization; explicit zero code proof',
                       'all float32 Vin in [90,140] reduced to all reachable quantized input codes',
                       'host integer decoded-kernel traces and actual CPU graph compare',
                       '501 Vin and 69 boundary board traces; new hidden channels all zero',
                       'three independent builds/loads at three trigger phases per admitted variant',
                       'ordinary versus detail timing segregated; raw logs and SHA256 preserved',
                       'standby, no power-start and all four OST locks checked every batch',
                       'no parameter-residency experiment without a proven rebase path']))
    data=json.loads(path.read_text(encoding='utf-8'))
    changed=[p for p,h in data['protected_sha256'].items() if sha(ROOT/p)!=h]
    dump(HERE/'results/protected_files.json',dict(ok=not changed,changed=changed))
    assert not changed,changed


def arrays(code,prefix):
    return {n:[int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',b)]
            for n,b in re.findall(r'static const uint32_t ('+prefix+r'\w*)\[\] = \{(.*?)\};',code,re.S)}


def mapping(path):
    code=(path/'lib2.c').read_text(encoding='utf-8')
    params=arrays(code,'FC_PARAMS');mmrs=arrays(code,'FC_MMR')
    layers=[]
    for i in range(4):
        b=body(code,f'tvmgen_default_ti_npu_fullyConnectedNHWC_{i}')
        p=re.findall(r'\b(FC_PARAMS\w*)\s*,',b)
        m=re.findall(r'\b(FC_MMR\w*)\s*,',b)
        ins=re.findall(r'\b(FC_\w+_INS)\s*,',b)
        count=int(re.search(r'tinie_num_sublayers = (\d+);',b)[1])
        assert count==len(p)==len(m)==len(ins)
        assert b.count('tinie_curr_layer += 1;')==1 and 'tinie_sublayer_IRQHandler();' in b
        layers.append(dict(layer=i,subtasks=count,parameters=p,mmrs=m,instructions=ins,
                           parameter_bytes=[len(params[x])*4 for x in p],
                           parameter_address_registers=[{str(j):mmrs[x][j] for j in (21,25,27)} for x in m]))
    assert not re.search(r'\bTINIE_fullyConnected\s*\(',code)
    return dict(layers=layers,hardware_tasks=sum(l['subtasks'] for l in layers),
                parameter_total_bytes=sum(len(v)*4 for v in params.values()),
                fc_instruction_tables=sorted(set(x for l in layers for x in l['instructions'])),
                lib2_sha256=sha(path/'lib2.c'))


def main():
    protect()
    a=mapping(STAGE_A/'validated/A4');b=mapping(HERE/'generated/B1_raw')
    assert a['hardware_tasks']==5 and b['hardware_tasks']==4
    assert all(x['subtasks']==1 for x in b['layers'])
    audit=json.loads((HERE/'generated/B1_raw/fc_audit.json').read_text(encoding='utf-8'))
    assert audit['hardware_fc_mapped'] and not audit['software_fc_library'] and not audit['cpu_generated_fc']
    assert audit['tinie_fullyConnected_soft_calls']==0 and not audit['conv_rewrite_detected']
    dump(HERE/'results/mapping_gate.json',dict(ok=True,board_allowed=True,A4=a,B1=b,
         first_layer_partition_reason='NNC config_fc_no_host_postproc chooses 4/2/1 output blocks; 29=7*4+1, 32=8*4. Both 32-channel FC parameter blocks fit the 2048-byte internal limit.',
         alignment_minimum_for_no_tail=4,smallest_extension_preserving_29_active_outputs=32))
    evidence=HERE/'evidence/nnc211';evidence.mkdir(parents=True,exist_ok=True)
    files=['hard/inc/tinie.h','hard/src/tinie_c28.c','hard/pyutils/common_utils.py',
           'hard/pyutils/common_mmr_defs.py','hard/pyutils/config_fc.py','hard/pyutils/gen_mmr_fc.py',
           'hard/pyutils/pack_weights_fc.py','hard/pyutils/pack_bias.py','hard/pyutils/pack_scale_shift.py']
    hashes={}
    for name in files:
        dst=evidence/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(TINIE/name,dst);hashes[name]=sha(dst)
    capacity=2048
    facts=dict(capacity_logical_bytes=capacity,capacity_source='NNC 2.1.1 common_utils.py TINIE_PARAMS_BUFSIZE=2048',
       cpu_word_address_base='0x54000 + 0x1800 = 0x55800',
       cpu_word_aperture_end='0x55fff; 512 uint32 writes at 4-word strides, every write spans two 16-bit units',
       logical_word_count_32bit=512,A4_total_parameter_bytes=a['parameter_total_bytes'],
       B1_total_parameter_bytes=b['parameter_total_bytes'],
       raw_sum_fits=dict(A4=a['parameter_total_bytes']<=capacity,B1=b['parameter_total_bytes']<=capacity),
       final_fc4_bias_prefetch_reserve_bytes=24,
       final_fc4_reserve_source='get_num_reserve_bytes(4,4)=max(0,(4-4//4)*8)=24',
       parameter_bytes_with_final_reserve=dict(A4=a['parameter_total_bytes']+24,B1=b['parameter_total_bytes']+24),
       B1_nominal_layout_including_final_reserve_fills_capacity_exactly=True,
       driver_always_reloads=True,driver_target_offset_is_fixed_zero=True,
       descriptor_has_resident_base_or_handle=False,
       generator_internal_address_fields={'weights':21,'bias':25,'scale_shift':27},
       generator_internal_address_units='64-bit chunks, inferred directly from w_num_64bits and b_num_64bits in gen_mmr_fc.py',
       c28_official_parameter_rebase_api_found=False,
       non_c28_NPU_setParamMem_is_not_a_C28_interface=True,
       public_TRM='https://www.ti.com/lit/pdf/spruj53#page=1056',
       public_TRM_limitation='Rev D chapter 8 occupies pages 1056-1057 and provides no NPU register fields, internal parameter address semantics, or relocation/multitask guarantees.',
       unproved=['FC microcode rebasing and any internal fixed-base/reset assumptions',
                 'whether the generated zero-base prefetch bounds remain valid for rebased simultaneous blocks',
                 'lifetime/invalidation guarantees for resident parameters across start/init'],
       hardware_feasibility='capacity permits it, generator address registers suggest a possible path; full hardware feasibility is not proved',
       current_sdk_and_nnc_support='no C28 residency/base-selection API or generated manager found; all blocks load at offset zero',
       experimental_implementation_admitted=False,
       decision='Do not execute B2/B3 or write speculative addresses. Obtain TI FC microcode relocation/access-span contract before attempting.',
       evidence_sha256=hashes)
    dump(HERE/'results/parameter_residency_audit.json',facts)
    print(json.dumps(dict(ok=True,B1_hardware_tasks=b['hardware_tasks'],A4_tasks=a['hardware_tasks'],
          A4_params=a['parameter_total_bytes'],B1_params=b['parameter_total_bytes'],B2_B3_admitted=False)))


if __name__=='__main__':main()
