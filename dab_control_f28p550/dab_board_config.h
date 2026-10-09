#ifndef DAB_BOARD_CONFIG_H_
#define DAB_BOARD_CONFIG_H_

// LAUNCHXL-F28P55X Site2：八路 PWM 在 J8，四路 ADC 在 J7，辅助信号在 J6。
// PWM 不再占用 GPIO4/5；使用默认两线 cJTAG，R44/R45 保持未安装，GPIO35/37 才可用于 PWM。
// 四桥臂逻辑顺序对应 EPWM7/4/5/10，独立采样与控制节拍改用 EPWM1。
// 外接功率板的驱动接线、采样前端阻抗和标定仍须人工确认。
#ifndef DAB_BOARD_CONFIG_CONFIRMED
#define DAB_BOARD_CONFIG_CONFIRMED 1 // 默认禁止输出；核对封装、原理图、采样与驱动接线后才能人工改为 1。
#endif
#ifndef DAB_AUTO_START
#define DAB_AUTO_START 0 // 默认不自动启动，使用新的人工启停请求。
#endif
#define DAB_DEBUG_GPIO 61U // J6 总54 / 本地4，控制代码段测时；不是整个中断的耗时。
#define DAB_DEBUG_PIN_CONFIG GPIO_61_GPIO61
#define DAB_HW_TRIP_GPIO 60U // J6 总55 / 本地5，外部低有效故障输入。
#define DAB_HW_TRIP_PIN_CONFIG GPIO_60_GPIO60
#define DAB_PWM_LEG1_BASE EPWM7_BASE // 第一桥臂是主计数器；逻辑编号不等于实际 ePWM 编号。
#define DAB_PWM_LEG2_BASE EPWM4_BASE
#define DAB_PWM_LEG3_BASE EPWM5_BASE
#define DAB_PWM_LEG4_BASE EPWM10_BASE
#define DAB_CTRL_EPWM_BASE EPWM1_BASE // 独立 10 kHz 节拍，不输出功率 PWM。
#define DAB_CTRL_ADC_TRIGGER ADC_TRIGGER_EPWM1_SOCA
#define DAB_PWM_MASTER_SYNC_SOURCE EPWM_SYNC_IN_PULSE_SRC_SYNCOUT_EPWM7
#define DAB_PWM_MASTER_LINK EPWM_LINK_WITH_EPWM_7
#define DAB_PWM_COMMIT_INTERRUPT INT_EPWM7
#define DAB_CONTROL_INTERRUPT INT_EPWM1
#define DAB_PWM_LEG1_RESET SYSCTL_PERIPH_RES_EPWM7
#define DAB_PWM_LEG2_RESET SYSCTL_PERIPH_RES_EPWM4
#define DAB_PWM_LEG3_RESET SYSCTL_PERIPH_RES_EPWM5
#define DAB_PWM_LEG4_RESET SYSCTL_PERIPH_RES_EPWM10
#define DAB_CTRL_EPWM_RESET SYSCTL_PERIPH_RES_EPWM1
#define DAB_PWM1A_GPIO 12U // J8 总80 / 本地10，EPWM7A，须设数字模式。
#define DAB_PWM1B_GPIO 13U // J8 总79 / 本地9，EPWM7B，须设数字模式。
#define DAB_PWM2A_GPIO 6U // J8 总78 / 本地8，EPWM4A。
#define DAB_PWM2B_GPIO 7U // J8 总77 / 本地7，EPWM4B。
#define DAB_PWM3A_GPIO 37U // J8 总76 / 本地6，EPWM5A，与 TDO 共脚，默认两线 cJTAG 可用。
#define DAB_PWM3B_GPIO 35U // J8 总75 / 本地5，EPWM5B，与 TDI 共脚。
#define DAB_PWM4A_GPIO 62U // J8 总74 / 本地4，EPWM10A。
#define DAB_PWM4B_GPIO 63U // J8 总73 / 本地3，EPWM10B。
#define DAB_PWM1A_CONFIG GPIO_12_EPWM7_A
#define DAB_PWM1B_CONFIG GPIO_13_EPWM7_B
#define DAB_PWM2A_CONFIG GPIO_6_EPWM4_A
#define DAB_PWM2B_CONFIG GPIO_7_EPWM4_B
#define DAB_PWM3A_CONFIG GPIO_37_EPWM5_A
#define DAB_PWM3B_CONFIG GPIO_35_EPWM5_B
#define DAB_PWM4A_CONFIG GPIO_62_EPWM10_A
#define DAB_PWM4B_CONFIG GPIO_63_EPWM10_B
// 原边为逻辑桥臂1/2，副边为3/4；相移计算含义保持不变。
#define DAB_VOUT_P_CHANNEL ADC_CH_ADCIN4 // ADCA SOC0：A4，J7 总66 / 本地6，100PZ MCU第36脚。
#define DAB_VOUT_N_CHANNEL ADC_CH_ADCIN5 // ADCA SOC1：A5，J7 总65 / 本地5，100PZ MCU第35脚。
#define DAB_IOUT_CHANNEL ADC_CH_ADCIN0 // ADCB SOC0：B0，J7 总63 / 本地3，MCU第41脚。
#define DAB_IL_CHANNEL ADC_CH_ADCIN1 // ADCB SOC1：B1，J7 总64 / 本地4，MCU第40脚。
#define DAB_VOUT_P_ANALOG_GPIO 225U // A4/B8 的 AIO225；显式保留模拟功能。
#define DAB_VOUT_N_ANALOG_GPIO 249U // 100PZ 的独立 A5/AIO249，不与 PGA2_INM 共脚。
#define DAB_IOUT_ANALOG_GPIO 253U // B0 的数字复用名；采样前显式接通模拟输入路径。
#define DAB_IL_ANALOG_GPIO 230U // B1/A10/C10 的数字复用名；此脚仅用于 ADC。

