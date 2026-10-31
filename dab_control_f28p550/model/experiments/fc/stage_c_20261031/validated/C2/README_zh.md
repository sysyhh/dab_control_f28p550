# C2 Stage C 独立实验包

此包已通过570点四层原始输出、float32位模式及三轮普通固件计时。完整统计见 [验收](acceptance.json) 与 [总报告](../../REPORT_zh.md)。

仅适用于冻结B1网络；需要配套lib0/1/2.c、dab_tinie_c28.c、tvmgen_default.h、dab_npu_contract.h、fc_stage_a_input.h及应用dab_nn.stage_c.c。C2/C5还需匹配的tinie_mem_write_fast.asm；mod.a为这些文件同一编译条件的普通版本，detail-profile=0。

输入ABI：GS RAM中16单元对齐uint16_t[8] packed INT8，输出float32[4]；沿用Stage B的96单元workspace和原RAM分区。stage_b_delay.h只用于有限测试预热后的启动延迟，不计入正式样本。完整隔离工程可由run_stage_c.py prepare --variant C2再生，保留于work/C2/dab_control_f28p550/。

原始B1回退包位于../../../stage_b_20261031/validated/B1/；当前包没有覆盖正式工程或改变功率启动逻辑，四路OST必须保持锁定。此包是实验交付，不能只替换一个库文件到不同模型工程。
