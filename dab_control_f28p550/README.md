# F28P550 DAB 控制程序

原配置使用 FPU 神经网络基准与 NN 开环，实际启动条件以当前板配置和请求为准。新增 `CPU1_LAUNCHXL_NPU_FLASH`，已加入真实 DAB NPU 库、16 项输入适配和完成计时；候选模型精度尚不足，该配置强制禁止功率启动，仅用于数值核对和计时。

详细阅读入口：

- [离线说明文档：目录、图示、查找和打印](docs/DAB_F28P550_guide_zh.html)
- [Markdown 原稿](docs/DAB_F28P550_guide_zh.md)
- [NPU 接入与开发板核对：配置、期望输出、计时和剩余验收](docs/NPU_integration_guide_zh.html)
- [NN 耗时统计与对比](docs/NN_timing_guide_zh.html)
- [模型文件与生成产物](model/README.md)
- [NPU 接入软件验证结果](../review_20261003/npu_integration_20261009/verification.json)
- [最新软件验证结果](../review_20261003/checks_site2_pin_cluster_20261008/verification.json)

建议先读说明文档第 1～8 节认识项目与功能，再按第 12 节使用 CCS，第 15 节记录硬件验收。开发板已确认为 LAUNCHXL-F28P55X（TMS320F28P550SJ9，100PZ）；四个构建配置和默认 XDS110 调试目标已一致。八路 PWM 已集中至 J8 第3～10针，四路 ADC 集中至 J7 第3～6针，故障/测时在 J6 第5/4针，全部在 Site2；保留默认两线 cJTAG 和未安装的 R44/R45，PWM 不再依赖 S4，完整接线表见第 5.1 节；外接功率板仍须单独验收。

2026-10-08 的 LaunchPad 引脚集中分配、模拟/数字模式及 LED 配置已通过实际 CPU1_RAM 构建、四组 TI 编译/链接、实际应用的模拟外设回归测试、121 组原网络对照和五万次滚动滤波检查。运行验证需本机 TI/MSVC 环境，入口为 `review_20261003/verify_site2_pin_cluster_20261008.py`；它不连接或烧写开发板，电脑测试不能证明电气性能和真实 NPU 精度。

旧报告和脚本反映修正前版本，当前软件问题状态及剩余任务以最新说明文档为准。修改前文件保存在 `review_20261003/before_pin_cluster_20261008`，未覆盖三个参考例程和 F28335 原程序。
