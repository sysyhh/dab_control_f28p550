# F28P550：原生三维输入 FC 硬件部署与实机性能评估

日期：2026-10-31。测试平台 LAUNCHXL-F28P55X，SYSCLK 150 MHz。Teacher 仅为 `dab_nn.c` 中的 FPU 网络 **3→29→12→6→4**，输入 `[-0.5, Vin/140, 0.285714]`，输出 `[D1, D0, D2, T]`。未重新训练，未把常量折进第一层偏置，未改有效权重。

本轮 PPT 对照数据全部来自这次原生三维输入 FPU/FC 实验。此前 PWCONV / Vin 折叠的推理时间与精度 **不再作为有效对照**。

隔离范围：

- 生成库：`model/generated/fc_int8`、`model/generated/fc_int4`（及 `*_detail`）。
- CCS 测试构建：`CPU1_LAUNCHXL_FC_INT8_FLASH`、`CPU1_LAUNCHXL_FC_INT4_FLASH`。
- 正式交付库 `model/generated/npu/mod.a` 未覆盖，SHA-256 仍为 `6714f8e2ee9909ecc1ba7a516df8f1c5e84369298d145549d3a5832530d99390`。
- `DAB_NPU_POWER_CONTROL_APPROVED=0`，`DAB_AUTO_START=0`，`DAB_BOARD_CONFIG_CONFIRMED=0`。四路功率 PWM 的 OST 在全部轮次保持锁定，未启动功率变换，FC 输出未写入比较寄存器。

硬件 FC 使用现有内部测试开关 `FORCE_NO_TI_C28_SOFT_OFFLOAD=true`。这不是量产路径，只用于隔离实验。

---

## 1. 对照表（正式成绩，关闭 detail-profile）

条件：Vin=90 V，预热 10 次，正式 1000 次，三轮独立重新编译/烧录/运行。三轮端到端均值完全重复。

| 指标 | 原始 FPU | INT8 FC | INT4 FC |
|---|---|---|---|
| 原生输入维度 | 3 | 3（另补 13 个零通道） | 3（另补 5 个零通道） |
| 网络结构 | 3-29-12-6-4 | 16-29-16-16-4 | 8-29-12-8-4 |
| 硬件 FC 层数 | — | **4 层 / 5 次 NPU 启动**（16→29 拆成 2 个 sublayer） | **4 层 / 5 次 NPU 启动**（8→29 拆成 2 个 sublayer） |
| MAC 数量 | 531 | 1248 | 708 |
| 端到端平均 | **28.680 μs** | **147.213 μs** | **114.126 μs** |
| 最小 / 最大 | 23.680 / 42.133 μs | 141.860 / 159.140 μs | 111.047 / 128.300 μs |
| 标准差 | 4.348 μs | 5.073 μs | 4.008 μs |
| P95 / P99 | 36.153 / 37.680 μs | 153.207 / 156.240 μs | 122.373 / 125.393 μs |
| 相对 FPU | 1.00× | **5.13× 更慢** | **3.98× 更慢** |
| 最大 PWM 计数误差 | 0（基准） | **335**（Vin=133.3 V） | **1730**（Vin=134.8 V） |
| 非法输出点（501 点） | 0 | 0 | **50**（含 Vin=90 V） |
| Vin=90 冻结输出 | `[0.449986, 0.249993, -2.65e-6, 0.999997]` | `[0.453125, 0.25, 0, 1]` | `[0.670103, 0.288516, -0.009307, 1.023768]`（非法） |

FPU 前向 23.726 μs，准备 1.992 μs，发布 2.928 μs。INT8 前台 CPU 39.318 μs，完成 ISR 累计 83.114 μs，硬件等待约 21.915 μs。INT4 前台 35.473 μs，ISR 65.451 μs，硬件等待约 9.349 μs。

---

## 2. 硬件映射验收（板上）

不能用 NNC 日志 `FC [X]` 或 `TVMGEN_DEFAULT_TI_NPU` 宏代替。本轮同时满足：

| 判据 | INT8 | INT4 |
|---|---|---|
| `ti_npu_fullyConnectedNHWC` | 4 个生成函数 | 4 个生成函数 |
| 软件 `TINIE_fullyConnected(` | 0 | 0 |
| `FC_*_INS` | `iCm8b16_oCm4` + `oC1LL` | `kB4_iCm8_oCm4` + `oC2L` |
| `tinie_curr_layer += 1` | 4 | 4 |
| 板上 `npuIsrLastCount` | **5** | **5** |
| `npuIsrLastLayerCount` | **`[0, 2, 1, 1, 1]`** | **`[0, 2, 1, 1, 1]`** |
| ISR 总次数 / 1000 样本 | 5000 | 5000 |
| `npuCompletion.samples` | 1000 | 1000 |
| CPU dense / PWCONV 符号 | 无 | 无 |

第一层因为输出 29 被 NNC 拆成 2 个硬件 sublayer，所以是 5 次完成中断，不是 4 次。层 0 的 ISR 计数保持为 0，与 TINIE 先自增再启动的调度一致。ReLU 仍在 CPU（日志 `nn.relu` 3 次），这是 FC 融合模式的限制，不是 fallback。

---

## 3. 端到端分项（INT8 主线）

正式成绩关闭 `--detail-profile`。下表的分段来自单独的插桩库，**不能与 147.213 μs 相加或替代**；插桩后 INT8 端到端被抬到 175.879 μs。

