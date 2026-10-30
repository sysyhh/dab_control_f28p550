# F28P550 NPU：基于原始 3-29-12-6-4 的 FC 算子映射实验报告

日期：2026-10-30。Teacher 仅为 `dab_nn.c` 中的 FPU 网络 **3→29→12→6→4**，隐藏层 ReLU，输出线性且顺序为 `[D1, D0, D2, T]`。未重新训练，未改有效权重、偏置、激活或输入语义。输入保持 `[-0.5, Vin/140, 0.285714]`，新增维严格补零。

产物全部在 `dab_control_f28p550/model/experiments/fc/`。正式 `model/generated/npu/mod.a`、模型清单和 FPU 固件未覆盖。未改 CCS 正式配置，未烧录，未放开功率/精度保护。

独立编译入口是 `compile_fc_npu.py`（NNC 2.1.1），**禁止** `MatMul→Conv`。硬件判据不是 `TVMGEN_DEFAULT_TI_NPU` 宏，也不是日志里的 `FC [X]`，而是生成代码中的 `tvmgen_default_ti_npu_fullyConnectedNHWC_*`、`FC_*_INS` 以及 `tinie_curr_layer += 1`。

---

## 1. NNC 2.1.1 对 FC 的实际支持

官方 `layer_configs_npu`：

| 权重 | iC | oC |
|---|---|---|
| INT8（kB=8） | `m1b16`，至少 16 | any |
| INT4（kB=4） | `m1b8`，至少 8 | any |

没有 2-bit FC。参数缓冲 2048 字节；无 host post-process 时 iC 上限 2032。`config_fc.py` 对 INT8 `iC<16`、INT4 `iC<8` 给出 WARNING，硬件检查失败。

ONNX 模式是 **MatMul => BNORM**（bias → scale → 右移 → Floor → Clip）。**ReLU 不在 FC 融合模式里。**

C28 默认（`tinie.py`）：即使 target 是 `ti-npu` hard，FC 也注册为软件库 `TINIE_fullyConnected`（DMAC）。硬件 `TINIE_fullyConnectedNHWC` 只在环境变量 `FORCE_NO_TI_C28_SOFT_OFFLOAD=true` 时启用，源码注释写明这是 **TI 内部测试开关**。

另外，TINPU 导出常用 `(1,1,1,1)` 量化常量，把 2D 激活广播成 `[1,1,1,C]`。NNC 随后在 `qnn.dense` 与 `bias_add` 之间插入 `reshape`，**FC 模式完全匹配不上**，生成的是 CPU `nn.contrib_dense_pack`。本实验把无 Pad 的图压回 NC 2D（不是 Conv 改写）后，模式才能匹配。

最小模型（压成 2D 后）实测：

| 模型 | 路径 | 结果 |
|---|---|---|
| INT8 16→4 | C28 默认 | 日志 `FC [X]`，但是 `TINIE_fullyConnected(` 软件库；无 INS；`TVMGEN_DEFAULT_TI_NPU` 仍为 1 |
| INT8 16→4 | FORCE_HW | **硬件 FC**：`ti_npu_fullyConnectedNHWC` + `FC_iB8_oB8_kB8_iCm8b16_oCm4_INS` + `tinie_curr_layer += 1` |
| INT8 8→4 | FORCE_HW | 未卸载：`does not support iC less than 16` |
| INT4 8→4 | FORCE_HW | **硬件 FC**：`FC_iB8_oB8_kB4_iCm8_oCm4_INS` |
| INT8 3→4 | FORCE_HW | 未卸载：iC&lt;16 |
| INT8 16→8→8→4 | FORCE_HW | 仅第一层硬件；两层 iC=8 被拒绝 |

结论：INT8 输入至少 16、INT4 至少 8、输出无硬上限，与文档一致。C28 量产路径的 FC `[X]` **不是** NPU 阵列。

---

## 2. INT8 / INT4 最终网络结构