// Original F28335 coefficients are reference values, not a new-board calibration.
#define DAB_IL_SCALE 0.0168f // 电流换算为 scale×raw−offset，沿用旧板系数，须实板标定。
#define DAB_IL_OFFSET 37.314f
#define DAB_IOUT_SCALE 0.0168f
#define DAB_IOUT_OFFSET 37.314f
#define DAB_NOMINAL_VIN 90.0f // 固定 NN 输入电压假设，不能当作实测 Vin。
// Vin wiring/scaling is not known. Keep a clearly identified nominal-input mode.
#define DAB_HAS_VIN_SENSING 0 // 未接入真实 Vin；启用前必须新增 SOC、标定与保护逻辑。
#if DAB_HAS_VIN_SENSING
#error "Add the actual Vin SOC, channel and calibration before enabling Vin protection"
#endif

// Open loop matches the old program's final F_duty=0 override.
#define DAB_MODE_NN_OPEN_LOOP 0U
#define DAB_MODE_NN_CLOSED_LOOP 1U
#ifndef DAB_CONTROL_MODE
#define DAB_CONTROL_MODE DAB_MODE_NN_OPEN_LOOP // 0：保留 NN 开环；1：启用电压 PI，参数仍需实板调试。
#endif
#if DAB_CONTROL_MODE != DAB_MODE_NN_OPEN_LOOP && DAB_CONTROL_MODE != DAB_MODE_NN_CLOSED_LOOP
#error "Unsupported DAB_CONTROL_MODE"
#endif
#define DAB_NPU_TIMEOUT_US 1000U // 一次真实 NPU 运算最多等 1 ms，超时锁定且不自动重试。
#define DAB_NN_REFRESH_DELTA_V 0.1f // 相对上次推理输入变化达到 ±0.1 V 才刷新 NN 缓存。
#define DAB_ADC_READ_GUARD_COUNTS 150U // 读取结束前距下次 EPWM1 零点至少 150 计数，150 MHz 下约 1 μs。
#define DAB_PWM_COMMIT_GUARD_COUNTS 600U // 距主 PWM 零点超过 600 计数，名义 4 μs；还需测写入最坏时间。
#define DAB_PWM_STAGE_BUDGET_COUNTS 450U // 写入前额外预留 3 us；本次实测约 2.01 us，仍须验证全周期范围的最坏耗时。
#if (DAB_PWM_COMMIT_GUARD_COUNTS + DAB_PWM_STAGE_BUDGET_COUNTS) >= 1250U
#error "PWM entry reserve must be below the minimum supported TBPRD (1250)"
#endif
// Conservative software deadlines; validate the margin with the power board.
#define DAB_ADC_MAX_AGE_US 150U // 上次有效读取及运行控制节拍的保守期限，不是快速短路关断预算。
#define DAB_PWM_UPDATE_TIMEOUT_US 300U // 提交/装载总等待期限，覆盖新请求不得把起始时刻后移。
#define DAB_FAULT_RECOVERY_US 5000U // 正常恢复至少 5 ms，还要有效采样和人工清除；不会自动重启。
// Numeric tolerance preserves the small negative D2 in the FLOAT baseline.
// This is an interface sanity limit, not a certified training/safety domain.
#define DAB_NN_PHASE_TOLERANCE 0.005f // 相对 T 的 0.5% 浮点容差，不能替代训练范围或电气允许区域。
#define DAB_TELEMETRY_FRAME_TIMEOUT_US 20000U // 活动遥测帧堵塞 20 ms 后清 FIFO/队列，控制主循环不等待。
#ifndef DAB_ENABLE_WATCHDOG
#define DAB_ENABLE_WATCHDOG 1 // 默认启用进度监督；无输出调试可关闭，正式使用应恢复验证。
#endif

#endif
