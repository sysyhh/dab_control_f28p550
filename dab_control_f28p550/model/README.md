# DAB 模型与 TI NPU 产物

`generated/npu/mod.a` 和 `tvmgen_default.h` 已由 TI MCU NNC 2.1.0 实际生成并通过 C2000 FLASH 链接。新增 `CPU1_LAUNCHXL_NPU_FLASH` 用于数值核对和计时，默认 FPU 配置继续保留；当前 INT8 精度未通过功率控制验收，启动拒绝码为 7。

| 文件 | 内容 |
|---|---|
| `dab_float_baseline.onnx` | 原 3→29→12→6→4 FLOAT32 基准，输入 `[1,3]`、输出 `[1,4]` |
| `dab_npu_tinpu_ptq.onnx` | 原量化候选，输入 `[1,16]`、输出 `[1,1,1,4]`；直接编译存在 CPU 回退 |
| `dab_npu_tinpu_conv.onnx` | 等价 1×1 Conv 模型，四层计算分配到 NPU |
| `dab_npu_quantize_report.json` | 先前 51 个整数电压点的量化误差报告 |
| `dab_npu_conv_validation.json` | 501 点转换等价检查和更密集的 FLOAT 基准误差报告 |
| `generated/npu/manifest.json` | 编译工具版本、选项、维度、硬件阶段数及文件摘要 |
| `generated/npu/lib0.c`～`lib2.c` | 真实生成代码，保留供检查；CCS 只链接库，不重复编译这些文件 |
| `dab_model_manifest.json` | 原网络参数、归一化、输出顺序和摘要 |
| `validation_vectors_NOT_calibration.csv` | 121 个 Vin=20～140 V 回归向量，不是完整训练域或真实校准集 |

FPU 输入为 `[-0.5,Vin/140,0.285714]`。DAB16 NPU 输入为 16 项 FLOAT32，仅 `features[1]=Vin/25-4.6`，其余为零；两项常量已折入第一层。输出仍按 `[D1,D0,D2,T]` 排列，编译接口负责最终还原为 FLOAT32，不能重复反量化。

新配置通过 `DAB_USE_HARDWARE_NPU` 和 `DAB_NPU_DAB16_MODEL` 选择专用适配，不使用旧三输入接口的 `DAB_NPU_FLOAT_IO_CONFIRMED`。模型工作区在 GS1，超时仍为 1 ms，一次只允许一个任务；超时后不自动重试或复用未结束的缓冲区。

转换前后 501 点输出差为零，不能据此认为与原 FLOAT 模型精度相同。密集检查中最大输出误差约 0.049，且 92.2～92.5 V 部分输出不满足现有范围检查，因此禁止功率启动；实际 NPU 输出和耗时仍需开发板验证。

操作、期望输出、误差、重建命令和剩余验收见 [NPU 接入说明](../docs/NPU_integration_guide_zh.md)，计时字段见 [NN 计时说明](../docs/NN_timing_guide_zh.md)。
