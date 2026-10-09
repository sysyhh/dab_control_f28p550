# DAB NPU 模型接入与开发板核对

## 1. 当前交付范围

新增 `CPU1_LAUNCHXL_NPU_FLASH`，已用 TI MCU NNC 2.1.0 和 C2000 CGT 22.6.2.LTS 生成并链接真实 DAB 模型库。四层主要矩阵计算使用 NPU，输入准备、层间数据转换和最终 FLOAT32 输出还原仍由 CPU 完成；实际开发板输出与耗时尚待核对。

**当前模型仅用于数值核对和耗时测试，禁止启动功率输出。** 原因是 INT8 量化精度尚不足，不是板卡配置未确认；即使把板确认和自动启动宏置 1，`DAB_Control_start()` 也会返回拒绝码 7。原 `CPU1_LAUNCHXL_FLASH` 继续使用 FPU，其板确认、自动启动和保护门限没有被本次接入改动。

## 2. 模型与输入输出

| 项目 | FPU 基准 | 当前 NPU 候选 |
|---|---|---|
| 网络 | 3→29→12→6→4 | 补齐为 16→32→16→16→4 |
| 输入 | `[-0.5, Vin/140, 0.285714]` | FLOAT32 `[1,16]`；除第 1 项外全部为零 |
| 第 1 项 | `Vin/140` | `Vin/25 - 4.6`，索引从 0 开始 |
| 常量输入 | 每次准备 | 已折入第一层权重/偏置，不再重复输入 |
| 内部运算 | FLOAT32 | INT8 权重与激活，整数累加及缩放 |
| 输出 | FLOAT32 `[1,4]` | FLOAT32 `[1,1,1,4]`，内存连续四个 float |
| 输出顺序 | D1、D0、D2、T | 相同，不能调换 D0 和 D2 |
| 检查范围 | 保留原有逻辑 | 只接受 Vin 90～140 V；这不是原模型完整训练域声明 |

原候选 ONNX 使用 `MatMul`。TI NNC 2.1.0 的 C28 路径编译该文件时会生成 CPU 计算循环，即使头文件带有 NPU 宏，也不能据此认为矩阵计算使用 NPU。因此新增 `prepare_npu_conv.py`，将四层等价改写为 1×1 `Conv` 并调整数据排列，保持已有量化参数和权重数值。

90～140 V、步长 0.1 V 的 501 组 ONNX Runtime 对照中，改写前后的输出差为 **0**。`compile_dab_npu.py` 还检查生成代码有四个硬件阶段，防止以后模型修改后悄悄退回 CPU；这项检查不能替代开发板验证。

## 3. 文件和内存

| 文件 | 作用 |
|---|---|
| `model/dab_npu_tinpu_ptq.onnx` | 原 INT8 候选，保留用于追踪和对照 |
| `model/dab_npu_tinpu_conv.onnx` | 等价 1×1 Conv 表达，供 TI NNC 编译 |
| `model/dab_npu_conv_validation.json` | 501 组等价对照、FLOAT 基准误差和六组核对值 |
| `model/generated/npu/mod.a` | 实际 C28/NPU 模型库；普通 CCS Build 直接使用它 |
| `model/generated/npu/tvmgen_default.h` | TI 生成的输入输出和运行函数声明 |
| `model/generated/npu/dab_npu_contract.h` | 经生成头文件检查后写入的维度、范围和禁止功率控制标记 |
| `model/generated/npu/lib0.c`～`lib2.c` | 模型及运行代码，保留供检查；已从 CCS 自动编译源文件中排除 |
| `model/generated/npu/manifest.json` | 编译版本、选项、模型和库的 SHA-256 摘要 |

CCS 仅链接 `mod.a`，不要再次把 `lib0.c`～`lib2.c` 添加到编译，否则会重复定义符号。不要把电弧识别例程的库替换进来。

链接检查确认 `.bss.noinit.tvm` 位于 GS1，起始地址 `0xE000`，当前占 `0x60` 个 C28 地址单位，即 192 字节；GS1 总共 `0x2000` 个地址单位。`.rodata.tvm` 位于 FLASH_BANK1 的 `0xA0000`；其他模型常量和代码由链接文件放入 FLASH，不能只用 `.rodata.tvm` 大小代表整个模型占用。

