# F28P55x NPU 性能外部证据核对

检索日期：2026-10-10。范围：TI 官方文档、TI 官方代码仓库和 TI E2E；未操作开发板，未更改模型或固件。

## 1. 最接近本项目的官方对照

已下载并逐项查看 SDAA185（2026 年 2 月）PDF 第 32 页图像，确认 §13.1 三张表均为 **F28P55x CPU 与 NPU 的正弦回归模型单次推理延迟**，单位原为 ms，下表乘以 1000 转为 μs。

| 正弦模型隐藏层宽度 | CPU μs | NPU μs | CPU/NPU |
|---|---:|---:|---:|
| 16 | 22.3 | 25.2 | 0.885 |
| 64 | 270.6 | 214.6 | 1.261 |
| 128 | 1012 | 711.6 | 1.422 |

§3.2 明确 64 宽模型为 `1→64→64→1`，两次 ReLU；表中 16/128 是该正弦任务的宽度变体。§13.2.2 将小模型 CPU 更快归因于传输、配置、等待及结果读取的额外成本。[TI SDAA185，第 5、32、33 页](https://www.ti.com/lit/pdf/sdaa185)

限制：§13.1 未逐表列出 CPU/NPU 时钟、编译优化级别、代码运行在 Flash/RAM 的位置、计时边界或中断负载；CPU 列也不能直接认定等同本项目手写 FPU 路径。本文结构与本项目四层网络不同，不能由 25.2 μs 推导本项目必然达到该数值；官方不同路径的精度指标也不完全一致。[同一官方 PDF](https://www.ti.com/lit/pdf/sdaa185)

## 2. 官方代码项目的量级及容易误用的结果

| 官方例程 | 平台与公开结果 | 可用于判断什么 |
|---|---|---|
| `grid_stability`，`CLS_ResCat_3k` | F28P55x；无特征提取：CPU 6371.13/NPU 1595.67 μs；有特征提取：CPU 3339.07/NPU 836.73 μs | 更复杂网络可以获得约 4 倍加速，但不是小型控制 MLP 的直接对照 |
| `torque_measurement_regression` | F28P55x，10 输入变量，`REGR_10k`，128/256 帧：114102/187445 cycles | 回归部署实例；README 未给出严格的 CPU/NPU 同模型对照，不能把两个帧长当作两种后端 |
| `induction_motor_speed_prediction`，`REGR_1k` | **F29H85x**，1/4/8 帧：9.45/17.59/36.44 μs | 平台不同，不能引用为 F28P55x NPU 成绩 |

来源分别为 [TI grid_stability README](https://github.com/TexasInstruments/tinyml-tensorlab/blob/main/tinyml-modelzoo/examples/grid_stability/readme.md)、[TI torque README](https://github.com/TexasInstruments/tinyml-tensorlab/blob/main/tinyml-modelzoo/examples/torque_measurement_regression/readme.md)及 [配置](https://github.com/TexasInstruments/tinyml-tensorlab/blob/main/tinyml-modelzoo/examples/torque_measurement_regression/config.yaml)、[TI induction motor README](https://github.com/TexasInstruments/tinyml-tensorlab/blob/main/tinyml-modelzoo/examples/induction_motor_speed_prediction/readme.md)。这些仓库的 `main` 会变化，应保留检索日期。

TI Tensorlab 另给出 F28P55 的典型分类模型 NPU 150～600 μs，但仅称“典型”，缺少完整复现条件，证据强度低于明确模型的实测表，不能据此验收本项目。[TI Tensorlab NPU deployment §9.2.8](https://software-dl.ti.com/C2000/esd/mcu_ai/user_guide/deployment/npu_device_deployment.html)

本项目 P5 的约 103 μs 落在官方公开模型覆盖的数十至数百微秒区间；相对官方 16 宽正弦例子的 25.2 μs 仍高约 4 倍。因此“量级可出现”与“本项目已经最优”是两件事，现有外部数据不能证明后者。

## 3. NPU 比 CPU 慢并非孤例，但论坛不能代替根因证明

TI E2E 存在同一型号、同一模型分别编译成 soft/hard 后 hard 更慢的报告，涉及 Conv2D 和 FC；公开答复只要求核对支持范围，未给出模型文件、逐段时间或已验证修复。因此它只能证明类似现象有人遇到，不能证明当前项目同因，也不能认定“全连接不支持”。[TI E2E 原帖](https://e2e.ti.com/support/microcontrollers/c2000-microcontrollers-group/c2000/f/c2000-microcontrollers-forum/1463713/tms320f28p550sj-tms320f28p550sc-npu-performance-issue-same-model-compiled-for-npu-shows-worst-performance-compare-to-the-model-compiled-for-cpu)

## 4. 当前编译器版本是具体可核对的改进机会

| 版本 | 官方明确说明 | 对本项目的意义 |
|---|---|---|
| NNC 2.1.0 | 扩展 8 位激活与 8/4/2 位权重的可卸载配置 | 项目当前基线；“能够编译”不等于装载开销已最优 |
| NNC 2.1.1 | **优化 F28P55x NPU setup 时间**；新增内存及卸载摘要；`skip_normalize` 的提取缩放值从整数改为 float | 应独立对照生成代码和实测，且核对输入缩放的契约变化 |
| NNC 2.1.2 | 编译时移除 C2000Ware SDK 依赖；生成模型库的应用链接要求 **C2000Ware 26.0 或更新** | 当前工程使用较早的 SDK，不能直接替换模型库而假设兼容 |

来源：[TI NNC 2.1.1 release notes](https://software-dl.ti.com/mctools/nnc/mcu/v2.1.1/release-notes.html)、[TI NNC 2.1.2 release notes](https://software-dl.ti.com/mctools/nnc/mcu/users_guide/release-notes.html)。发布说明未承诺具体百分比，也未证明新版本优化与本项目 P4/P5 已做的修改相互独立；实际收益必须重新测量。

## 5. 模型设计与运行时间应分别验收

NNC 只将匹配的层模式交给 NPU，其余操作由 CPU 执行；输入/输出特征图主要为 8 位整数，权重为 2/4/8 位，通道通常要求 4 的倍数，当前只支持 batch=1。[TI NNC Layer Patterns](https://software-dl.ti.com/mctools/nnc/mcu/users_guide/layer_patterns.html)

TI 官方设计指南建议按 NPU 约束设计模型，并警告不匹配配置可能回落到软件；PWCONV 要求通道为 4 的倍数，FC 有最小输入规模限制。[TI NPU Configuration Guidelines](https://github.com/TexasInstruments/tinyml-tensorlab/blob/main/tinyml-modelzoo/docs/NPU_CONFIGURATION_GUIDELINES.md)

这些约束解释了为什么极小输入、额外补齐、层数和软件转换会影响延迟，但不能仅凭约束推算某段裸 NPU cycles。后续应记录每层实际卸载、数据尺寸、装载字数和普通版耗时；精度验收还须比较同一输入下的 FPU、量化软件参考与实板输出，只有速度提高不能证明模型适用于控制。

## 6. 据现有证据可作出的判断

- 固有启动/传输成本确实存在，小模型不保证快于 CPU；官方 16 宽案例已经显示这一点。
- 编译和部署方式同时影响速度，新版 NNC 对 setup 的明确优化说明不能把当前 103 μs 全部视为硬件下限。
- 外部证据支持继续做有限、可复现的验证，但不支持承诺当前网络必然超过本项目 28.7 μs FPU。是否超过，应在精度相当、计时边界一致、同一平台和中断条件下判定。
