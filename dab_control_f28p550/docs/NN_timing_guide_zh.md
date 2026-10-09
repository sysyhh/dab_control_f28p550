# NN 前向计算耗时统计与 FPU/NPU 对比

## 1. 当前可以做什么

已支持 FPU 和真实 DAB NPU 的板上计时及待机有限次数测试。NPU 使用新配置 `CPU1_LAUNCHXL_NPU_FLASH`，真实模型库与输入适配已接入；实际硬件耗时与加速倍数仍待开发板测量，操作和六组期望输出见 [NPU 接入说明](NPU_integration_guide_zh.md)。

计时使用已有的 Timer2，不再新增定时器，也不在每次推理前重置 Timer2，避免破坏 PWM、采样、保护和遥测的公共时间基准。Timer2 以 SYSCLK 向下计数，当前 150 MHz：`elapsed = (uint32_t)(begin - end)`，`时间 μs = elapsed / 150`。无符号差值允许测量跨一次计数回绕；测量中不要暂停或单步，Timer2 在调试暂停时仍继续运行。

普通模式仍按 Vin 变化达到约 0.1 V 才重新计算，命中缓存不算一次推理。当前 Vin 固定 90 V，普通启动通常只有一组统计，因此需要下面的重复测试才能获得多个样本。

## 2. 第一次 FPU 测量

1. 保持功率级不投入运行。建议为本次测试将 `dab_board_config.h` 中 `DAB_AUTO_START` 设为 `0`，使用 `CPU1_LAUNCHXL_FLASH`，重新 Build、加载并从完整初始化运行。代码没有自动更改你当前的自动启动设置。
2. 加入 [CCS 观察变量列表](NN_timing_CCS_watch.txt) 中的变量，确认 `g_dabState=1`（待机），没有故障，PWM 未启用。若此前已运行，应先正常停止；已有 FAULT 则须先满足恢复条件并按原流程清故障，不能直接改状态变量。
3. 设置下面四项，最后才设置请求变量：

```c
g_nnBenchmarkIterations = 1000;  // 正式统计样本数，允许 1～10000。
g_nnBenchmarkWarmup = 10;        // 预热次数，允许 0～1000，不计入正式统计。
g_nnBenchmarkVin = 90.0f;        // 测试输入电压，内部仍按原三项输入进行归一化。
g_nnBenchmarkRequested = true;  // 最后提交，后台消费后自动清零。
```

4. 连续运行，完成后暂停读取。预期 `g_nnBenchmarkState=2`、`g_nnBenchmarkCompleted=1000`、`g_nnBenchmarkWarmupCompleted=10`，且 `g_nnTiming.fpuForward.samples=1000`、`g_nnTiming.frozen=true`。
5. 保存整个 `g_nnTiming`、测试输入、预热次数、编译设置和模型版本，再进行下一种方法的测量。测试结束后统计冻结，正常推理仍可继续，不会因普通输入变化覆盖这组结果。

每次主循环最多执行一次 FPU 前向；NPU 尚在计算时只查询完成，不重复提交或修改其缓冲区。测试期间控制启动请求会被拒绝，`g_startRejectReason=6`；一旦处理过重复测试请求，本次运行剩余的自动启动会取消，结束后仍需新的人工启动请求。

如果请求和取消同时提交，取消优先阻止新一轮计算。重复请求发生在正在测试时只拒绝该请求，不会中断现有测试。

## 3. 看哪些结果

`g_nnTiming` 中每个统计项都有 `samples`、`lastTicks`、`minTicks`、`maxTicks`、`totalTicks` 和 `meanUs`。总计数使用 64 位，平均值在计时区间外计算；没有样本时字段为零，零不表示该步骤不耗时。

| 统计项 | 测量范围 | 用法与限制 |
|---|---|---|
| `prepare` | 准备所选模型输入（FPU 三项、NPU 16 项） | 不包含 ADC 采样和滤波；NPU 运行库内部量化属于运行时间 |
| `fpuForward` | 调用 RAM 中 FPU 前向函数前后 | 当前最直接的 FPU 前向耗时，包含函数调用及期间中断时间 |
| `npuSubmit` | `tvmgen_default_run()` 调用前后 | 包含输入量化、打包和首层启动，不能作为 NPU 完成时间 |
| `npuObserved` | 提交开始到后台发现完成标志 | 包括运行库、NPU 执行、中断和后台查询延迟 |
| `npuCompletion` | 提交开始到可选完成通知钩子 | DAB16 库已接入最终输出时间戳；含提交、层间 CPU 处理和中断响应，不是裸 NPU 周期 |
| `publish` | 输出有效性检查和缓存发布 | NPU 在发现完成后开始计量；手工反量化若接入，应放在结果处理区间 |
| `endToEnd` | 输入准备开始到有效结果发布 | 两种方法优先用这一项比较应用实际获得结果的时间 |

示例换算：若 `fpuForward.minTicks=1500`，当前时钟下最短时间是 10 μs；这只是换算示例，不是本板实测结果。平均时间直接读取 `meanUs`，最长时间为 `maxTicks/150`。

`timerHz` 保存换算时钟，`timerReadOverheadTicks` 是连续两次读取 Timer2 的间隔，原始数据没有自动扣除该开销。若测量期间刚好被中断，读取开销也可能包含中断时间；不要把一次较大的校准值从每个样本中机械减去。