全部从 `dab_nn.c` 的 3-29-12-6-4 复制有效块；新增列/新增输出神经元的权重和偏置为 0。

| 候选 | 结构 | 权重量化 | 中间维适配 |
|---|---|---|---|
| `int8_input_pad` | 16→29→12→6→4 | INT8 | 12→16、6→16 显式 Pad |
| `int8_zero_neuron` | 16→29→16→16→4 | INT8 | FC2/FC3 增加全零输出神经元 |
| `int4_input_pad` | 8→29→12→6→4 | INT4 | 6→8 显式 Pad |
| `int4_zero_neuron` | 8→29→12→8→4 | INT4 | FC3 增加 2 个全零输出神经元 |

输入补零：INT8 补 13 维，INT4 补 5 维。网络输入补零发生在特征构造，不进入计算图。

---

## 3. 输入补零 vs 输出零神经元

| 项目 | INT8 Pad | INT8 零神经元 | INT4 Pad | INT4 零神经元 |
|---|---:|---:|---:|---:|
| MAC | 972 | 1248 | 684 | 708 |
| 运行时 Pad | 2 | 0 | 1 | 0 |
| 原始 FPU MAC | 531 | 531 | 531 | 531 |
| 现网 PWCONV MAC | 640 | 640 | 640 | 640 |
| FP32 与 Teacher | 全零误差 | 全零误差 | 全零误差 | 全零误差 |
| NNC 2D FC 模式 | 否（4D Pad/Slice 打断） | 是 | 否 | 是 |
| FORCE_HW 四层硬件 FC | 否，全 CPU | **是** | 否，全 CPU | **是** |
| C28 默认 | 模式不匹配，CPU dense | 四层软件 `TINIE_fullyConnected` | — | — |

Pad 方案 MAC 更少，但 TINPU 把 `F.pad` 导出成 Pad/Slice/Concat/Cast 的 4D 图，NNC 不能匹配 FC，四层都落 CPU。零神经元方案 MAC 更高（INT8 高 28%），但可以保持 NC 2D MatMul，四层都能进硬件 FC（仅在内部开关下）。

不能预先认定谁更快：Pad 方案目前根本没有硬件 FC；零神经元方案有硬件 FC，但仍有逐层装载、ISR、以及层间 CPU ReLU。INT8 零神经元还把 16→29 拆成 2 个 NPU sublayer（oC=28+1）。

---

## 4. FP32 等价性

官方 90–140 V / 0.1 V（501 点），四个候选相对 `dab_nn.c`：

- 输出 max abs = `[0, 0, 0, 0]`
- 新增神经元输出 max abs = 0

即零填充后的 FP32 网络与原始 3-29-12-6-4 **逐点一致**，新增通道严格为零。

---

## 5. INT8 / INT4 量化精度（相对原始 FPU Teacher）

判据是逐维最大绝对误差、PWM 计数（`tbprd/cmpA2/cmpA4/phase34`）和非法控制量，不只看 MSE。PWM 映射与 `dab_control.c` / `dab_pwm.c` 在 ramp=1、duty=0 时一致。INT8 Pad 与 INT8 零神经元数值相同；INT4 两种方法也相同。

### INT8（两种结构相同）

| 集合 | max abs `[D1,D0,D2,T]` | 最大 PWM | 分项最大 | 非法输出 | 最差 Vin |
|---|---|---:|---|---:|---:|
| 校准 90–140 / 1 V | [0.134, 0.087, 0.074, 0.118] | 334 | T 295 / D1 334 / D2 184 / D0 217 | 0 | 133.0 V |
| 官方 90–140 / 0.1 V | [0.134, 0.087, 0.080, 0.119] | **335** | T 296 / D1 335 / D2 196 / D0 217 | 0 | 133.3 V |
| 加密 92.2–92.5 / 0.01 V | 见 `phase2.json` | 56 | — | 0 | 92.5 V |
| holdout 0.05 V 偏移 | 同量级 | 335 | — | 0 | 133.25 V |

