"""Checked, reproducible edits of this model's TI NNC output (not arbitrary models)."""
import re

IDENTITY = 'tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast'

def hidden_identity(code, constants):
    """Only these checked power-of-two quantizers are uint8 identities."""
    for suffix, scale, inverse in [('',64,'1.562500e-02f'),('_1',128,'7.812500e-03f'),('_2',256,'3.906250e-03f')]:
        for stem, expected in [('fused_cast_cast_multiply_nn_relu_constant',float(scale)),
                               ('fused_cast_cast_multiply_nn_relu_multiply_constant',0.5)]:
            value=re.search(r'\.'+stem+suffix+r'_let\s*=\s*\{\s*([^\s}]+)',constants)
            if not value or float.fromhex(value[1]) != expected:
                raise RuntimeError('Unexpected hidden-layer quantization constant')
        def replace(body):
            count=re.search(r'ax3 < (\d+);',body)
            if not count or inverse not in body or 'floorf(' not in body:
                raise RuntimeError('Unexpected hidden-layer quantization expression')
            width=int(count[1])
            if width not in (8, 12, 16, 32):
                raise RuntimeError(f'Unexpected hidden-layer width {width}')
            return ('\n  /* uint8 全范围逐值验证：逆缩放、ReLU、再缩放及取整的结果均为原值。 */\n'
                    f'  for (int32_t i = 0; i < {width}; ++i) T_cast[i] = p0[i];\n  return 0;\n')
        code=function(code,IDENTITY+suffix,replace)
    return code

def pack_channels(code, name):
    match=re.search(r'\b'+re.escape(name)+r'\([^;{}]*\)\s*\{(?:.|\n)*?for \(int32_t i = 0; i < (\d+);',code)
    if not match:
        raise RuntimeError('Missing pack loop in '+name)
    return int(match[1])

def packed_transitions(code):
    """Keep original next-layer buffers; copying avoids input/output aliasing."""
    offsets={name:int(offset) for name,offset in re.findall(r'(sid_\d+_let) = \(&\(global_workspace_1_var\[(\d+)\]\)\);',code)}
    for layer in (1, 2, 3):
        begin=code.index(f'case {layer}:'); end=code.index(f'case {layer+1}:',begin)
        block=code[begin:end]
        lines=block.splitlines()
        calls=[line.strip() for line in lines if line.strip().startswith('tvmgen_default_')]
        if len(calls)!=4 or 'unpack' not in calls[0] or IDENTITY not in calls[1] or 'pack' not in calls[2] or 'convolve' not in calls[3]:
            raise RuntimeError('Unexpected layer transition sequence')
        pack_name=re.search(r'(tvmgen_default_fused_tinie_c28_pack(?:_\d+)?)',calls[2])[1]
        channels=pack_channels(code, pack_name)
        if channels % 2:
            raise RuntimeError(f'Odd packed channel count {channels}')
        words=channels // 2
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
    arrays=re.findall(r'static const uint32_t ((?:PWCONV|FC)_(?:PARAMS|MMR)(?:_\d+)?(?:_sub\d+)?)\[\]',code)
    headers=sorted(set(re.findall(r'#include "hard/ins_asm/((?:PWCONV|FC)_\w+_INS)\.h"',code)))
    n_params=sum('PARAMS' in name for name in arrays)
    n_mmr=sum('MMR' in name for name in arrays)
    pwconv=any(name.startswith('PWCONV_') for name in arrays)
    if pwconv:
        if (sum(name.startswith('PWCONV_PARAMS') for name in arrays)!=4 or
                sum(name.startswith('PWCONV_MMR') for name in arrays)!=4 or not 1 <= len(headers) <= 2):
            raise RuntimeError('Unexpected constant layout; expected 4 parameter/4 MMR arrays and 1 or 2 instruction tables')
    elif n_params < 4 or n_mmr < 4 or n_params != n_mmr or not 1 <= len(headers) <= 4:
        raise RuntimeError(f'Unexpected FC constant layout: params={n_params} mmr={n_mmr} ins={headers}')
    names=arrays+headers
    return '\n'.join(f'#pragma DATA_SECTION({name}, ".dab_npu_const")' for name in names)+'\n'+code,names

def output_stage(name):
    """2.1.0 ends at cast_multiply; 2.1.1 appends _reshape to the same final float restore."""
    return name.endswith('_fused_cast_multiply') or name.endswith('_fused_cast_multiply_reshape')

INPUT_QUANT = 'tvmgen_default_fused_reshape_multiply_add_floor_clip_cast_reshape'
VIN_CHANNEL_LOOP = re.compile(
    r'  void\* fused_reshape_multiply_constant_let = \(&\(global_const_workspace_2_var\[0\]\)\);\n'
    r'  void\* fused_reshape_constant_let = \(&\(global_const_workspace_2_var\[16\]\)\);\n'
    r'  for \(int32_t ax3 = 0; ax3 < (\d+); \+\+ax3\) \{\n'
    r'    float v_ = floorf\(\(\(p0\[ax3\] \* \(\(float\*\)fused_reshape_constant_let\)\[0\]\) \+ \(\(float\*\)fused_reshape_multiply_constant_let\)\[0\]\)\);\n'
    r'    float v__1 = \(v_\) < \(1\.270000e\+02f\) \? \(v_\) : \(1\.270000e\+02f\);\n'
    r'    T_reshape\[ax3\] = \(\(int8_t\)\(\(v__1\) > \(-1\.280000e\+02f\) \? \(v__1\) : \(-1\.280000e\+02f\)\)\);\n'
    r'  \}\n')

