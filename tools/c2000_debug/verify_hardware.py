"""Executable acceptance checks. Requires the connected F28P550/XDS110."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'c2000_debug.py'


def invoke(*args):
    process = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                             capture_output=True, text=True, encoding='utf-8', timeout=180)
    return process.returncode, json.loads(process.stdout)


def main():
    tests = []
    for index in range(2):
        code, result = invoke('--run-test')
        assert code == 0 and result['ok'], result
        assert result['loaded'] and result['state'] == 'halted' and result['debugger_closed'], result
        assert len(result['samples']) == 2 and len(result['checks']) == 5, result
        assert all(result['checks'].values()), result
        tests.append({'name': f'default_real_board_{index + 1}', 'pass': True,
                      'result': str(Path(result['run_dir']) / 'result.json')})
    code, result = invoke('--run-test', '--expr', 'g_controlHeartbeat',
                          '--expr', 'g_sensing.vout_n_ave', '--register', 'ST1')
    assert code == 0 and result['ok'] and 'ST1' in result['registers'], result
    assert isinstance(result['variables']['g_sensing.vout_n_ave'], float), result
    tests.append({'name': 'custom_expression_and_register', 'pass': True,
                  'result': str(Path(result['run_dir']) / 'result.json')})
    code, result = invoke('--run-test', '--samples', '1', '--expr', '__missing_debug_variable__')
    assert code != 0 and not result['ok'] and result['state'] == 'halted', result
    assert any(e.get('stage') == 'read' for e in result['errors']), result
    tests.append({'name': 'missing_expression_fails_and_halts', 'pass': True,
                  'result': str(Path(result['run_dir']) / 'result.json')})
    # A failed build must never connect, even if an old .out already exists.
    with tempfile.TemporaryDirectory(prefix='c2000_build_failure_') as temp:
        project = Path(temp)
        build = project / 'CPU1_RAM'
        build.mkdir()
        (build / 'makefile').write_text('all:\n\texit 1\n', encoding='utf-8')
        (build / (project.name + '.out')).write_bytes(b'stale output')
        code, result = invoke('--run-test', '--project', str(project), '--ccxml',
                              str(ROOT / 'dab_control_f28p550/targetConfigs/TMS320F28P550SJ9_LaunchPad.ccxml'))
        assert code != 0 and result['build'] == 'FAIL' and not result['connected'], result
        assert not (Path(result['run_dir']) / 'request.json').exists(), result
        tests.append({'name': 'build_failure_blocks_stale_output', 'pass': True,
                      'result': str(Path(result['run_dir']) / 'result.json')})
    report = {'ok': True, 'tests': tests}
    (Path(__file__).parent / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
