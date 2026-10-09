"""Checked, reproducible edits of this model's TI NNC output (not arbitrary models)."""
import re

def function(code, name, transform):
    match=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',code)
    if not match: raise RuntimeError("Missing generated function: "+name)
    begin=match.end(); depth=1; end=begin
    while depth:
        depth += (code[end]=='{')-(code[end]=='}'); end+=1
    return code[:begin]+transform(code[begin:end-1])+code[end-1:]

def trace(call):
    return '\n#if DAB_NPU_DETAIL_PROFILE\n  '+call+';\n#endif\n'

def instrument(code, enabled):
    names=re.findall(r'\b(tvmgen_default_fused_\w+)\([^;{}]*\)\s*\{',code)
    for name in names:
        slot=('DAB_NPU_PACK' if '_tinie_c28_pack' in name else
              'DAB_NPU_UNPACK' if '_tinie_c28_unpack' in name else
              'DAB_NPU_CONVERT' if '_cast_cast_multiply_nn_relu' in name else
              'DAB_NPU_INPUT' if '_reshape_multiply_add_floor' in name else
              'DAB_NPU_OUTPUT' if name.endswith('_fused_cast_multiply') else None)
        if slot:
            code=function(code,name,lambda body: trace('DAB_NN_traceBegin('+slot+')')+body.replace('  return 0;',trace('DAB_NN_traceEnd('+slot+')')+'  return 0;'))
    code=function(code,'tvmgen_default_IRQHandler',lambda body:trace('DAB_NN_traceEnd(DAB_NPU_WAIT0 + tinie_curr_layer - 1)')+body)
    return '#define DAB_NPU_DETAIL_PROFILE '+str(int(enabled))+'\n#include "dab_npu_trace.h"\n'+code

def instrument_driver(code, enabled):
    for marker,slot in [('    // Step 1 - write to PARAMS memory','DAB_NPU_PARAMS'),
                        ('    // Step 2 - write to INS memory','DAB_NPU_INS'),
                        ('    // Step 3 - write to MMRs','DAB_NPU_REGISTERS')]:
        if marker not in code: raise RuntimeError('Unexpected TI runtime setup layout')
    code=code.replace('    // Step 1 - write to PARAMS memory',trace('DAB_NN_traceBegin(DAB_NPU_PARAMS)')+'    // Step 1 - write to PARAMS memory')
    code=code.replace('    // Step 2 - write to INS memory',trace('DAB_NN_traceEnd(DAB_NPU_PARAMS)')+trace('DAB_NN_traceBegin(DAB_NPU_INS)')+'    // Step 2 - write to INS memory')
    code=code.replace('    // Step 3 - write to MMRs',trace('DAB_NN_traceEnd(DAB_NPU_INS)')+trace('DAB_NN_traceBegin(DAB_NPU_REGISTERS)')+'    // Step 3 - write to MMRs')
    code=code.replace('    write_configMMR(layer);','    write_configMMR(layer);'+trace('DAB_NN_traceEnd(DAB_NPU_REGISTERS)'))
    code=function(code,'TINIE_start',lambda body:trace('DAB_NN_traceBegin(DAB_NPU_WAIT0 + tinie_curr_layer - 1)')+body)
    return '#define DAB_NPU_DETAIL_PROFILE '+str(int(enabled))+'\n#include "dab_npu_trace.h"\nextern volatile int32_t tinie_curr_layer;\n'+code