输入、输出和描述对象保持到任务结束。`TI_NPU_init()` 开启 NPU 时钟和中断源；生成运行库注册并处理 NPU 中断，不额外注册另一个中断函数覆盖它。主循环一次只允许一项任务，完成后检查输出，再发布完整四项缓存。

## 4. 在 CCS 中运行

1. 刷新项目，在 Build Configurations 中选择 **`CPU1_LAUNCHXL_NPU_FLASH`**；若列表未更新，关闭并重新打开项目，使 CCS 重新读取 `.cproject`。
2. 执行 Build，确认编译命令有 `DAB_USE_HARDWARE_NPU`、`DAB_NPU_DAB16_MODEL`，链接命令包含 `model/generated/npu/mod.a`。该配置另外定义 `DAB_AUTO_START=0`、`DAB_BOARD_CONFIG_CONFIRMED=0`，无需改动公共头文件。
3. 加载此配置的 `CPU1_LAUNCHXL_NPU_FLASH/dab_control_f28p550.out`，完整复位并运行初始化；不能只切换配置后继续运行先前的 FPU 程序。
4. 导入 [CCS 观察变量](NN_timing_CCS_watch.txt)。当前源码保留已有的启动即请求测试设置，默认 Vin=90 V、预热 10 次、正式 1000 次；连续运行到完成后暂停查看。
5. 应看到下表；如果未自动开始，可按下一节手动提交。测量期间不要单步或暂停，因为 Timer2 在调试暂停时继续运行。

| 观察项 | 成功预期 |
|---|---|
| `g_dabState` | 1，待机 |
| `g_nnBenchmarkState` | 2，正式样本完成 |
| `g_nnBenchmarkCompleted` | 1000 |
| `g_nnBenchmarkWarmupCompleted` | 10 |
| `g_nnTiming.backend` | 1 |
| `g_nnTiming.frozen` | true |
| `g_nnTiming.npuCompletion.samples` | 1000 |
| `g_nnTiming.npuObserved.samples` | 1000 |
| `g_nnTiming.fpuForward.samples` | 0 |
| `g_nnTimeoutCount`、`g_nnTiming.rejectedOutputs` | 0 |
| `g_nnLastOutput` | Vin=90 V 时离线预期 `[0.4375, 0.25, 0, 1]`，需要实板核对 |

`g_nnLastOutput` 供只读观察。不要在 CCS 中改写输出、忙标志、完成标志或故障标志来绕过检查；运行代码应通过 `DAB_NN_getOutput()` 取得带有效性检查的完整结果。

## 5. 换输入与核对数值

每组测试只接受一次参数快照；上一组结束后编辑以下变量，最后提交请求：

```c
g_nnBenchmarkIterations = 1000;
g_nnBenchmarkWarmup = 10;
g_nnBenchmarkVin = 100.0f;
g_nnBenchmarkRequested = true;
```

下表是 ONNX Runtime 的候选模型输出，**不是板上实测**。先逐组检查这六个点；实板应与候选模型一致，随后再与同输入的 FPU 结果比较误差。

| Vin/V | D1 | D0 | D2 | T |
|---:|---:|---:|---:|---:|
| 90 | 0.4375 | 0.25 | 0 | 1 |
| 100 | 0.484375 | 0.09375 | 0 | 1.09375 |
| 110 | 0.484375 | 0.109375 | 0 | 1.015625 |
| 120 | 0.390625 | 0.09375 | 0 | 0.859375 |
| 130 | 0.625 | 0.21875 | 0.125 | 0.96875 |
| 140 | 0.84375 | 0.203125 | 0.09375 | 1.15625 |

Vin 超出 90～140 V 的测试请求返回拒绝码 4，不启动 NPU。当前 501 点对照还发现 **92.2、92.3、92.4、92.5 V** 的候选输出超过已有相位合理性范围；这些输入预计会触发 NN 故障并使测试失败，保留该行为，不放宽保护来获得计时结果。故障后需完整复位再测试，晚完成不解除锁定。

## 6. 怎样比较耗时

NPU 库在最后一层完成、CPU 输出还原之后，先调用 `DAB_NN_noteNpuCompletion()` 记录 Timer2，再发布 `tvmgen_default_finished=1`。该改动由编译脚本自动重复生成，不能在重新编译模型时遗漏。

