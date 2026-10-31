# A4 已验证实验包

优先使用 ../../work/A4/dab_control_f28p550/ 的完整隔离工程。

本目录未安装到交付工程；acceptance.json 关联逐层实机检查及三轮正式性能。

输入为 GS RAM 中 16 单元对齐的 uint16_t[8] packed INT8，输出为 float32[4]。必须配套 dab_nn.stage_a.c、fc_stage_a_input.h 和本目录头文件使用，不能仅将 mod.a 换到 float 输入工程。