| 分段 | INT8 详细 μs | 调用 | 说明 |
|---|---:|---:|---|
| 输入量化 | 13.737 | 1 | 16 路 float→int8，含 13 个恒零通道 |
| 打包 | 5.199 | 4 | 层间 pack |
| 拆包 | 4.500 | 4 | 层间 unpack |
| 隐层 ReLU+再量化 | **43.960** | 3 | 全部在 CPU，是 INT8 相对 FPU 变慢的最大单项 |
| 参数装载 | 25.162 | 5 | 含 16→29 的第二 sublayer |
| 指令装载 | 6.973 | 5 | 两张 INS 表，复用已开启 |
| 寄存器 | 12.480 | 5 | 每 sublayer 写 MMR |
| 四层启动→完成中断 | 6.805+10.165+7.402+6.274 | 2+1+1+1 | 硬件阵列等待；第一层两次 |
| 输出反量化 | 0.420 | 1 | float 恢复 |

INT4 详细库同样表明隐层转换 36.300 μs、参数 11.104 μs。INT4 正式成绩更快，主要是参数区更小，不是精度更好。

结论：四层硬件等待合计大约 22–30 μs，已经和 FPU 前向同一量级。端到端慢在 **逐层装载 + 5 次 ISR 调度 + 三次 CPU ReLU/再量化**，不是 MAC 吞吐不够。

---

## 4. 精度（相对原始 FPU，Vin=90～140 V / 0.1 V，501 点）

| 集合 | INT8 最大 PWM | INT8 非法 | INT4 最大 PWM | INT4 非法 |
|---|---:|---:|---:|---:|
| 官方 90–140 / 0.1 V | 335 | 0 | 1730 | 50 |
| 加密 92.2–92.5 / 0.01 V | 56 | 0 | 542 | 31 |
| 板上 Vin=90 快照 | 与 ONNX 一致，PWM 约 8 计数 | 合法 | 与 ONNX 一致 | **非法**（D2=-0.0093） |

INT8 最差点 Vin=133.3 V。T 绝对误差 0.119 × 2500 ≈ 296 个周期计数，与 `pwm_tbprd_max=296` 一致。INT4 在 90.0–91.5 V 等 50 个官方网格点产生非法控制量；板上 1000 次正式样本全部被记为拒绝输出（含 10 次预热共 1010），但计时样本仍为 1000。

验收：最大 PWM 不超过 1 个计数、不允许非法输出。两条都不满足。精度不合格没有阻止计时，但这些速度数字 **不能解释成已经具备控制应用可行性**。

---

## 5. 三个研究问题

1. **保留原始三维输入后，FC 在 F28P550 上的实际推理时间是多少？**  
   INT8 硬件 FC 端到端平均 **147.213 μs**（最小 141.860，最大 159.140，P95 153.207）。INT4 为 **114.126 μs**，但这是非法输出上的计时。

2. **FC 相比原始 FPU 究竟快还是慢，差距主要来自哪些环节？**  
   慢。INT8 是 FPU 的 5.13 倍，INT4 是 3.98 倍。硬件阵列等待约 22 μs，并不慢于 FPU 前向 23.7 μs。差距主要是：三次 CPU ReLU/再量化（详细计时约 44 μs）、五次参数/指令/寄存器装载（约 25+7+12 μs）、以及五次层间 ISR（正式 ISR 累计 83 μs，与装载和 ReLU 重叠，不能和分段简单相加）。

3. **在满足原始控制精度要求的前提下，FC 是否具有实际部署价值？**  
   **没有。** 速度慢于原始 FPU，INT8 PWM 误差 335 个计数，INT4 出现非法输出。内部硬件开关不能当作产品策略。本轮不建议把 FC 网络接入功率闭环，也不建议用这些数字替换 PPT 里的 FPU 基准。

---

## 6. 复现

```powershell
# 从已审计的零神经元 NNC 产物打包固件库（禁止写入 model/generated/npu）
review_20261003/npu_integration_20261009/nnc211_env/python.exe `
  dab_control_f28p550/model/experiments/fc/compile_fc_npu.py --package-firmware `
  --src dab_control_f28p550/model/experiments/fc/generated/int8_zero_neuron_force_hw `
  --out dab_control_f28p550/model/generated/fc_int8 `
  --onnx dab_control_f28p550/model/experiments/fc/onnx/int8_zero_neuron.onnx `
  --optimization-level 5 --reuse-instructions

python dab_control_f28p550/tools/prepare_fc_ccs_build.py --variant all

python tools/c2000_debug/benchmark_nn.py --backend fpu --label fc_native_fpu --repeats 3
python tools/c2000_debug/benchmark_nn.py --backend fc_int8 --label fc_native_int8 --repeats 3
python tools/c2000_debug/benchmark_nn.py --backend fc_int4 --label fc_native_int4 --repeats 3
```

详细分段在同样命令上对 `fc_*_detail` 库加 `--detail-profile` 后各跑 1 轮。501 点精度：`python dab_control_f28p550/model/experiments/fc/run_fc_board_campaign.py --skip-package`。

原始 JSON：

- 板上汇总：`tools/c2000_debug/benchmarks/20261031_00{3715_fc_native_fpu,3837_fc_native_int8,4031_fc_native_int4,3953_fc_native_int8_detail,4150_fc_native_int4_detail}/summary.json`
- 副本：`model/experiments/fc/results/board_runs/`
- 精度：`model/experiments/fc/results/board_accuracy_501.json`
- 抽取：`model/experiments/fc/results/board_timing_extract.json`
