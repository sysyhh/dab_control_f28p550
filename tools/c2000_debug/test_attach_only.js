// Exercise the actual worker: attaching must never reset, program or resume.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'debug_worker.js'), 'utf8');
for (const verifyFails of [false, true]) {
    let saved, exitCode;
    const calls = [];
    const forbidden = () => { throw new Error('Forbidden target mutation'); };
    const request = {ccs:'fixture',out:'existing.out',attach_only:true,result:'result.json',
        expressions:['g_firstFault.reason'],registers:['PC'],memory_registers:{EPWM7_TZFLG:0x4693},samples:2};
    const session = {
        target:{connect(){calls.push('connect');},isConnected(){return true;},halt(){calls.push('halt');},
            isHalted(){return true;},reset:forbidden,run:forbidden},
        symbols:{load(file){assert.equal(file,'existing.out');calls.push('symbols');}},
        memory:{loadProgram:forbidden,verifyProgram(){calls.push('verify');if(verifyFails)throw new Error('image mismatch');},
            read(){return [4];}},
        expressions:{evaluate(){return 5;}},registers:{read(){return 0x80000;}}
    };
    const ds={configure(){},listCores(){return ['C28'];},openSession(){return session;},shutdown(){calls.push('shutdown');}};
    const fakefs={readFileSync(){return JSON.stringify(request);},writeFileSync(file,text){saved=JSON.parse(text);}};
    const context={require(name){if(name==='node:fs')return fakefs;if(name==='node:path')return path;
        return {initScripting(){return ds;},sleep:forbidden};},
        process:{argv:['node','worker','request'],exit(code){exitCode=code;}}};
    vm.runInNewContext(source,context);
    assert.equal(saved.loaded,false);
    assert.equal(saved.symbols_loaded,true);
    assert.equal(saved.program_verified,!verifyFails);
    assert.equal(saved.variables['g_firstFault.reason'],5);
    assert.equal(saved.samples.length,1);
    assert.equal(saved.state,'halted');
    assert.equal(saved.debugger_closed,true);
    assert.equal(exitCode,verifyFails?1:0);
    assert.deepEqual(calls,['connect','halt','symbols','verify','halt','shutdown']);
}
console.log('PASS: attach only reads original fault without reset/load/run; image mismatch retains snapshot and fails explicitly');
