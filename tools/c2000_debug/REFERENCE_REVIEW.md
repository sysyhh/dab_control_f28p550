# C2000 最小实机调试路线评估

核对日期：2026-10-09。依据两个参考仓库的当前源代码，以及 TI CCS 20.3 官方文档；这里只记录接口与设计判断，真实硬件是否通过以本地运行结果为准。

## 结论

推荐 `Codex → Python CLI → 本机 CCS Scripting → XDS110 → C2000`。Build 使用现有 CCS 工程的官方命令行，调试使用同一 CCS 安装提供的 API；一次命令内完成连接、加载、运行、暂停、取值和退出。无需先安装 MCP，也无需常驻服务器。这是针对当前单板需求的工程判断，最终需实机验证。

本机实施补充：安装记录实际为 CCS 20.4.1，已验证 `Python 标准库 CLI → CCS 自带 Node → 新版 CCS Scripting`；编译直接复用已存在的 CCS 生成 makefile，因此不需要新建或导入另一个 workspace。选择 JavaScript 调试文件是为了复用自带运行环境，避免额外安装 Python 的 `websockets` 依赖；这仍是官方新版 CCS Scripting，不是旧 DSS/Rhino。实际结果与使用边界见 [README.md](README.md) 和 [verification.json](verification.json)。

## 参考项目中值得保留的部分

| 来源 | 当前需求可借鉴 | 第一阶段不引入 |
|---|---|---|
| C2000_Multicore_Debug_MCP | `.ccxml` 定位目标、明确 CPU、API 调用、分阶段超时、结构化错误、读取真实运行状态、区分 mock 与硬件证据 | MCP、CPU1/CPU2 管理、daemon、RPC、SQLite、worker、lease、多板调度、PCAN、DLOG、ERAD、HIL SDK、学习/提案/PR 流程、安全档位 |
| C2000-IDEA | 官方器件资料、项目与器件信息、寄存器说明入口 | 为获得 run/halt 而安装整个扩展；其 IDEA MCP 的工具集中于迁移、工程信息与资料查询，不能代替 Debug Server |

前者当前源码实际使用旧 DSS/Rhino：启动 `ccs_base/scripting/bin/dss.bat`，导入 Java 包，并通过 `ScriptingEnvironment.instance()` 创建 `DebugServer.1`。`CcsScriptingAdapter` 这个类名不能证明使用新版 CCS Scripting。其 README 也明确多项能力只有 Mock 验证，不能把项目声明当成本机硬件证据。[README](https://github.com/gjjisadog/C2000_Multicore_Debug_MCP/blob/master/README.md)、[DSS bridge 源码](https://github.com/gjjisadog/C2000_Multicore_Debug_MCP/blob/master/src/adapters/CcsScriptingBridge.ts)、[persistent bridge 源码](https://github.com/gjjisadog/C2000_Multicore_Debug_MCP/blob/master/src/adapters/PersistentDssBridge.ts)。

C2000-IDEA 当前 README 与 IDEA MCP 实际工具注册表中包含器件迁移、bitfield 转 driverlib、工程信息和文档查询；它是辅助开发工具，不是本轮实机调试闭环的必要依赖。[README](https://github.com/TexasInstruments/C2000-IDEA/blob/main/README.md)、[IDEA MCP 工具源码](https://github.com/TexasInstruments/C2000-IDEA/blob/main/src/mcp/idea-mcp.ts)。

## 优先检查的本机能力

TI 的新版 CCS Scripting 与旧 DSS 是两套接口，旧脚本不直接兼容。新版以 Node.js 为基础，CCS 20.3 文档同时提供 Python 入口；Python 要求 3.11 或更高，安装目录为 `ccs/scripting/python`，可通过 `launcher.py` 设置包路径，或把其 `site-packages` 加入当前进程的 Python 搜索路径。无需打开 IDE。[CCS Scripting](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_debug-scripting.html)、[DSS 迁移说明](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_debug-scripting-migration.html)。

优先用本机确实存在的新版 Python API；若本机版本只有 JavaScript，Python 可调用 `ccs/scripting/run.bat` 执行一个短脚本；若仅有旧 CCS，则保留 Python 调用 DSS 的兼容路线。不要为了接口统一而升级现有 CCS，也不要混用以下 API。

| 动作 | 新 CCS Scripting | 旧 DSS |
|---|---|---|
| 初始化 | `initScripting(ScriptingOptions(ccsRoot=...))` | `ScriptingEnvironment.instance().getServer("DebugServer.1")` |
| 配置 | `ds.configure(ccxml)` | `server.setConfig(ccxml)` |
| 会话 | `ds.openSession(coreName)` | `server.openSession("*", corePattern)` |
| 连接 | `session.target.connect()` | `session.target.connect()` |
| 加载 | `session.memory.loadProgram(out)` | 同左 |
| 非阻塞运行 | `session.target.run(false)`，Python 为 `False` | `session.target.runAsynch()` |
| 暂停 | `session.target.halt()` | 同左 |
| 表达式 | `session.expressions.evaluate(expr)` | `session.expression.evaluate(expr)` |
| PC | `session.registers.read("PC")` | `session.memory.readRegister("PC")` 或 `session.expression.evaluate("PC")` |
| 结束 | `session.close()` / `ds.shutdown()` | `session.terminate()` / `server.stop()` |

新版接口的对象结果在 Python 中是字典，整数无需处理 JavaScript BigInt。完整本机 API 文档在 `ccs/scripting/docs`；实际参数签名以本机安装包为准。[Python 文档](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_debug-scripting.html#python)、[接口差异表](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_debug-scripting-migration.html)。

## Build 与运行的最小约定

官方 CCS 20 命令行为 `ccs-server-cli -noSplash -workspace <workspace> -application com.ti.ccs.apps.buildProject -ccs.projects <name> -ccs.configuration <config>`；工程尚未登记时用 `com.ti.ccs.apps.importProject -ccs.location <project_dir>` 导入。独立脚本专用 workspace 可避免与正在打开的 CCS 工作区争用，这是本轮设计选择。[TI 命令行构建说明](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_project-command-line.html)。

最短运行方式为非阻塞 run、等待指定毫秒、halt、读取表达式与 PC。`run()` 默认等待目标暂停，不能对无限主循环无期限调用；TI 官方示例设置 `ds.setScriptingTimeout(ms)`，遇到 `ScriptingTimeoutError` 后显式 halt。必须给连接与加载合理的超时，并在失败时保留阶段、原始错误和日志。[运行与超时官方示例](https://software-dl.ti.com/ccs/esd/documents/users_guide_ccs_20.3.0/ccs_debug-scripting.html#example-script)。

第一阶段无需读取 CCS Expressions 窗口；直接给 API 同样的 C/GEL 表达式即可。关键全局量、结构体成员以及寄存器表达式应从当前固件与芯片定义选取；不能把用户示意的 Vout/IL 当成实际已有符号。板上结果应至少带 Build 结论、目标/探针身份、真实 halted 状态、PC、变量值、错误与日志路径；文件存在或 Mock 通过都不代表硬件闭环通过。

## 可执行验收标准

1. 无人工点击 CCS，现有工程 Build 成功，生成可验证的 `.out`。
2. 按 `.ccxml` 连接实际 XDS110/C2000，并成功加载本次构建产物。
3. 运行指定时长后暂停，读到真实 PC 与至少一个固件全局量；重复运行显示能再次连接和取值。
4. CLI 返回可解析的 JSON；Build/连接/读取失败时返回非零状态及明确阶段，不把失败写成 PASS。
5. 如果本次包含固件修改，用改后的构建再次执行上述闭环，结果与修改预期比较。
