from pathlib import Path
app=Path(__file__).resolve().parents[2]/"dab_control_f28p550"
p=app/"docs/NN_timing_guide_zh.md"
s=p.read_text(encoding="utf-8")
a=s.index("当前已支持 FPU")
b=s.index("\n\n计时使用",a)
s=s[:a]+"已支持 FPU 和真实 DAB NPU 的板上计时及待机有限次数测试。NPU 使用新配置 `CPU1_LAUNCHXL_NPU_FLASH`，真实模型库与输入适配已接入；实际硬件耗时与加速倍数仍待开发板测量，操作和六组期望输出见 [NPU 接入说明](NPU_integration_guide_zh.md)。"+s[b:]
a=s.index("## 5. NPU 接入后怎样测")
b=s.index("## 6.",a)
s=s[:a]+'''## 5. 已接入的 NPU 怎样测

选择 `CPU1_LAUNCHXL_NPU_FLASH`，完整 Build、加载并从初始化运行；该配置输入为 16 项 FLOAT32，内部使用四层 NPU，输出为四项 FLOAT32。模型库会在最终输出还原之后、发布完成标志之前调用 `DAB_NN_noteNpuCompletion()`，因此 `npuCompletion` 已有真实完成路径的时间点；具体步骤见 [NPU 接入说明](NPU_integration_guide_zh.md)。

该配置固定用于候选模型核对和计时，功率启动拒绝码为 7，板确认宏不能绕过。输入只接受 Vin 90～140 V；优先使用说明文档中的 90、100、110、120、130、140 V 六组值，92.2～92.5 V 已发现输出越界，现有检查会拒绝并锁定故障，不能放宽保护来收集成功耗时。

先核对 `g_nnLastOutput` 与候选 ONNX，再保存完整 `g_nnTiming`。`npuCompletion` 含运行库、NPU、层间 CPU 处理和完成中断响应；`npuSubmit` 仅为启动调用，不能代表完整前向耗时。

'''+s[b:]
s=s.replace("准备原网络的三项归一化输入", "准备所选模型输入（FPU 三项、NPU 16 项）")
s=s.replace("不包含 ADC 采样和滤波；未来手工量化应在该准备区间内完成", "不包含 ADC 采样和滤波；NPU 运行库内部量化属于运行时间")
s=s.replace("未接入钩子时 `samples=0`；仍含提交和完成中断响应，不是裸硬件运算周期", "DAB16 库已接入最终输出时间戳；含提交、层间 CPU 处理和中断响应，不是裸 NPU 周期")
s=s.replace("只是启动调用耗时，不能作为 NPU 完成时间", "包含输入量化、打包和首层启动，不能作为 NPU 完成时间")
p.write_text(s,encoding="utf-8")
p=app/"docs/DAB_F28P550_guide_zh.md"
s=p.read_text(encoding="utf-8")
s=s.replace("5=保护未允许。请求", "5=保护未允许，6=NN 测试中，7=NPU 候选模型未批准功率控制。请求")
s=s.replace("| `tvmgen_default.h` | 当前缺失 | 必须由真实 DAB 模型生成 |", "| `generated/npu/tvmgen_default.h` | TI NNC 2.1.0 真实生成，输入 16 项 FLOAT32 | 已接入专用配置，待实板核对 |")
s=s.replace("| `mod.a` | 当前缺失 | 必须是对应 DAB 模型的 TI NPU 库 |", "| `generated/npu/mod.a` | DAB16 模型库，四层矩阵运算使用 NPU | 已编译链接；仅核对/计时，禁止功率启动 |")
a=s.index("### 9.4")
b=s.index("## 10.",a)
s=s[:a]+'''### 9.4 已接入真实 NPU，功率控制仍待精度验收

`CPU1_LAUNCHXL_NPU_FLASH` 已加入真实 DAB 模型库、16 项输入适配、GS1 工作区和最终完成计时。仅 `features[1]=Vin/25-4.6`，其余为零；输出仍为 `[D1,D0,D2,T]`。旧三输入接口的 `DAB_NPU_FLOAT_IO_CONFIRMED` 不适用于这个模型。

TI NNC 对原候选 `MatMul` 图会回退到 CPU，现已等价改写为四层 1×1 Conv；501 点转换前后输出一致，生成代码与最终链接确认四个 NPU 阶段。原 FLOAT 基准与 INT8 候选仍有最大约 0.049 的输出误差，92.2～92.5 V 部分点还不满足已有输出范围检查，因此该配置强制禁止功率启动（拒绝码 7），不能只改板确认宏绕过。

开发板操作、六组期望输出、完成时间含义、重建命令和剩余验收见 [NPU 接入说明](NPU_integration_guide_zh.md)。实际硬件输出和耗时尚待开发板核对；电脑接口替身只验证调用与保护逻辑。

'''+s[b:]
s=s.replace("真实 NPU 库接入前不能给出硬件速度", "真实 NPU 库已接入独立配置，板上速度仍待测量")
s=s.replace("未来真实 NPU 工作区仍必须按真实模型重新检查", "新增 DAB16 NPU 构建已确认 GS1 工作区容量，换模型后仍需重新检查")
s=s.replace("| DAB NPU 生成产物 | 当前只有 FLOAT 基准 | 编译真实 NPU 分支和工作区安排 |", "| DAB NPU 生成产物 | 真实库已生成且编译链接 | 待板上数值/计时核对和精度改进，禁止功率启动 |")
s=s.replace("真实 NPU 接入属于 B13 和训练资料工作", "真实 NPU 的板上核对与功率控制验收属于 B13 和训练资料工作")
p.write_text(s,encoding="utf-8")
p=app/"docs/NN_timing_CCS_watch.txt"
s=p.read_text(encoding="utf-8")
if "g_nnLastOutput" not in s: s += "g_nnLastOutput\n"
p.write_text(s,encoding="utf-8")
(app/"model/README.md").write_text('''# DAB 模型与 TI NPU 产物

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
''',encoding="utf-8")