官方网格 **没有** 非法移相比/周期。这比现网 PWCONV INT8 在 92.2–92.5 V 出现非法输出要干净，但 335 个 PWM 计数远大于 1 计数目标，也差于现网 PWCONV 的约 122 计数。本轮禁止把常数输入折进偏置、禁止 Vin 仿射重映射，量化仍按原始三特征，所以精度没有走那条已经失败的折叠路径。

T 的 0.119 绝对误差 × 2500 ≈ 296 个周期计数，与 `pwm_tbprd_max` 一致。

### INT4（两种结构相同）

| 集合 | max abs `[D1,D0,D2,T]` | 最大 PWM | 非法输出 | 最差 Vin |
|---|---|---:|---:|---:|
| 校准 1 V | [0.682, 0.301, 0.298, 0.332] | 1701 | 5（90–94 V） | 135.0 V |
| 官方 0.1 V | 同量级 | **1730** | 50 | 134.8 V |
| 92.2–92.5 V | — | 542 | 31（整段） | 92.2 V |

INT4 在合法工作域产生非法控制量，不能用于闭环。

浮点 ReLU 前激活存在负值（ReLU 有效）。三层 ReLU 后峰值约 0.52 / 0.73 / 0.71，削峰主要来自后续 INT8 激活量化，而不是 float ReLU 饱和。

---

## 6. 四层硬件卸载与 CPU fallback

### 零神经元 + FORCE_HW（唯一真正的四层硬件 FC）

`int8_zero_neuron_force_hw` 与 `int4_zero_neuron_force_hw`：

- 日志 **FC [X] × 4**，且生成 `tvmgen_default_ti_npu_fullyConnectedNHWC_{0..3}`
- INT8 INS：`FC_iB8_oB8_kB8_iCm8b16_oCm4_INS`、`..._oC1LL_INS`（29 输出拆出 1 通道块）
- INT4 INS：`FC_iB8_oB8_kB4_iCm8_oCm4_INS`、`..._oC2L_INS`
- `tinie_curr_layer += 1` 共 4 次；INT8 的 16→29 层 `tinie_num_sublayers = 2`
- **nn.relu × 3 全部 CPU**；每层前后还有 dequant / requant（add/mul/floor/clip/cast）
- 无 host post-process
- ABI：`float32 [1,16] → [1,4]` 或 INT4 的 `[1,8] → [1,4]`，二维 NC，不是 PWCONV 的 NHWC 4D
- 无 Conv / PWCONV 符号，MatMul 计算图被保留

### C28 默认（量产路径）

`int8_zero_neuron_default`：日志同样 `FC [X] × 4`，头文件仍有 `TVMGEN_DEFAULT_TI_NPU`、没有 `TI_NPU_SOFT`，但生成的是 **4 次 `TINIE_fullyConnected(` 软件库调用**，无 `FC_*_INS`，无 `tinie_curr_layer += 1`。这就是宏和日志不能当硬件证据的实例。

### 显式 Pad 方案

`int8_input_pad`（默认和 FORCE_HW）以及 `int4_input_pad`：`qnn.dense` 全部 `[ ]`，无 NHWC、无 INS、无 layer++。Pad 本身也在 CPU。四层 FC **没有** 卸载到 NPU。

---

## 7. 参数、指令规模与运行时开销

| 产物 | lib2.c | mod.a | 硬件层 | 额外 sublayer |
|---|---:|---:|---:|---|
| 现网 PWCONV | 13726 B | 252070 B | 4 PWCONV | 无（每层 1） |
| INT8 FC 零神经元 FORCE_HW | 14047 B | 261472 B | 4 FC | 16→29 拆 2 段 |
| INT4 FC 零神经元 FORCE_HW | 11625 B | 267642 B | 4 FC | 末层拆 2 段 |
| INT8 FC 零神经元 默认软件 | 8951 B | 243512 B | 0 | 软件库 4 次调用 |

