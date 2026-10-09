"""Regression: old timestamps must not bypass a requested NN rebuild. No board."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]

def main():
    with tempfile.TemporaryDirectory(prefix='nn_rebuild_',dir=ROOT/'review_20261003') as temp:
        project=Path(temp)
        source=project/'dab_nn.c'
        source.write_text('/* fixture */\n')
        os.utime(source,(1,1))
        build=project/'CPU1_RAM'; build.mkdir()
        target=build/(project.name+'.out'); target.write_bytes(b'stale output')
        (build/'makefile').write_text(f'all: {target.name}\n{target.name}: ../dab_nn.c\n\texit 1\n')
        def invoke(force):
            command=[sys.executable,str(ROOT/'c2000_debug.py'),'--build-only','--project',str(project),
                     '--ccxml',str(ROOT/'dab_control_f28p550/targetConfigs/TMS320F28P550SJ9_LaunchPad.ccxml')]
            if force: command.append('--rebuild-nn')
            completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
            return completed.returncode,json.loads(completed.stdout)
        code,control=invoke(False)
        assert code==0 and control['build']=='PASS' and not control['connected']
        code,forced=invoke(True)
        assert code!=0 and forced['build']=='FAIL' and not forced['connected']
        assert target.read_bytes()==b'stale output'
        assert not (Path(forced['run_dir'])/'request.json').exists()
        print('PASS: reproduced old-timestamp skip; forced NN build fails explicitly and never loads stale output')

if __name__=='__main__': main()
