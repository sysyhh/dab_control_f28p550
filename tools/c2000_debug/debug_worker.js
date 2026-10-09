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
