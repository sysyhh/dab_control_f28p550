"""Write Chinese reports only from replay-verified board evidence."""
from common_c import *
import statistics


def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(x) for x in row)+' |\n' for row in rows)


def main():
    d=json.loads((HERE/'results/final_verification.json').read_text());assert d['ok']
    t=json.loads((HERE/'results/transfer_analysis.json').read_text());assert t['ok']
    m=json.loads((HERE/'results/mmr_data.json').read_text());best=d['best'];variants=d['variants']
    names={'C1A':'B1 完整 MMR 对照','C1B':'NNC 原生压缩 MMR','C2':'仅精简参数复制','C4':'仅固定 MMR 直接写入','C5':'固定 MMR + 精简参数复制'}
    perf=table(['版本','内容','平均 μs','最小 μs','P95 μs','P99 μs','最大 μs','相对 C1A 降低'],[
        [v,names[v],*[f'{d["formal"][v]["pooled"][k]:.6f}' for k in ('mean_us','min_us','p95_us','p99_us','max_us')],f'{d["mean_reduction_percent"][v]:.3f}%'] for v in variants])
    rounds=table(['版本','轮次','启动延迟 μs','平均 μs','最小 μs','P95 μs','P99 μs','最大 μs'],[
        [v,r['round'],r['delay_requested_us'],*[f'{r[k]:.6f}' for k in ('mean_us','min_us','p95_us','p99_us','max_us')]] for v in variants for r in d['formal'][v]['rows']])
    ordinary=table(['版本','CPU 前台 μs','NPU ISR 累计 μs','提交 μs','提交到完成 μs','准备 μs','发布 μs','NPU 中断/次'],[
      [v,*[f'{statistics.mean(r[k] for r in d["formal"][v]["rows"]):.6f}' for k in ('cpu_foreground_us','npu_isr_us','submit_us','completion_us','prepare_us','publish_us')],4] for v in variants])
    stages=table(['版本','插桩版端到端 μs','参数装载 μs','MMR 配置 μs','指令阶段 μs','输入处理 μs','输出恢复 μs'],[
      [v,f'{d["detail"][v]["pooled"]["mean_us"]:.6f}',*[f'{d["detail"][v]["stage_means_us"][k]:.6f}' for k in ('parameters','registers','instructions','input','output')]] for v in variants])
    mmr_table=table(['FC 层','完整 uint32 数 / 逻辑字节','压缩 uint32 数 / 逻辑字节','完整寄存器写入','压缩/直接写入','参数 uint32 数'],[
      [i,'33 / 132','6 / 24',30,13,t['parameter_uint32_counts'][i]] for i in range(4)])
    loads=table(['参数源','uint32 数','原循环 → RAM 周期','精简循环 → RAM 周期','原循环 → PARAMS 周期','精简循环 → PARAMS 周期'],[
      [s,n,*[next(x['baseline_min_ticks'] if candidate==0 else x['candidate_min_ticks'] for x in t['rows'] if x['source']==s and x['target']==target and x['uint32_count']==n) for target,candidate in [('GS0',0),('GS0',1),('NPU_PARAMS',0),('NPU_PARAMS',1)]]] for s in ('LS3','GS1') for n in t['parameter_uint32_counts']])
    audit='''# NNC 2.1.1 MMR 源码审计

审计材料为 [common_mmr_defs.py](evidence/nnc211/common_mmr_defs.py)、[gen_mmr_fc.py](evidence/nnc211/gen_mmr_fc.py)、[config_fc.py](evidence/nnc211/config_fc.py)、[common_utils.py](evidence/nnc211/common_utils.py)。未修改 NNC 安装目录。

## 编码与运行条件

完整表为 33 个 uint32，索引 0..32 对应 CTL5..MMR3。压缩表以两个 uint32 位图开头，第一张表示后续 32 位值，第二张表示后续 8 位值；位 b 指向寄存器 b+1，因此 CTL5 不编码。先按寄存器升序保存所有大于 255 的值，再按升序将其余值每四个从最低 8 位开始装入一个 uint32；末尾不足四项补齐存储槽。压缩总长度不小于 33 时回退完整表，运行时以 num_mmrs 区分格式。

`MMR.__setitem__()` 标记 is_set。`tofile()` 仅编码 is_set 字段；如果 prev_mmr 曾显式设置该字段、字段属于前一层 constant_defs 且值相同，则进一步省略。constant_defs 表示前一段微码执行后值保持不变的字段，不表示所有地址寄存器都能缓存。FC 的附加清单为 ARout1(18)、ARt5(24)，默认含 CTL4..CTL0、LC0..LC5、MMR0..MMR3；PC(12)、ARwt0(21)、ARbias0(25)、ARss0(27) 不在清单中，必须重新建立。

实际 B1 每个 FC 只有一个子层，NNC 的 prev_mmr 只在同一 FC 的子层循环中传递，每个 FC 入口重新为 None。本次四层都没有跨 FC 的 prev_mmr 差分复用；host 中的 delta_demo 仅证明编码规则，没有应用到固件。

## 实际写入清单

四层 NNC 显式字段均为 `{3,5,8,9,12,18,21,24,25,27}`：CTL2、CTL0、LC2、LC3、PC、ARout1、ARwt0、ARt5、ARbias0、ARss0。随后原驱动按原始公式动态更新 CTL1(4)、MMR0(29)、MMR1(30)。没有 residual fmap。完整路径另写 `{6,7,10,11,13,14,15,16,17,19,20,22,23,26,28,31,32}`，原生压缩路径省略它们；剩余控制字段原路径本来也不写。

这些省略项不是因为本次与上一层恰好相同，而是当前 FC 指令不依赖其入口值，或会在使用前建立临时值；这是 NNC 自身 is_set 契约。本实验没有把它扩展到其他微码、残差网络或其他模型。START 和 ACK 仍走原驱动，未计入下表的配置写入数。

'''+mmr_table+'''
合计完整表 528、压缩表 96 个逻辑 8 位字节，节省 432 字节（81.82%）；对应 C28 的 16 位地址单元为 264 → 48。配置写入总数 120 → 52，减少 68 次（56.67%），但原生解码变慢，不能据此推断时间收益。

## 连续执行与逐寄存器验证

[mmr_data.json](results/mmr_data.json) 保存全部完整/压缩原始数组。[mmr_host_verification.json](results/mmr_host_verification.json) 记录原生 encoder 重放、真实 C28 decoder 的主机 C 测试、1000 条有脏初值及层间破坏的四层链、两张位图最高位边界。真实板上在三个批次的第一个工作点分别截取每层配置前后全部 33 个寄存器，见 [mmr_board_snapshots.json](results/mmr_board_snapshots.json)。检查 13 个有效入口字段与完整版逐值相等，同时逐项检查每个未写字段的本次前后值确实保持。

**并未声称全部 33 个寄存器的原始值等于完整版**：完整版会将一些不使用的寄存器清零，省略版会保留历史值。正确性证明是有效入口字段相等、其余字段满足 NNC 的不依赖条件，加上连续四层实机逐位输出验证，不能把未用字段的脏值当作失败，也不能只用单层解码结果代替连续执行验证。

## 独立直接写入候选

[static_mmr.py](static_mmr.py) 保留 B1 的 33 项原表、权重和指令，只生成上述十项的直接寄存器赋值，再执行完全相同的三个动态地址公式。每个任务均重写全部有效入口字段，没有跨层相等比较或配置缓存；[static_mmr_host.json](results/static_mmr_host.json) 是实际候选 C 函数的 1000 条四层链验证。该候选仅适用于冻结的四层 B1，不作为通用 TINIE 驱动替代品。
'''
    (HERE/'MMR_AUDIT_zh.md').write_text(audit,encoding='utf-8')
    param='''# 参数装载汇编与传输效率审计

## 实际代码与存储位置

`TINIE_setup()` 的参数阶段调用当前工程编译进去的 `TINIE_mem_write(params,num_params,params_source)`。审计由接受的 B1 驱动源码重新以相同 cl2000 22.6.2.LTS、EABI、-O3、opt_for_speed=5、FPU32 生成汇编和 listing，未反推 C 代码代替汇编。见 [原始汇编](assembly/baseline/dab_tinie_c28.asm)、[listing](assembly/baseline/dab_tinie_c28.lst)、[编译命令与实机审计材料](assembly/audit/)。

链接 map 确认驱动运行于 LS2(0x9000)，参数运行于 LS3(0x9800 起)，Flash 是加载镜像，不是推理中的参数读取位置。全体普通版本 workspace=0xe000、packed input=0xe060，原有对齐和容量不变。参数源四个实际 C28 地址依次为 '''+', '.join(t['parameter_source_word_addresses'])+'''，每个 uint32 占两个 16 位地址单元；参数总数 208+168+104+26=506 个 uint32，即 2024 个逻辑 8 位字节。

SDK `tinie.h` 给出 base 0x54000、PARAMS offset 0x1800，即 CPU 地址 0x55800。NNC 容量常数 2048 个逻辑字节，对应 512 个 32 位有效数据、每项地址步长四个 C28 单元的窗口 0x55800..0x55fff。每个有效 MOVL 只写两个单元，跳过后两个单元；并非对连续 uint32 数组做 memcpy。首层208项的最后有效写起点为0x55b3c，未超过已知窗口。本轮只访问这个已有、已使用的 PARAMS 基址。

## 原始热循环

源 C 已手动四项展开，编译器再次展开为八项 RPTB：16 条 MOVL 负载/写入、4 条 MOVB 地址偏移设置、2 条 ADDB 目标推进，共 22 条发射指令/8 个 uint32（2.75 条/项）。源地址通过 *XAR5++ 每次推进两个 C28 单元，目标通过 0/4/8/12 偏移及每四项 +16 推进。没有发现多复制一份完整参数的情况。

重复 MOVB 可以移出 RPTB；短块入口有比较、分支、保存 XAR1 和恢复等固定成本，末层26项有两个尾项。四层长度都没有需额外四项剥离的情况。C2 的独立汇编 [tinie_mem_write_fast.asm](candidates/tinie_mem_write_fast.asm) 为四项九条指令（2.25 条/项），偏移只设置一次，保留 XAR1、EABI、RPTB、原始写入宽度和目标步长。只替换参数阶段的一处调用，原 TINIE_mem_write 仍用于指令和原始 MMR 路径。

主机解释实际候选汇编，覆盖 n=0..512、随机32位负载、读写地址轨迹、源区保护、所有目的空槽及保存寄存器，见 [parameter_candidate_admission.json](results/parameter_candidate_admission.json)。这不提供主机性能成绩；实际 EABI/循环与目标地址读回由下面的开发板实验验收。

## 独立实机传输实验

同一个函数分别从原参数 LS3、等值 GS1 读取，分别写 GS0、已知 NPU PARAMS。每个源/目标/层长128次；先 PWM 初始化并锁定 OST，保持全局中断屏蔽、NPU空闲，复制后逐项读回校验；之后恢复原有限1000次推理并检查四输出、超时和OST。没有启动功率输出。原始记录分别为 [baseline](results/transfer_audit_raw.json)、[candidate](results/transfer_fast/transfer_audit_raw.json)，下表为最小 CPU 周期，包含相同调用包裹和计时读数成本。

'''+loads+'''
原循环 RAM 目标线性段为 `77+2.75n`，NPU 目标为 `74+6n` 周期；精简循环 RAM 为 `54+2.25n`，NPU 为 `51+6n`，中间长度误差不超过1周期。LS3/GS1相同长度差不超过1周期，换参数源 RAM 没有可用收益。对相同函数只改变目标得到的是 NPU 目标通路的额外成本，尚不能进一步分解为桥接等待、目标接收与流水线重叠各占多少。

**关键归因：CPU 发射开销下降后，NPU PARAMS 稳态吞吐仍停在约6周期/32位项，节省的发射位置主要变成等待；可重复节省主要来自固定入口和尾项。** 不能把普通 RAM 的0.5周期/项收益直接按506项计入NPU收益。

## 下限与实测差距

在单发射负载+写入模型下，仅506次负载和506次写入的绝对软件发射下限为1012周期=6.746667 μs，忽略地址、循环、调用和目标停顿，不能作为可达到的硬件承诺。原热循环自身发射预算1391.5周期=9.276667 μs；精简循环为1138.5周期=7.590000 μs，同样不含目标等待。

在本板已测得的约6周期/项持续吞吐下，506项的纯流式预算为3036周期=20.240000 μs；四次调用与尾项的实测最小和分别为原始3335周期=22.233333 μs、候选3236周期=21.573333 μs，改善99周期=0.660000 μs。候选距离该“已观察吞吐预算”约1.333333 μs，原始约1.993333 μs；这给出合理效率判断，但不是未经公开时序规格证明的芯片绝对下限。

详细插桩参数阶段包含调用、分支、trace及其他中断影响，必须单独报告，不能与以上屏蔽中断的独立微实验或普通固件端到端数字相加减。实际 C28 桥接每次存储的强制时延未在本轮公开硬件资料中找到，不能把原始6周期斜率中的3.25周期简单当作每条store的固定额外等待。

## 官方依据与停止条件

指令、RPTB、EABI 的语义依据为 TI [C28 CPU 手册 SPRU430F](https://www.ti.com/lit/ug/spru430f/spru430f.pdf) 和 [扩展指令手册 SPRUHS1C](https://www.ti.com/lit/ug/spruhs1c/spruhs1c.pdf)。TI [存储操作优化说明](https://software-dl.ti.com/C2000/docs/optimization_guide/phase1/mem_operands.html) 解释 RAM 端口冲突的影响；本轮另以 LS3/GS1 对照检查，未将该说明泛化为 NPU 外设时序。

多层参数驻留沿用 [Stage B 证据](../stage_b_20261031/results/parameter_residency_audit.json)：容量本身可能够用，但未证明非零参数基址、微码预取范围与多任务寿命约定；当前 C28 驱动及 NNC 未提供已核实的驻留基址切换接口。本轮没有写未知地址或改微码，停止此实现路线。继续手写参数循环只有约固定入口余量，优先等待 TI 的正式目标通路时序/搬运与重定位接口证据。
'''
    (HERE/'PARAMETER_AUDIT_zh.md').write_text(param,encoding='utf-8')
    report=f'''# F28P550 FC-NPU Stage C 实机优化报告

日期：2026-10-31。原始 HEAD：`{json.loads((HERE/'provenance.json').read_text())['head']}`。

## 结论

本轮通过主机与开发板验收的最快实验版本为 **{best}，平均 {d['best_mean_us']:.6f} μs，相对同轮 B1 对照 {d['baseline_mean_us']:.6f} μs 降低 {d['best_reduction_percent']:.3f}%**。正式计时使用 detail-profile=0；详细插桩使用独立构建和数据，不混算。冻结 B1 结构16-32-16-16-4、有效权重、量化、四个硬件任务和指令不变，最终四输出原始位模式一致。

原生 `opt_for_space` 能显著节省数据空间，但实测增加耗时，故拒绝作为性能方案。独立固定 MMR 写入移除未使用字段的写入和压缩解码；精简参数复制主要减少固定开销，NPU目标通路的稳态吞吐没有提升。全部候选仍在实验目录中，未覆盖正式库；A/B已验收材料的受保护文件SHA256全部不变，四路OST始终锁定。

## 验收范围与实验矩阵

开始时建立可执行验收条件，记录在 [provenance.json](provenance.json)：原始材料逐字节保护；NNC实际编码与四层寄存器重放；真实C28解码主机验证；实际汇编和独立源/目标实机传输审计；每候选570点四层原始输出与最终float位模式；三轮独立普通/插桩构建、烧录、相位变化及1000样本；保留原始序列、镜像与SHA256。最终由 [verify_results_c.py](verify_results_c.py) 重放验收，结果 [final_verification.json](results/final_verification.json)。

{table(['版本','单项变化','判断'],[[v,names[v], '性能回退，保留反证' if v=='C1B' else '通过主机与实机正确性及三轮计时'] for v in variants])}
C3（原生压缩+精简复制）未运行：原生压缩已证实负收益，缺乏组合价值。C4、C5使用原始完整表，彼此以参数复制作为唯一差异，避免将不同因素混作一个实验。固定写入为B1专用生成补丁，不能单独部署成通用驱动。

## 原始执行流程与 MMR 审计

沿用Stage A整数输入与packed层间直连：输入准备 → 四次FC硬件任务（每次参数装载、指令阶段、MMR配置、START、原完成中断）→ 最终unpack与浮点输出恢复。指令地址/长度缓存机制完全保留，本轮没有修改中断调度、MMR未知字段、PARAMS基址或微码。

每个FC的MMR表原为33项，native压缩为6项，四层数据528→96逻辑字节，配置写入120→52次。`prev_mmr`在当前四个FC之间重置，因此不存在自动跨FC差分复用；省略依据是NNC显式字段清单。有效入口字段和动态地址在每次任务均重新建立，临时/未用寄存器允许保留历史值。完整编码格式、constant_defs规则、全部数组和连续状态证明见 [MMR_AUDIT_zh.md](MMR_AUDIT_zh.md)。

## 主机与实机正确性

原生encoder逐项重放与真实decoder主机C测试通过1000条脏初值四层链；直接写入候选另运行真实C函数相同验证；参数原循环边界、候选实际汇编轨迹覆盖n=0..512，检查地址步长、空槽、保护区、有效值和保存寄存器。候选参数函数另在实机屏蔽中断测试0及四个实际长度，并逐项读回。

所有{len(variants)}个测试版本分别通过570个实机工作点：501个Vin=90..140V/0.1V正式点、69个量化跳变点与相邻float32值。packed输入、四层全部有效中间输出及最终float32原始位模式与C1A逐项相等；C1A再与Stage B已验收B1记录相等。每批190点，固定四个任务，无超时、拒绝输出、功率启动；原始记录与逐层数据在 [capture/](results/capture/)。

三个批次分别获取每层配置前后33个寄存器；有效字段逐项等于完整版，未写字段逐项保持自己的前值，见 [mmr_board_snapshots.json](results/mmr_board_snapshots.json)。这里没有把未使用的全部原始寄存器误称为完全相同。

## 正式性能：detail-profile 关闭

LAUNCHXL-F28P55X，F28P550，SYSCLK=150MHz，Vin=90V，预热10次、正式1000次，三轮分别完整重建与烧录。启动延迟0/17/43μs置于预热后、正式计时前；镜像哈希与三条计时序列各自不同。沿用Stage B的起止点、packed缓冲地址与定时器，未减去插桩开销来制造普通固件成绩。

{perf}
表中总样本为每版本3000，分位数从合并后的原始序列计算，采用Stage B相同的排序索引规则。每轮完整数据如下，保留均值差异，不仅选择最快一轮。

{rounds}
三轮结果对启动延迟敏感，尤其C4第三轮较慢；这仍是有限相位实验，不等于所有异步中断相位的最坏情况上界。每版本的三轮平均值和尾部都完整保存，收益判断以整个普通固件实验为准。

{ordinary}
CPU前台按原框架等于 prepare+submit+publish 的计时和，ISR为四次NPU中断处理累计值；这些是框架定义的计时窗口，可能含其他中断影响，不能当作完整CPU利用率计数。completion从提交到观察完成，包含submit和NPU ISR，与其他列重叠，不能横向求和。每次推理四次NPU中断，正式每轮4000次，无任务数变化。

## 独立详细插桩

{stages}
详细版同样每版本三轮、每轮1000次，完整12项阶段和逐轮样本见 [detail_performance.csv](results/detail_performance.csv) 与各 summary.json。指令阶段包含原缓存判断和trace，不表示每层都实际重新加载微码。普通版的端到端收益不能用这些列相减重建；START后到完成的四个层等待窗口也包括中断调度和观察延迟，并非纯MAC时钟数。

C4参数复制源码完全不变，其参数阶段均值变化不能算作参数优化收益；同理，C5虽在详细版更快，普通版却慢于C4，不能用分项计时掩盖这一结果。C5没有作为最快方案采用；相位及计时窗口的影响已观察到，但现有数据不足以将组合反向变化的每一个周期精确归因，未追加未经证实的补偿修改。

## 参数装载审计及实际边界

实际B1参数共506个uint32，源LS3、代码LS2、目标PARAMS固定0x55800、32位MOVL、目标步长四个C28地址单元。原RPTB八项22条指令，独立候选四项九条。原循环普通RAM目标为2.75周期/项，候选为2.25；NPU目标两者均约6周期/项，LS3与GS1的差不超过1周期。

独立屏蔽中断的四次参数装载最小和原始22.233333μs、候选21.573333μs；按本板已观察6周期/项的纯流式预算20.240000μs，剩余主要是固定调用/尾项。绝对负载+写入发射下限6.746667μs不包含目标停顿，不能拿来承诺实际NPU传输性能。官方公开资料未提供足以证明该目标通路绝对最优的完整时序，结论限定为当前已验证方法接近所测吞吐边界。汇编、逐项地址与数据、原始128次序列、理论口径见 [PARAMETER_AUDIT_zh.md](PARAMETER_AUDIT_zh.md)。

## 取舍、剩余瓶颈与下一步

采用实验版本{best}作为本轮最快可回退包；B1仍保留为原验收基准。C4消除本模型未使用MMR字段的配置写入、通用格式判断和通用复制调用，也避免采用压缩解码；参数偏移设置与入口精简只属于C2/C5，未计入C4代码变化。四个FC任务数、参数总传输量、NPU执行及原中断机制均未改变。

参数装载仍占主要阶段，NPU目标通路约6周期/项是本轮实测稳定限制；下一层仍覆盖同一参数窗口。原生压缩路线停止，进一步只精简复制热循环也缺少较大收益证据。参数驻留所需非零基址重定位、预取范围和多任务寿命约定仍未证明，未做猜测寄存器实验。

下一阶段最值得做的一项工作是向TI取得C28 PARAMS通路的正式时序与支持的搬运/基址接口约定，再设计保持506项及地址语义不变的独立搬运实验。取得依据前，保留当前已验证实现；调度相位另应扩展覆盖以建立耗时上界，不能通过删减其他中断来获得本轮成绩。

## 交付与复现

本轮共{d['formal_runs']}轮普通固件、{d['formal_samples']}条正式原始计时，以及{d['detail_runs']}轮独立插桩固件、{d['detail_samples']}条详细测试计时。每轮镜像.out、map、来源manifest、构建/烧录/调试日志和1000项原始序列在 [results/benchmarks/](results/benchmarks/) 与 [results/debug_runs/](results/debug_runs/)；普通/详细CSV分开保存。[validated/](validated/)含各通过版本完整源码、匹配头文件及普通mod.a；[assembly/](assembly/)保存真实编译输出与传输审计镜像。不能把仅MMR生成原始包当成Stage A已优化运行库替换。

主机复验：`python verify_mmr_host.py`、`python verify_transfer_host.py`、`python parameter_candidate.py`、`python static_mmr.py`；原生NNC再生：`python generate_mmr.py`。实机重跑使用 `python validate_board_c.py --variant C5`（替换为目标版本），通过后 `python run_stage_c.py board --variant C5`、`python run_stage_c.py detail --variant C5`；参数独立实验为 `python transfer_audit.py` 和 `python transfer_audit.py --fast`，开发板操作必须串行执行。主机脚本复验原版时仅检查C1A/C1B，其他候选由各自独立记录及最终汇总验收。

最后运行 `python analyze_transfer.py`、`python verify_results_c.py`、`python write_report.py`、`python finalize_artifacts.py`。命令从本实验目录执行，依赖现有NNC 2.1.1环境、TI CCS/C2000工具链和已连接XDS110。源码、编译产物、逐层记录和计时证据的总清单见 [SHA256SUMS.json](SHA256SUMS.json)。
'''
    (HERE/'REPORT_zh.md').write_text(report,encoding='utf-8')
    print('Chinese Stage C report and audits updated from verified data')


if __name__=='__main__':main()