| 统计项 | 当前准确含义 |
|---|---|
| `npuSubmit` | 运行函数调用，包括首次数据准备和首层启动；不能表示完整前向计算 |
| `npuCompletion` | 开始提交至最终 FLOAT32 输出准备完成，包含四层 NPU、CPU 转换和中断响应 |
| `npuObserved` | 开始提交至后台发现完成，还包含后台查询延迟 |
| `endToEnd` | 输入准备至有效结果发布，优先用于比较应用得到结果的耗时 |

切回 `CPU1_LAUNCHXL_FLASH` 后，按 [计时说明](NN_timing_guide_zh.md)测相同 Vin、预热和样本数，保存 FPU/NPU 两份 `g_nnTiming`，用 `tools/compare_nn_timing.py` 比较。两个配置的应用代码均为 O2；生成模型库为 O3，FPU 前向在 RAM，NPU 运行库代码在 FLASH，这些差别应随结果记录。

两种实现的网络尺寸和数值精度不同，因此结果表示当前两条实现路径的耗时比较，不能表述为同等精度下的纯硬件加速比。所有统计包含期间的中断占用，`npuCompletion` 也不是裸 NPU 运算周期；小网络不保证更快。

## 7. 重新生成模型库

普通 CCS 编译不需要 Python、PyTorch 或重新量化，交付的 `mod.a` 已可链接。只有修改候选模型或重新生成库时，才需 Python 3.10、`ti_mcu_nnc==2.1.0`、`numpy==1.26.4`、`onnx==1.16.2`、`onnxruntime==1.20.1` 及 TI 编译器/SDK。

本机已准备隔离的 Python 3.10 环境，在 `ccs_projects` 目录执行：

```powershell
review_20261003/npu_integration_20261009/python310/python.exe dab_control_f28p550/tools/compile_dab_npu.py
```

编译器和 SDK 默认使用本机现有 E 盘路径，可用 `--cgt`、`--sdk` 指定其他安装位置；TI 工具路径不能包含空格。脚本执行等价转换、501 点对照、TI NNC 编译、维度和硬件阶段检查、完成时间钩子写入及库更新，并保存清单。它不会重新训练模型，也不会把模型标记为已通过功率控制验收。

## 8. 剩余验收与精度改进

本地已通过真实 TI 模型编译、NPU/FPU FLASH 链接、501 点转换等价对照，以及输入适配、范围、异步任务、计时、超时与启动禁止测试。电脑上的接口替身只验证程序逻辑，不能证明开发板实际执行时间或硬件数值。

与 FLOAT ONNX 基准比较时，501 点最大绝对误差依次约为 `[0.0488685, 0.0370852, 0.0269486, 0.0488721]`。以基础周期 2500 估算，相位误差约 `[133,101,74]` 个计数、周期误差约 123 个计数；估算未替代完整 PWM 参数包对照，明显不满足一个计数的精度目标。先前 51 个整数电压点报告的误差更小，是因为较稀疏的点没有覆盖这些量化转换位置。

| 待完成项 | 通过条件 |
|---|---|
| 实板候选模型核对 | 六组输出与上表核对，再扫完整检查范围，保存 NPU 与 ONNX/FPU 差异 |
| 实板计时 | 成功完成 1000 个样本，完成时间、后台发现时间、端到端时间齐全且无超时 |
| 中断与保护并发 | ADC 数据持续更新，控制期限和故障检查有效，停止及超时后无缓冲区覆盖 |
| 提高量化精度 | 补齐真实代表性数据和训练定义，评估量化感知训练、输出缩放和网络调整，再比较完整 PWM 参数包 |
| 允许功率控制 | 数值、参数边界、最小脉宽、完整板上保护验收完成后，专门审阅并修改批准标记；不能仅改板确认宏 |

官方依据：[TI NNC 安装说明](https://software-dl.ti.com/mctools/nnc/mcu/v2.1.0/installing.html)、[TI NNC 编译与 CCS 集成](https://software-dl.ti.com/mctools/nnc/mcu/v2.1.0/compiling.html)。本项目的真实硬件分配还通过本地生成的 `lib1.c`、`lib2.c` 和最终链接文件核对。
