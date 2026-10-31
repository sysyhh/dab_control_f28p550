# A4 Stage B 实验包

本包未覆盖正式工程；优先使用 ../../work/A4/dab_control_f28p550/ 的完整隔离工程。

输入 ABI 为 GS RAM 中 16 单元对齐的 uint16_t[8] packed INT8，输出 float32[4]；必须配套应用源码、fc_stage_a_input.h、stage_b_delay.h 及生成头文件，不能只替换 mod.a。

stage_b_delay.h 只控制有限测试预热后的启动延迟，计时样本不包含这段等待；功率输出保持关闭。
