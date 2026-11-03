# DAB Converter Control Firmware on TMS320F28P550SJ9

基于 TI C2000 **TMS320F28P550SJ9** 的双有源桥（Dual Active Bridge, DAB）DC-DC 变换器数字控制与片上神经网络（FPU / TINIE 硬件 NPU）推理框架。

---

## 1. 工程架构与模块划分

本工程采用中断实时控制环与主循环后台推理分离的双层架构：

- **100 kHz 实时控制中断 (`epwm7_isr`)**：
  - 由 EPWM7 周期事件触发 ADC 同步采样，并在采样转换完成后进入控制中断；
  - 执行 ADC 采样换算与故障保护边界检查 (`dab_adc.c`, `dab_protect.c`)；
  - 从神经网络双缓冲结果区无锁读取最近一次完整有效的相移与周期比参数 `[D1, D0, D2, T]` (`DAB_NN_getOutput`)；
  - 结合输出电压 PI 闭环调节量计算四桥臂开关时刻，并在全局单次同步装载（Global One-Shot Load）保护下更新 EPWM7 / EPWM4 / EPWM5 / EPWM10 (`dab_control.c`, `dab_pwm.c`)。
- **主循环后台服务 (`main`)**：
  - 负责神经网络前向推理调度与超时监控 (`DAB_NN_service`, `DAB_NN_checkDeadline`)；
  - 支持可选的片上推理耗时基准压测状态机 (`DAB_NN_benchmarkService`)；
  - 负责 SCI 串口遥测帧打包发送 (`DAB_Telemetry_service`) 与心跳指示。

### 核心源文件说明

| 文件 | 职责说明 |
|---|---|
| `dab_main.c` | 系统初始化、外设启动顺序、主循环调度与 100 kHz 控制 ISR 入口 |
| `dab_board_config.h` | 板级引脚映射、EPWM 通道分配、功率级电气参数与安全门控开关 |
| `dab_types.h` | 全局数据结构、枚举状态定义与跨模块外部接口声明 |
| `dab_math.h` | 轻量级内联数学工具与神经网络输出合法性校验 |
| `dab_adc.c` | ADC 硬件 SOC 配置、采样均值计算與连续就绪判定 |
| `dab_pwm.c` | 四桥臂 EPWM 同步相位/死区配置、Global Load 原子装载与硬件 Trip 锁存 |
| `dab_control.c` | 状态机（待机 / 软起动 / 闭环运行 / 故障）与 PI + 神经网络混合调制映射 |
| `dab_protect.c` | 过流/过压软件比较、CMPSS + EPWM X-BAR 硬件保护与故障锁存恢复 |
| `dab_nn.h` / `dab_nn.c` | 双模神经网络推理接口（FPU 软件前向 & 片上硬件 NPU 异步调度）及耗时统计状态机 |
| `dab_npu_trace.h` | 硬件 NPU 分段计时钩子与槽位定义 |
| `dab_telemetry.c` | 非阻塞式 SCI 状态遥测输出 |
| `model/generated/fc_int8/` & `fc_int4/` | 原生三维输入全连接（FC）NPU 模型的 C 接口契约与 C28 TINIE 运行时适配驱动 |

---

## 2. 神经网络推理配置与自定义模型接入

为了保护具体实验模型参数，开源仓库中的神经网络部分采用**脱敏占位配置**，开发者可按以下方式接入自训练模型：

### 2.1 FPU 软件推理模式（默认）

在 `dab_nn.h` 与 `dab_nn.c` 中，默认提供 `3 -> 8 -> 8 -> 4` 的示例全连接网络维度与安全标称占位参数：
- **网络维度宏**（`dab_nn.h`）：
  `DAB_NN_INPUT_DIM` (3)、`DAB_NN_LAYER1_OUT` (8)、`DAB_NN_LAYER2_OUT` (8)、`DAB_NN_OUTPUT_DIM` (4)。
- **输入特征归一化宏**（`dab_nn.h`）：
  `DAB_NN_INPUT0_CONST`、`DAB_NN_VIN_NORM_SCALE`、`DAB_NN_INPUT2_CONST`。
- **权重与偏置数组**（`dab_nn.c`）：
  `s_w1`, `s_b1`, `s_w2`, `s_b2`, `s_w3`, `s_b3`。默认权重全为 `0.0f`，输出层偏置 `s_b3` 设为安全标称值 `{1.0f, 0.0f, 1.0f, 1.0f}`（对应 `D1=1, D0=0, D2=1, T=1`）。
- **替换为自有模型**：根据训练导出的网络层数与神经元维度修改 `dab_nn.h` 中的维度宏及归一化常数，并将导出的浮点权重填入 `dab_nn.c` 即可。

### 2.2 片上硬件 NPU 模式（FC INT8 / INT4）

F28P550 内置 TINIE 硬件 NPU。本工程提供原生三维输入全连接（FC）NPU 模型的完整运行时接入框架：
- 仓库保留了 NPU 接口头文件與底层驱动源码：
  - `model/generated/fc_int8/dab_npu_contract.h`、`tvmgen_default.h`、`dab_tinie_c28.c`
  - `model/generated/fc_int4/dab_npu_contract.h`、`tvmgen_default.h`、`dab_tinie_c28.c`
- **接入编译后的 NPU 模型库**：
  1. 使用 TI MCU Neural Network Compiler (`ti-mcu-nnc`) 将训练好的 ONNX 模型编译为目标静态库 `mod.a`（或生成的 `lib0.c` / `lib1.c` / `lib2.c`）；
  2. 将生成的 `mod.a` 放置于 `model/generated/fc_int8/mod.a`（或 `fc_int4/mod.a`）；
  3. 在 CCS 构建配置中选择 `CPU1_LAUNCHXL_NPU_FLASH`（或定义 `DAB_USE_HARDWARE_NPU` 与 `DAB_NPU_FC_INT8` / `DAB_NPU_FC_INT4`）进行编译链接。

---

## 3. 构建配置与安全默认项

工程包含以下主要 CCS 构建配置：
1. `CPU1_RAM`：RAM 调试配置（使用 `28p55x_generic_ram_lnk.cmd`），适合快速仿真与基础功能验证。
2. `CPU1_LAUNCHXL_FLASH`：Flash 独立运行配置（使用 `28p55x_generic_flash_lnk.cmd`），启用 FPU 推理并将关键控制/推理函数搬移至 `.TI.ramfunc` 零等待 RAM 执行。
3. `CPU1_LAUNCHXL_NPU_FLASH`：启用片上硬件 NPU（`DAB_USE_HARDWARE_NPU` + `DAB_NPU_FC_INT8`）的 Flash 构建配置。

### 安全门控说明
- 默认 `DAB_AUTO_START = 0`：上电后保持 `DAB_STATE_STANDBY`，所有功率 EPWM 均由 Trip Zone 单次关断锁存（OST）强制拉低，不会自动发波。
- 默认 `DAB_BOARD_CONFIG_CONFIRMED = 0`（Flash 配置）：在未确认功率板硬件接线、CMPSS 保护极性与死区参数前，调用 `DAB_Control_start()` 会被安全拦截并记录拒绝原因 `g_startRejectReason = 1`。

---

## 4. 实板自动调试与耗时压测工具

仓库根目录提供了基于 CCS Scripting 的命令行自动化实板调试工具 `c2000_debug.py` 及 `tools/c2000_debug/` 组件，支持无人工干预的编译、下载、运行快照读取与 1000 次片上推理耗时压测。详细使用方法参见 [tools/c2000_debug/README.md](../tools/c2000_debug/README.md)。
