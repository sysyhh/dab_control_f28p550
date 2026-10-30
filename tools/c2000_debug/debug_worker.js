// Runs with the CCS-provided Node runtime and its installed scripting module.
const fs = require('node:fs');
const path = require('node:path');
const request = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { initScripting, sleep } = require(path.join(request.ccs, 'scripting/node_modules/scripting'));
const result = { connected: false, state: 'unknown', loaded: false, variables: {}, registers: {}, errors: [], samples: [] };
let ds, session;
function save() {
    fs.writeFileSync(request.result, JSON.stringify(result, (_, v) =>
        typeof v === 'bigint' ? (v <= BigInt(Number.MAX_SAFE_INTEGER) && v >= BigInt(Number.MIN_SAFE_INTEGER) ? Number(v) : v.toString()) : v, 2));
}
function sample() {
    const values = {};
    for (const expression of request.expressions) {
        try {
            const value = session.expressions.evaluate(expression);
            if (value === undefined) throw new Error('Expression does not return a scalar; select a member or array element');
            values[expression] = value;
        } catch (e) { result.errors.push({ stage: 'read', expression, message: String(e) }); }
    }
    return values;
}
try {
    result.stage = 'configure'; save();
    ds = initScripting({ timeout: request.timeout_ms, suppressMessages: true });
    ds.configure(request.ccxml);
    result.cores = ds.listCores();
    session = ds.openSession(/C28/i);
    result.stage = 'connect'; save();
    session.target.connect();
    result.connected = session.target.isConnected();
    session.target.halt();
    if (request.attach_only) {
        // 只读取原现场；符号加载不写入程序，也不复位或恢复运行。
        result.stage = 'attach_symbols'; save();
        result.attach_pc_before_symbols = session.registers.read('PC');
        session.symbols.load(request.out);
        result.symbols_loaded = true;
        result.attach_pc_after_symbols = session.registers.read('PC');
        if (result.attach_pc_before_symbols !== result.attach_pc_after_symbols)
            throw new Error('PC changed while loading symbols; target GEL may have reset the CPU');
        try { session.memory.verifyProgram(request.out); result.program_verified = true; }
        catch (e) { result.program_verified = false; result.errors.push({ stage: 'verify_program', message: String(e) }); }
        const values = sample();
        result.samples.push({ index: 0, values, pc: session.registers.read('PC') });
        result.variables = values;
    } else {
        result.stage = 'reset'; save();
        session.target.reset();
        result.stage = 'load'; save();
        session.memory.loadProgram(request.out);
        result.loaded = true;
        result.stage = 'run'; save();
        for (let i = 0; i < request.samples; i++) {
        session.target.run(false);
        sleep(request.run_ms);
        session.target.halt();
        if (!session.target.isHalted()) throw new Error('Target did not halt');
        const values = sample();
        result.samples.push({ index: i, values, pc: session.registers.read('PC') });
        result.variables = values;
        }
    }
    if (request.read_e2e_ticks) {
        result.stage = 'read_e2e_ticks';
        const addr = session.symbols.getAddress('g_nnBenchmarkE2eTicks');
        const words = session.memory.read(addr, 2000, 16);
        const ticks = [];
        for (let i = 0; i < 1000; i++) {
            const lo = Number(words[2 * i]);
            const hi = Number(words[2 * i + 1]);
            ticks.push((hi << 16) >>> 0 | (lo & 0xffff));
        }
        result.e2e_ticks = ticks;
        result.e2e_ticks_address = addr;
    }
    if (request.verify_npu_const) {
        result.stage = 'verify_constants';
        // 链接器符号直接给出地址/长度；通过符号表读取，避免表达式求地址报错。
        // 只在本轮统计结束后比较镜像，不影响推理期间的计时。
        const load = session.symbols.getAddress('DabNpuConstLoadStart');
        const run = session.symbols.getAddress('DabNpuConstRunStart');
        const words = Number(session.symbols.getAddress('DabNpuConstLoadSize'));
        if (run !== 0x9800n || load < 0x80000n || load >= 0xc0000n || !(words > 0 && words <= 2048))
            throw new Error('Unexpected model constant load/run bounds');
        const flash = session.memory.read(load, words, 16);
        const ram = session.memory.read(run, words, 16);
        const mismatch = flash.findIndex((value, index) => value !== ram[index]);
        result.model_constant_copy = { load, run, words, matches: mismatch === -1, first_mismatch: mismatch };
        if (flash.length !== words || ram.length !== words || mismatch !== -1)
            throw new Error('Model RAM constants differ from Flash image');
    }
    for (const register of request.registers) {
        try { result.registers[register] = session.registers.read(register); }
        catch (e) { result.errors.push({ stage: 'register', register, message: String(e) }); }
    }
    for (const [register, address] of Object.entries(request.memory_registers || {})) {
        try { result.registers[register] = session.memory.read(BigInt(address), 1, 16)[0]; }
        catch (e) { result.errors.push({ stage: 'register', register, message: String(e) }); }
    }
    result.state = session.target.isHalted() ? 'halted' : 'running';
    result.stage = 'complete';
} catch (e) {
    result.errors.push({ stage: result.stage, message: String(e), stack: e.stack });
} finally {
    if (session && result.connected) {
        try { session.target.halt(); result.state = session.target.isHalted() ? 'halted' : 'unknown'; }
        catch (e) { result.errors.push({ stage: 'cleanup_halt', message: String(e) }); }
    }
    save();
    if (ds) {
        try { ds.shutdown(); result.debugger_closed = true; }
        catch (e) { result.errors.push({ stage: 'shutdown', message: String(e) }); }
    }
    save();
}
process.exit(result.errors.length ? 1 : 0);