硬件 FC 运行时与现网 PWCONV 同类：

1. 每层覆盖装载 PARAMS / MMR / INS
2. `TINIE_setup` + `TINIE_start` + ISR 推进 `tinie_curr_layer`
3. 层间回到 CPU 做 ReLU 和重量化，再启动下一层
4. 原始 29、12、6 不是 4 的倍数时，还会多 1 个 1/2 通道微码块

因此，即便内部开关打开、四层都进了 NPU，也不保证比 PWCONV 更快。软件默认路径没有 NPU 装载，但是 C28 上的库实现，不是阵列。

---

## 8. 与现有 PWCONV 对照

| 项目 | 原始 FPU | INT8 FC 零神经元 | INT4 FC 零神经元 | 现网 PWCONV |
|---|---|---|---|---|
| 结构 | 3-29-12-6-4 | 16-29-16-16-4 | 8-29-12-8-4 | 4-32-12-8-4 |
| MAC | 531 | 1248 | 708 | 640 |
| 算子 | FPU GEMM | MatMul/FC | MatMul/FC | 1×1 PWCONV |
| C28 默认卸载 | CPU FPU | 软件 FC 库 | （同左，未单编默认） | 硬件 PWCONV |
| 硬件卸载条件 | — | 内部 FORCE 开关 | 内部 FORCE 开关 | 正式 `ti-npu` |
| 官方网格最大 PWM | 0 | 335 | 1730 | ≈122 |
| 官方网格非法输出 | 0 | 0 | 50 | 92.2–92.5 V 有非法点 |
| 输入合同 | 三特征 | 三特征+零填充 | 三特征+零填充 | 折叠 Vin 通道 |

FC 没有减少计算量：INT8 零神经元 MAC 约是原始网络的 2.3 倍、现网 PWCONV 的 1.95 倍。INT4 零神经元 MAC 接近 PWCONV，但精度不可用，且硬件仍依赖内部开关。

---

## 9. 是否进入下一轮实机性能测试

**不进入。** 本轮两条硬门槛是：FC 按预期做 NPU 硬件映射，以及保持原始 3-29-12-6-4 的数学功能。

| 门槛 | 结果 |
|---|---|
| FP32 与原始网络一致 | 通过（误差为 0） |
| 量产 C28 上四层硬件 FC | **失败**（默认是软件库，宏会误报） |
| 仅内部开关下四层硬件 FC | 通过（仅零神经元方案；Pad 方案失败） |
| 量化后 1 个 PWM 计数 | **失败**（INT8 335；INT4 1730 且有非法输出） |

因此不满足“同时证明硬件映射可用于正式部署、且控制精度可接受”。内部 `FORCE_NO_TI_C28_SOFT_OFFLOAD` 不能作为固件策略；Pad 适配进不了 FC 模式；零神经元适配能进硬件，但 ISR/sublayer/CPU ReLU 仍在，INT8 误差比现网 PWCONV 更大。

下一轮若只做延迟微基准，也需要 TI 书面确认该开关可用于 F28P550，并且明确那是研究测量而不是控制闭环。本轮不烧板、不改正式库。

---

## 附录：隔离与复现

- 脚本：`model/experiments/fc/run_fc_campaign.py`、`compile_fc_npu.py`
- ONNX：`model/experiments/fc/onnx/`
- NNC 生成：`model/experiments/fc/generated/`
- JSON：`model/experiments/fc/results/`
- 量化环境：`review_20261003/npu_integration_20261009/narrow_quant_env`（torch + tinyml 1.5.0）
- 编译环境：同目录 `nnc211_env/python.exe`（`ti_mcu_nnc==2.1.1`）
- 未新增 CCS 配置，避免改写 `CPU1_LAUNCHXL_FLASH` / `CPU1_LAUNCHXL_NPU_FLASH`
