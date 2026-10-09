"""Checked, reproducible edits of this model's TI NNC output (not arbitrary models)."""
import re

IDENTITY = 'tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast'

def hidden_identity(code, constants):
    """Only these checked power-of-two quantizers are uint8 identities."""
    for suffix, count, scale, inverse in [('',32,64,'1.562500e-02f'),('_1',16,128,'7.812500e-03f'),('_2',16,256,'3.906250e-03f')]:
        for stem, expected in [('fused_cast_cast_multiply_nn_relu_constant',float(scale)),
                               ('fused_cast_cast_multiply_nn_relu_multiply_constant',0.5)]:
            value=re.search(r'\.'+stem+suffix+r'_let\s*=\s*\{\s*([^\s}]+)',constants)
            if not value or float.fromhex(value[1]) != expected:
                raise RuntimeError('Unexpected hidden-layer quantization constant')
        def replace(body):
            if inverse not in body or f'ax3 < {count};' not in body or 'floorf(' not in body:
                raise RuntimeError('Unexpected hidden-layer quantization expression')
            return ('\n  /* uint8 全范围逐值验证：逆缩放、ReLU、再缩放及取整的结果均为原值。 */\n'
                    f'  for (int32_t i = 0; i < {count}; ++i) T_cast[i] = p0[i];\n  return 0;\n')
        code=function(code,IDENTITY+suffix,replace)
    return code

def packed_transitions(code):
    """Keep original next-layer buffers; copying avoids input/output aliasing."""
    offsets={name:int(offset) for name,offset in re.findall(r'(sid_\d+_let) = \(&\(global_workspace_1_var\[(\d+)\]\)\);',code)}
    for layer,words in [(1,16),(2,8),(3,8)]:
        begin=code.index(f'case {layer}:'); end=code.index(f'case {layer+1}:',begin)
        block=code[begin:end]
        lines=block.splitlines()
        calls=[line.strip() for line in lines if line.strip().startswith('tvmgen_default_')]
        if len(calls)!=4 or 'unpack' not in calls[0] or IDENTITY not in calls[1] or 'pack_' not in calls[2] or 'convolve' not in calls[3]:
            raise RuntimeError('Unexpected layer transition sequence')
        source=re.search(r'\((sid_\d+_let),',calls[0])[1]
        destination=re.search(r'\(sid_\d+_let, (sid_\d+_let),',calls[2])[1]
        if 0 < abs(offsets[source]-offsets[destination]) < words:
            raise RuntimeError('Packed transition buffers overlap')
        replaced=f'  dab_npu_copy_words((uint16_t*){source}, (uint16_t*){destination}, {words}U);'
        block=block.replace('\n'.join(lines[1:4]),replaced)
        code=code[:begin]+block+code[end:]
    helper='''TVM_DLL int32_t dab_npu_copy_words(uint16_t* source, uint16_t* destination, uint16_t words) {
  /* C28 一个存储单元包含两个 8 位通道；保持原目标缓冲区，避免下一层输入和输出重叠。 */
'''+trace('DAB_NN_traceBegin(DAB_NPU_PACK)')+'''  for (uint16_t i = 0; i < words; ++i) destination[i] = source[i];
'''+trace('DAB_NN_traceEnd(DAB_NPU_PACK)')+'''  return 0;
}
'''
    return code.replace('void tvmgen_default_IRQHandlerHelper();',helper+'void tvmgen_default_IRQHandlerHelper();',1)

def function(code, name, transform):
    match=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',code)
    if not match: raise RuntimeError("Missing generated function: "+name)
    begin=match.end(); depth=1; end=begin
    while depth:
        depth += (code[end]=='{')-(code[end]=='}'); end+=1
    return code[:begin]+transform(code[begin:end-1])+code[end-1:]

def trace(call):
    return '\n#if DAB_NPU_DETAIL_PROFILE\n  '+call+';\n#endif\n'

def ram_functions(code, names):
    """Dedicated section, separately copied at startup; no GS1 code placement."""
    for name in names:
        if not re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{',code):
            raise RuntimeError('Missing RAM function '+name)
    return '\n'.join(f'#pragma CODE_SECTION({name}, ".dab_npu_ramfunc")' for name in names)+'\n'+code

def ram_constants(code):
    # 仅改变 CPU 读取常量的位置；每层向 NPU 的完整装载流程保持原样。
    arrays=re.findall(r'static const uint32_t (PWCONV_(?:PARAMS|MMR)(?:_\d+)?)\[\]',code)
    headers=sorted(set(re.findall(r'#include "hard/ins_asm/(PWCONV_\w+_INS)\.h"',code)))
    if (sum(name.startswith('PWCONV_PARAMS') for name in arrays)!=4 or
            sum(name.startswith('PWCONV_MMR') for name in arrays)!=4 or len(headers)!=2):
        raise RuntimeError('Unexpected constant layout; expected 4 parameter/4 MMR arrays and 2 instruction tables')
    names=arrays+headers
    return '\n'.join(f'#pragma DATA_SECTION({name}, ".dab_npu_const")' for name in names)+'\n'+code,names

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

def load_unroll(code):
    """Preserve every volatile MMIO write and its stride, amortize loop control."""
    for target,field in [('params','params'),('ins','ins')]:
        old=(f'    for (int i = 0; i < layer->num_{field}; i++)\n'
             '    {\n'+f'        {target}[i * 2] = layer->{field}[i];\n'+'    }')
        if code.count(old)!=1: raise RuntimeError('Unexpected TI loading loop: '+field)
        code=code.replace(old,f'    dab_npu_load_words({target}, layer->{field}, layer->num_{field});')
    helper='''
#pragma FUNC_ALWAYS_INLINE(dab_npu_load_words)
static int32_t dab_npu_load_words(volatile uint32_t* destination, const uint32_t* source, uint32_t count) {
    /* 保留 TI 的隔一个 32 位位置写入规则；按原顺序写四项，减少循环判断。 */
    while (count >= 4U) {
        destination[0] = source[0];
        destination[2] = source[1];
        destination[4] = source[2];
        destination[6] = source[3];
        source += 4; destination += 8; count -= 4U;
    }
    /* 处理不足四项的尾部，禁止越界读或写相邻保留位置。 */
    while (count != 0U) { *destination = *source++; destination += 2; --count; }
    return 0;
}
'''
    return code.replace('void TINIE_setup(TINIE_layer_t *layer)',helper+'void TINIE_setup(TINIE_layer_t *layer)',1)
