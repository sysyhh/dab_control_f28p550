"""Archive reproducible sources, check report links, hash every deliverable byte."""
import re
import shutil
from common_c import *


def files():
    for p in sorted(HERE.rglob('*')):
        rel=p.relative_to(HERE)
        if not p.is_file() or rel.parts[0] in ('work','host','__pycache__'):continue
        if p.name in ('SHA256SUMS.json','artifact_verification.json','debug_cli.py','capture_cli.py','capture_worker.js','audit_cli.py','audit_worker.js'):continue
        yield p


def main():
    protect();d=json.loads((HERE/'results/final_verification.json').read_text());assert d['ok']
    dest=HERE/'evidence/host';dest.mkdir(exist_ok=True)
    for p in (HERE/'host').glob('*.c'):shutil.copy2(p,dest/p.name)
    for v in d['variants']:
        p=HERE/'validated'/v
        (p/'README_zh.md').write_text(f'''# {v} Stage C 独立实验包

此包已通过570点四层原始输出、float32位模式及三轮普通固件计时。完整统计见 [验收](acceptance.json) 与 [总报告](../../REPORT_zh.md)。

仅适用于冻结B1网络；需要配套lib0/1/2.c、dab_tinie_c28.c、tvmgen_default.h、dab_npu_contract.h、fc_stage_a_input.h及应用dab_nn.stage_c.c。C2/C5还需匹配的tinie_mem_write_fast.asm；mod.a为这些文件同一编译条件的普通版本，detail-profile=0。

输入ABI：GS RAM中16单元对齐uint16_t[8] packed INT8，输出float32[4]；沿用Stage B的96单元workspace和原RAM分区。stage_b_delay.h只用于有限测试预热后的启动延迟，不计入正式样本。完整隔离工程可由run_stage_c.py prepare --variant {v}再生，保留于work/{v}/dab_control_f28p550/。

原始B1回退包位于../../../stage_b_20261031/validated/B1/；当前包没有覆盖正式工程或改变功率启动逻辑，四路OST必须保持锁定。此包是实验交付，不能只替换一个库文件到不同模型工程。
''',encoding='utf-8')
    # Create the manifest before link checking so report links can resolve it.
    hashes={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in files()}
    dump(HERE/'SHA256SUMS.json',dict(algorithm='SHA256',files=hashes))
    bad=[];links=0
    for p in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in target:continue
            links+=1
            if not (p.parent/target.split('#')[0]).exists():bad.append([p.name,target])
    assert not bad,bad
    for name,h in hashes.items():assert sha(HERE/name)==h,name
    assert set(hashes)=={str(p.relative_to(HERE)).replace('\\','/') for p in files()}
    for v in d['variants']:
        assert sha(HERE/f'validated/{v}/mod.a')==d['artifact_checks'][v]['library_sha256']
    total=sum((HERE/name).stat().st_size for name in hashes)
    dump(HERE/'results/artifact_verification.json',dict(ok=True,manifest_sha256=sha(HERE/'SHA256SUMS.json'),
      files=len(hashes),logical_bytes=total,report_local_links=links,all_manifest_hashes_rechecked=True,
      best=d['best'],formal_runs=d['formal_runs'],detail_runs=d['detail_runs'],
      A_B_and_production_protection='passed',unrelated_existing_changes_preserved=True))
    print(json.dumps(dict(ok=True,files=len(hashes),MiB=total/1048576,links=links,best=d['best'])))


if __name__=='__main__':main()
