# C2000 自动实板调试：最小原型

已于 2026-10-09 在本机真实 LAUNCHXL-F28P55X 上验证，无人工操作 CCS。

## 本机配置与技术路线

| 项目 | 实际检查结果 |
|---|---|
| CCS 安装 | `E:/Software_Download/ti/ccs2020/ccs`；目录名不是版本号，安装记录为 CCS 20.4.1，Debug Server 20.4.0.3973 |
| 编译器 | 现有工程使用 `ti-cgt-c2000_22.6.2.LTS` |
| 探针 | XDS110 Embed with CMSIS-DAP；序列号 `CL550001`；固件 `3.0.0.41` |
| 目标 | `.ccxml` 配置 TMS320F28P550SJ9，实机可连接 C28xx_CPU1 |
| 工程 | `dab_control_f28p550`，使用已有 `CPU1_RAM/makefile` |
| 调试配置 | `targetConfigs/TMS320F28P550SJ9_LaunchPad.ccxml`，XDS110、两线 cJTAG |
| 产物 | `CPU1_RAM/dab_control_f28p550.out` |

实际路线：`Codex → Python CLI → CCS 自带 Node / CCS Scripting → Debug Server → XDS110 → C28xx_CPU1`。
Python 入口只使用标准库；调用 CCS 自带的 Node 和 Scripting 包，不依赖电脑全局 Node，也不安装 Python 调试依赖。
本机虽有 Python Scripting 包，但需要额外的 `websockets`；当前短 JavaScript 文件直接使用 CCS 已有运行环境，减少安装步骤。

参考项目的具体取舍与来源见 [REFERENCE_REVIEW.md](REFERENCE_REVIEW.md)。保留目标配置、明确 CPU、超时、结构化结果；不引入 MCP、常驻服务、多核管理或 HIL。

## 使用

在工作区根目录运行：

```powershell
python .\c2000_debug.py --run-test
```

默认执行现有工程增量编译，连接、暂停、复位、加载 RAM 程序；运行 250 ms 后暂停读取，再运行 250 ms 后暂停读取；最后关闭本次 Debug Server。
程序加载默认运行到 `main`；不能在 RAM 加载后再复位。本机初始原型在加载后复位并 restart 时发生超时，改为加载前复位后已通过重复实板验证。
这条命令不会点击 CCS；验证时原有 CCS 窗口保持打开，脚本自行建立独立调试连接。

自定义读取对象与运行时间：

```powershell
python .\c2000_debug.py --run-test --run-ms 500 --samples 2 --expr "g_controlHeartbeat" --expr "g_sensing.vout_n_ave" --expr "g_protectFlags.all" --register ST1
python .\c2000_debug.py --build-only
```

`--expr` 可重复，使用与 CCS Expressions 相同的标量 C/GEL 表达式；结构体须指定成员，数组须指定下标。
指定 `--expr` 时替换默认变量列表；PC 和四路 PWM 的 TZFLG 始终读取。
表达式直接交给 TI 的求值接口，因此调用者应只传读取表达式，不传赋值、函数调用或其他改变板上状态的表达式。
第一阶段采用定时运行后暂停，不提供条件触发、多核或连续采集。

`--ccs` / 环境变量 `CCS_ROOT` 可覆盖 CCS 位置；`--ccxml` 和 `--build-dir` 可覆盖目标配置与已有构建目录。
这些参数服务于当前 F28P550 工程，PWM 地址与默认变量都是当前目标专用，不能直接套用于其他型号。
最初验证了 `CPU1_RAM`；NN 自动统计扩展还已实板验证 `CPU1_LAUNCHXL_FLASH` 与 `CPU1_LAUNCHXL_NPU_FLASH` 的 Flash 加载、运行及读取，结果见下节。

## 返回与验收

标准输出仅含 JSON；退出码 `0` 表示当前检查全部通过，`1` 表示失败，参数错误返回 `2`。
编译及调试原始输出单独存入 `tools/c2000_debug/runs/<时间>/build.log` 和 `debug.log`；同目录保存请求、板上结果及完整 `result.json`。
`out_sha256` 记录本次加载文件的 SHA-256；`g_debugBuildId=0x20261009` 是本轮新增并保留的只读诊断标记，不参与控制，也不是每次编译自动变化的版本号。
已验证该源码修改触发 `dab_main.c` 重编译和重新链接，并从真实板上读回该标记。

默认检查包含：两次读取间主循环与控制中断计数增加；调试标记正确；状态为待机 `1`；四路功率 PWM 的 `TZFLG.OST` 全部锁定。
`connected=true` 表示本次已成功连接，`state=halted` 表示退出 Debug Server 前最后确认的状态；`debugger_closed=true` 表示脚本已关闭其调试进程，不表示退出后仍保持连接。
`ok` 是闭环及所选检查结果，不是整机电气性能结论。

