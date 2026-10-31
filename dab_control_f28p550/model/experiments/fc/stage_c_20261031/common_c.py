"""Stage C paths, byte-preserving protection, immutable B1 input."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
FC=HERE.parent
APP=FC.parents[2]
ROOT=APP.parent
A=FC/'stage_a_20261031';B=FC/'stage_b_20261031'
BASE=B/'validated/B1'
NNC=ROOT/'review_20261003/npu_integration_20261009/nnc211_env'
TVM=NNC/'Lib/site-packages/tvm'
TINIE=TVM/'3rdparty/tinie-api'
sys.path.insert(0,str(A));sys.path.insert(0,str(B))
import run_stage_b as stage_b
from audit_stage_b import arrays,mapping
from patch_stage_a import body,replace_once
BUILD=stage_b.BUILD


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8',newline='\n')


def run(cmd,cwd=None,timeout=240):
    p=subprocess.run([str(x) for x in cmd],cwd=cwd or ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if p.returncode:raise RuntimeError(f'{cmd[0]} returned {p.returncode}\n{p.stdout[-5000:]}\n{p.stderr[-5000:]}')
    return p.stdout


def protect():
    path=HERE/'provenance.json'
    if not path.exists():
        names=[]
        for folder in (A,B):names+=subprocess.check_output(['git','ls-files',str(folder.relative_to(ROOT))],cwd=ROOT,text=True).splitlines()
        files=[ROOT/p for p in names]+[APP/'dab_nn.c',APP/'.cproject',APP/'.settings/org.eclipse.core.resources.prefs']
        files += [p for name in ('npu','fc_int8','fc_int4') for p in (APP/'model/generated'/name).iterdir() if p.is_file()]
        dump(path,dict(head=run(['git','rev-parse','HEAD']).strip(),protected_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
             completion_criteria=['immutable B1 network, input helper, weights and instruction tables',
               'native NNC opt_for_space: actual MMR encoding and four-layer masked-register replay',
               'actual C28 decoder host C test and target pre/post-config snapshots',
               'baseline load assembly, fixed-source/target physical transfer audit',
               'only evidence-backed independent parameter loop candidates',
               '570 board points per candidate, all four raw layers and final bits',
               '3 independent ordinary and detailed builds/loads, 1000 samples, delays 0/17/43us',
               'OST locked, no power start, logs/images/ticks/SHA256 retained']))
    j=json.loads(path.read_text(encoding='utf-8'));bad=[p for p,h in j['protected_sha256'].items() if sha(ROOT/p)!=h]
    dump(HERE/'results/protected_files.json',dict(ok=not bad,changed=bad));assert not bad,bad
