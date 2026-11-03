# C2000 自动实板调试与耗时基准工具

用于在真实 LAUNCHXL-F28P55X 开发板上执行一键编译、加载、运行、暂停采样及片上神经网络（FPU / NPU）耗时基准测试，无需人工点击 CCS 界面。

## 环境配置与技术路线

| 项目 | 默认配置 / 说明 |
|---|---|
| CCS 安装 | 默认 `C:/ti/ccs2020/ccs`（可通过环境变量 `CCS_ROOT` 或 `--ccs` 参数指定） |
| 编译器 | `ti-cgt-c2000_22.6.2.LTS` |
| 探针 | 板载 XDS110（两线 cJTAG） |
| 目标器件 | `TMS320F28P550SJ9` (`C28xx_CPU1`) |
| 工程路径 | `dab_control_f28p550` |
| 调试配置 | `targetConfigs/TMS320F28P550SJ9_LaunchPad.ccxml` |

技术路线：`Python CLI -> CCS 自带 Node / CCS Scripting -> Debug Server -> XDS110 -> C28xx_CPU1`。
Python 入口仅使用标准库，直接调用 CCS 自带的 Node 和 Scripting 组件，无需安装额外的 Python 第三方调试依赖。

## 基本用法

在仓库根目录运行：

```powershell
python .\c2000_debug.py --run-test
```

默认执行现有工程增量编译，连接、暂停、复位、加载程序；运行 250 ms 后暂停读取快照，再运行 250 ms 后暂停读取第二次快照；最后关闭本次 Debug Server。

自定义读取表达式与运行时间：

```powershell
python .\c2000_debug.py --run-test --run-ms 500 --samples 2 --expr "g_controlHeartbeat" --expr "g_sensing.vout_n_ave" --expr "g_protectFlags.all" --register ST1
python .\c2000_debug.py --build-only
python .\c2000_debug.py --attach-only
```

- `--expr` 可重复指定，使用与 CCS Expressions 相同的标量 C/GEL 表达式（结构体须指定成员，数组须指定下标）。
- `--attach-only` 仅挂接并暂停当前运行中的目标以读取状态，不执行编译、复位、加载或重新运行。
- `--ccs` / 环境变量 `CCS_ROOT` 可覆盖 CCS 路径；`--ccxml` 和 `--build-dir` 可覆盖目标配置与构建目录（如 `CPU1_RAM`、`CPU1_LAUNCHXL_FLASH`、`CPU1_LAUNCHXL_NPU_FLASH`）。

## 返回结构与硬件闭环自检

标准输出为结构化 JSON；退出码 `0` 表示检查全部通过，`1` 表示失败。
每次运行的编译日志、调试日志与快照保存在 `tools/c2000_debug/runs/<timestamp>/` 下（该目录已加入 `.gitignore`）。

默认检查项包括：
- 两次采样之间主循环与控制中断心跳计数递增；
- 诊断构建标记 `g_debugBuildId` 匹配；
- 状态机处于待机状态 `DAB_STATE_STANDBY (1)`；
- 四路功率 PWM 的 `TZFLG.OST` 硬件单次关断锁存全部生效。

运行实板硬件闭环验收：

```powershell
python .\tools\c2000_debug\verify_hardware.py
```

无需开发板的离线回归自检：

```powershell
node .\tools\c2000_debug\test_attach_only.js
python .\tools\c2000_debug\test_rebuild_nn.py
```

## 片上神经网络（FPU / FC-NPU）耗时压测

`benchmark_nn.py` 复用 `c2000_debug.py` 的 `--nn-auto-benchmark` 独立测试构建选项（正式固件默认 `DAB_NN_AUTO_BENCHMARK=0`），在待机安全关断状态下自动执行预热 10 次 + 正式 1000 次前向推理，并采集 `g_nnTiming`、`g_nnNpuDetail` 及 `g_nnBenchmarkE2eTicks` 分布统计：

```powershell
python .\tools\c2000_debug\benchmark_nn.py --backend fpu --label fpu_flash --repeats 3
python .\tools\c2000_debug\benchmark_nn.py --backend fc_int8 --label fc_int8_flash --repeats 3
python .\tools\c2000_debug\benchmark_nn.py --backend fc_int4 --label fc_int4_flash --repeats 3
```

测试脚本每次均传入 `--rebuild-nn` 强制重编译并重链接 `dab_nn.c`，确保替换模型权重或 `mod.a` 后不会因时间戳缓存跳过链接。测试报告输出至 `tools/c2000_debug/benchmarks/<timestamp>_<label>/summary.json`。