重新执行验收：

```powershell
python .\tools\c2000_debug\verify_hardware.py
```

验收会连续执行两次默认实板闭环，验证自定义浮点变量与 ST1 读取，验证不存在的变量返回失败且目标暂停，并验证编译失败时即使有旧 `.out` 也绝不连接开发板。
验收结果保存于 [verification.json](verification.json)，每项包含完整原始结果路径。

## 当前边界

- 固件默认 `DAB_AUTO_START=0`，本轮保持待机，没有发出功率启动或清故障请求；四路 PWM 关断寄存器已经读回验证。`DAB_BOARD_CONFIG_CONFIRMED` 当前实际值为 1，旁边“默认禁止输出”的旧注释与数值不一致，不能依赖这段注释判断允许启动。
- ADC 浮点值是真实固件运行结果，但换算仍沿用旧板系数，不能当成已标定的电压、电流。`vin` 还有固定标称输入假设。
- 编译直接复用已有 CCS 生成的 makefile，可处理当前源码、头文件与 SysConfig 依赖；修改 `.cproject` 的文件列表、编译选项或新增构建配置后，须先通过 CCS 的工程构建入口重新生成 makefile。官方命令行入口记于参考评估中，未在本原型中增加另一套构建系统。
- 如果另一个调试会话占用探针，连接会返回失败；不要强行结束用户的 CCS。遇到此类冲突需结束占用探针的 Debug 会话。
- 单个 TI 操作默认超时 20 秒，外层也限制运行时长；普通异常会尝试 halt 并关闭调试器。强制终止进程、USB 拔出或调试驱动无响应时，无法保证成功暂停，须以 JSON 的实际状态与错误为准。
- 简单 `.lock` 防止本 CLI 重叠运行；进程被外部强制结束可能留下该文件。确认没有本脚本正在运行后才删除它；本工具不管理或抢占其他调试器。

## NN 自动统计扩展

`benchmark_nn.py` 复用同一个 CLI 和 Debug Server，不添加表达式赋值或功率启动命令。当前固件 `DAB_NN_init()` 已设置自动请求有限次数基准测试，Vin=90 V、预热 10 次、正式 1000 次；工具要求结果满足这些条件，否则返回失败。

```powershell
python tools/c2000_debug/benchmark_nn.py --backend fpu --label fpu_flash --repeats 3
python tools/c2000_debug/benchmark_nn.py --backend npu --label p3_release --repeats 3
```

需要分段统计时，先按照应用文档用 `compile_dab_npu.py --optimization-level 4 --detail-profile` 生成库，再执行 NPU 命令，将 label 改为 `p4_profile`；指定级别 3 可重建此前版本。测试脚本自动 Build、加载、连续运行 1000 ms 后暂停，读取全部 `g_nnTiming`、`g_nnNpuDetail` 标量和输出；一次测量中途不暂停，三轮均重新加载程序。

每轮核对样本、预热、冻结、拒绝、超时、待机和四路 PWM 关断；NPU 还核对详细计时开关、各层调用次数及 Vin=90 V 的预期输出。原始 CLI 结果、加载文件 SHA-256、源文件校验值、模型清单和整理后的统计保存在 `benchmarks/<时间>_<label>/`，失败结果同样保留，但不能作为速度结果。

统计入口始终传入 `--rebuild-nn`，强制重新编译 `dab_nn.c` 并重新链接，避免复制恢复旧模型文件后因时间戳较旧而继续加载前一个模型版本。读取后仍检查详细计时开关与库清单一致，模式不符判为失败，不纳入成绩。

正式速度使用关闭详细计时的库。本文统计扩展没有修改控制算法，也没有解决 NPU 量化误差；三种版本的实板统计及分析见应用的 `docs/NPU_optimization_log_zh.html`，开发板实际输出是读取结果，非电脑模拟。

总验收见 [nn_benchmark_verification.json](nn_benchmark_verification.json)。离线复核使用 `python tools/c2000_debug/verify_benchmarks.py <summary.json> ...`，会核对存档的原始快照、整理结果、计数换算、样本数和 PWM 关断状态；不把电脑运行时间当作实板性能。

P4 展开装载循环的七轮成功实板测试见 [p4_benchmark_verification.json](p4_benchmark_verification.json)。构建恢复的回归检查可运行 `python tools/c2000_debug/test_rebuild_nn.py`，无需开发板。

## 原型文件

入口 `c2000_debug.py`、短 CCS Scripting 文件 `debug_worker.js`、实板验收脚本及说明文档；应用仅新增保留的 `g_debugBuildId` 诊断常量，没有改控制逻辑。