def vin_channel_quant(code):
    """Keep the original scale/bias/floor/clip on the live Vin channel; zeros stay zero."""
    match=VIN_CHANNEL_LOOP.search(code)
    if not match:
        raise RuntimeError('Unexpected DAB input quantization loop')
    width=int(match.group(1))
    if width not in (4, 16):
        raise RuntimeError(f'Unexpected input width {width}')
    fast=(
        '  void* fused_reshape_multiply_constant_let = (&(global_const_workspace_2_var[0]));\n'
        '  void* fused_reshape_constant_let = (&(global_const_workspace_2_var[16]));\n'
        f'  /* 本模型其余 {width-1} 项输入恒为 0；floor(0*scale+0.5)=0，与原循环逐项量化一致。 */\n'
        f'  for (int32_t ax3 = 0; ax3 < {width}; ++ax3) T_reshape[ax3] = 0;\n'
        '  {\n'
        '    float v_ = floorf(((p0[1] * ((float*)fused_reshape_constant_let)[0]) + ((float*)fused_reshape_multiply_constant_let)[0]));\n'
        '    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);\n'
        '    T_reshape[1] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));\n'
        '  }\n')
    return code[:match.start()]+fast+code[match.end():]

INS_WRITE = '''    if (layer->num_ins > 0)
    {
        TINIE_mem_write(ins, layer->num_ins, layer->ins);
    }
'''
INS_REUSE = '''    if (layer->num_ins > 0)
    {
        /* 指令区在层执行后保持；仅在表指针或长度变化时重写。参数区仍每层覆盖。 */
        if (layer->ins != dab_npu_loaded_ins || layer->num_ins != dab_npu_loaded_ins_count)
        {
            TINIE_mem_write(ins, layer->num_ins, layer->ins);
            dab_npu_loaded_ins = layer->ins;
            dab_npu_loaded_ins_count = layer->num_ins;
        }
    }
'''

def reuse_instructions(code):
    """Skip rewriting NPU instruction memory when the same table is already resident."""
    if INS_WRITE not in code or code.count('void TINIE_setup(TINIE_layer_t *layer)') != 1:
        raise RuntimeError('Unexpected TINIE instruction load block')
    if 'void TI_NPU_init(void)' not in code:
        raise RuntimeError('Missing TI_NPU_init; cannot invalidate instruction residency')
    code = code.replace(
        'void TINIE_setup(TINIE_layer_t *layer)',
        'static const uint32_t *dab_npu_loaded_ins;\nstatic uint32_t dab_npu_loaded_ins_count;\n\n'
        'void TINIE_setup(TINIE_layer_t *layer)',
        1)
    code = code.replace(INS_WRITE, INS_REUSE, 1)
    init = 'void TI_NPU_init(void)\n{'
    if code.count(init) != 1:
        raise RuntimeError('Unexpected TI_NPU_init layout')
    return code.replace(
        init,
        init + '\n    dab_npu_loaded_ins = 0;\n    dab_npu_loaded_ins_count = 0U;\n',
        1)


def instrument(code, enabled):
    names=re.findall(r'\b(tvmgen_default_fused_\w+)\([^;{}]*\)\s*\{',code)
    outputs=[name for name in names if output_stage(name)]
    if len(outputs)!=1:
        raise RuntimeError('Expected one final float output stage, found: '+', '.join(outputs))
    for name in names:
        slot=('DAB_NPU_PACK' if '_tinie_c28_pack' in name else
              'DAB_NPU_UNPACK' if '_tinie_c28_unpack' in name else
              'DAB_NPU_CONVERT' if '_cast_cast_multiply_nn_relu' in name else
              'DAB_NPU_INPUT' if ('_reshape_multiply_add_floor' in name or
                                  name.endswith('fused_multiply_add_floor_clip_cast')) else
              'DAB_NPU_OUTPUT' if output_stage(name) else None)
        if slot:
            code=function(code,name,lambda body, slot=slot: trace('DAB_NN_traceBegin('+slot+')')+body.replace('  return 0;',trace('DAB_NN_traceEnd('+slot+')')+'  return 0;'))
    if code.count('DAB_NN_traceBegin(DAB_NPU_OUTPUT)')!=1:
        raise RuntimeError('Final float output stage was not instrumented')
    def wrap_irq(body):
        return ('  uint16_t dab_npu_isr_layer = (uint16_t)tinie_curr_layer;\n'
                '  DAB_NN_isrEnter();\n'
                + trace('DAB_NN_traceEnd(DAB_NPU_WAIT0 + tinie_curr_layer - 1)')
                + body
                + '  DAB_NN_isrExit(dab_npu_isr_layer);\n')
    code=function(code,'tvmgen_default_IRQHandler', wrap_irq)
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
