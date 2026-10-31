$ErrorActionPreference = 'Stop'
$stageBRoot = $PSScriptRoot
$stageBWorkspace = (Resolve-Path (Join-Path $stageBRoot '../../../../../')).Path
$stageBNncPython = Join-Path $stageBWorkspace 'review_20261003/npu_integration_20261009/nnc211_env/python.exe'
$stageBCompiler = Join-Path $stageBRoot '../compile_fc_npu.py'
$stageBOnnx = Join-Path $stageBRoot 'onnx/B1_16_32_16_16_4.onnx'
function Invoke-StageBStep {
    param([string]$Python, [string[]]$StepArguments)
    & $Python @StepArguments
    if ($LASTEXITCODE -ne 0) { throw "Stage B step failed: $($StepArguments[0])" }
}
Push-Location $stageBWorkspace
try {
    Invoke-StageBStep $stageBNncPython @((Join-Path $stageBRoot 'build_candidate.py'))
    Invoke-StageBStep $stageBNncPython @($stageBCompiler, '--onnx', $stageBOnnx, '--out', (Join-Path $stageBRoot 'generated/B1_raw'), '--force-hw')
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'audit_stage_b.py'))
    Invoke-StageBStep $stageBNncPython @($stageBCompiler, '--package-firmware', '--src', (Join-Path $stageBRoot 'generated/B1_raw'), '--out', (Join-Path $stageBRoot 'generated/B1_packaged'), '--onnx', $stageBOnnx, '--optimization-level', '5', '--reuse-instructions')
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'run_stage_b.py'), 'prepare')
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'verify_host_b.py'))
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'verify_cpu_graph.py'))
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'validate_board_b.py'))
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'run_stage_b.py'), 'board')
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'run_stage_b.py'), 'detail')
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'verify_results_b.py'))
    Invoke-StageBStep 'python' @((Join-Path $stageBRoot 'write_report_b.py'))
} finally {
    Pop-Location
}