`g_nnTimingSequence` 为奇数表示后台正在更新多字段，为偶数表示一次更新已结束。CCS 连续刷新可能混读不同样本，建议测试完成后暂停并整体刷新读取。

## 4. 测试状态与控制

| `g_nnBenchmarkState` | 含义 |
|---:|---|
| 0 | 尚未测试 |
| 1 | 正在测试，包含预热或等待 NPU 完成 |
| 2 | 正式样本收集完成，结果冻结 |
| 3 | 请求被拒绝，查看 `g_nnBenchmarkRejectReason` |
| 4 | NN 错误或超时，本组测试失败 |
| 5 | 已取消，已完成的部分结果冻结，不能当作完整测试 |

拒绝原因：1 正在测试；2 未满足待机/输出关闭条件；3 NN 正忙或已故障；4 次数或 Vin 无效。次数和输入在接受请求时固定下来，测试途中编辑请求参数不改变当前这一组。

设置 `g_nnBenchmarkCancelRequested=true` 可取消后续提交。NPU 已提交的运算仍持有缓冲区，必须等它完成或超时，不会强行复用；原有 1 ms 超时和异常锁定继续生效。

设置 `g_nnTimingResetRequested=true` 可请求清统计并恢复普通自动记录，检查 `g_nnTimingResetAccepted` 是否为 true。正在测试或 NPU 运算在途时拒绝清统计；清统计不会解除 NN 故障，也不会重置 Timer2。重新提交一组获准的重复测试也会自动清空上一组统计。

失败或无效输出不进入成功耗时的最短/平均/最长统计，查看 `rejectedOutputs` 和 `g_nnTimeoutCount`。NPU 通过控制中断检测到超时后，后台恢复服务时才更新本组失败状态与统计；不能只看平均值忽略超时。

## 5. 已接入的 NPU 怎样测

选择 `CPU1_LAUNCHXL_NPU_FLASH`，完整 Build、加载并从初始化运行；该配置输入为 16 项 FLOAT32，内部使用四层 NPU，输出为四项 FLOAT32。模型库会在最终输出还原之后、发布完成标志之前调用 `DAB_NN_noteNpuCompletion()`，因此 `npuCompletion` 已有真实完成路径的时间点；具体步骤见 [NPU 接入说明](NPU_integration_guide_zh.md)。

该配置固定用于候选模型核对和计时，功率启动拒绝码为 7，板确认宏不能绕过。输入只接受 Vin 90～140 V；优先使用说明文档中的 90、100、110、120、130、140 V 六组值，92.2～92.5 V 已发现输出越界，现有检查会拒绝并锁定故障，不能放宽保护来收集成功耗时。

先核对 `g_nnLastOutput` 与候选 ONNX，再保存完整 `g_nnTiming`。`npuCompletion` 含运行库、NPU、层间 CPU 处理和完成中断响应；`npuSubmit` 仅为启动调用，不能代表完整前向耗时。

## 6. 对比和保存

分别将暂停后获取的整个统计结构保存为 `fpu_timing.json`、`npu_timing.json`，可以直接保存结构 JSON，或使用 `{"g_nnTiming": {...}}` 包装。使用项目中的对比工具：

```powershell
python tools/compare_nn_timing.py fpu_timing.json npu_timing.json --out nn_timing_comparison.md
```

工具按原始 Tick、总和和样本数重新计算最短/平均/最长微秒值，拒绝未冻结、零时间、无样本或含无效输出的记录，并给出端到端平均耗时比 `FPU/NPU`。比值大于 1 才表示本次 NPU 路径更快，不能预设小网络一定获得加速。

至少记录板卡、150 MHz 时钟、FLASH/RAM、O2/O3、DEBUG 定义、函数和权重所在存储区、模型版本、输入、预热次数、有效样本数、错误/超时数。当前 FLASH 配置为 O2 且定义 DEBUG；不要把它称为关闭所有检查的 Release 测量。

当前重复测试保留 ADC/PWM 中断和后台服务，但处于待机，因此不包含运行状态下完整控制算法的负载。所有计时都是墙钟经过时间，包含区间内的中断占用；最短值也不是已剔除中断的纯运算周期。上线前还需验证实际运行负载、最坏完成延迟和保护时效。

TI 官方提供模型性能测量例程与板上周期计数方法，可作为独立验证参考；官方电弧模型的时间不能替代本 DAB 小网络实测。[TI 模型性能测量说明](https://software-dl.ti.com/C2000/esd/mcu_ai/user_guide/deployment/npu_device_deployment.html#model-performance-profiling)

## 7. 已完成的本地验证

- TI C2000 编译和 FLASH 链接；FPU 前向函数仍位于 RAM，权重及前向数学表达式未改变。
- 121 组原表达式参考输出，最大绝对误差保持约 `3.91155481e-7`。
- 模拟时间源：计时边界、微秒换算、Timer2 回绕、64 位总和、计数饱和、缓存命中不增样本、预热排除、有限次数及结果冻结。
- 启动互斥、请求拒绝、取消和恢复普通推理；NPU 模拟接口验证提交与完成分离、可选完成钩子、在途缓冲区归属、超时和错误不计为成功。
- 现有 ADC、PWM、保护、通信及看门狗回归测试。

上述模拟测试只能证明统计和调用逻辑，不能给出真实 FPU/NPU 速度；板上实测结果待补充。
