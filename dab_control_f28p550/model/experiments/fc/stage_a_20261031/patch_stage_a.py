"""Checked FC INT8 stage-A transforms; never edits an installed library."""
from pathlib import Path
import re

HIDDEN = 'tvmgen_default_fused_cast_cast_multiply_nn_relu_multiply_add_floor_clip_cast'


def body(code, name):
    m = re.search(r'\b' + re.escape(name) + r'\([^;{}]*\)\s*\{', code)
    if not m:
        raise ValueError('missing function: ' + name)
    end, depth = m.end(), 1
    while depth:
        depth += (code[end] == '{') - (code[end] == '}')
        end += 1
    return code[m.end():end-1]


def checked_identity(code):
    # Full expression match, including unsigned type, clipping and rounding.
    expected = '''
for (int32_t ax1 = 0; ax1 < WIDTH; ++ax1) {
float v_ = ((float)((int32_t)p0[ax1])) * 3.906250e-03f;
float v__1 = floorf(((((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f)) * 2.560000e+02f) + 5.000000e-01f));
float v__2 = (v__1) < (2.550000e+02f) ? (v__1) : (2.550000e+02f);
T_cast[ax1] = ((uint8_t)((v__2) > (0.000000e+00f) ? (v__2) : (0.000000e+00f)));
}
return 0;'''
    for name, width in ((HIDDEN, 29), (HIDDEN+'_1', 16)):
        content = body(code, name)
        content = re.sub(r'#if DAB_NPU_DETAIL_PROFILE.*?#endif', '', content, flags=re.S)
        if re.sub(r'\s+', '', content) != re.sub(r'\s+', '', expected.replace('WIDTH', str(width))):
            raise ValueError('unproved hidden expression: ' + name)


def replace_once(code, old, new):
    if code.count(old) != 1:
        raise ValueError('expected unique source: ' + old)
    return code.replace(old, new, 1)


def checked_input(code):
    content=body(code,'tvmgen_default_fused_multiply_add_floor_clip_cast')
    content=re.sub(r'#if DAB_NPU_DETAIL_PROFILE.*?#endif','',content,flags=re.S)
    expected='''for (int32_t ax1 = 0; ax1 < 16; ++ax1) {
    float v_ = floorf(((p0[ax1] * 6.400000e+01f) + 5.000000e-01f));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    T_cast[ax1] = ((int8_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f)));
    }
    return 0;'''
    if re.sub(r'\s+','',content)!=re.sub(r'\s+','',expected):
        raise ValueError('unproved FC input formula')


def transform(code, variant):
    if variant not in ('Baseline', 'A1', 'A2', 'A3', 'A4'):
        raise ValueError(variant)
    if variant in ('A1', 'A2', 'A4'):
        checked_identity(code)
    if variant in ('A3','A4'):
        checked_input(code)
    if variant == 'A1':
        # Keep unpack/pack, alias the identity result to the unpack buffer.
        # Forward in-place compression in case 1 and 3 cannot clobber future reads.
        for suffix, src, dst, pack in (
            ('', 'sid_4_let', 'sid_5_let', 'pack_1'),
            ('_1', 'sid_8_let', 'sid_9_let', 'pack_2'),
            ('_1', 'sid_12_let', 'sid_13_let', 'pack_2'),
        ):
            code = replace_once(code, f'  {HIDDEN}{suffix}({src}, {dst}, global_workspace_0_var);\n', '')
            code = replace_once(code, f'tvmgen_default_fused_tinie_c28_{pack}({dst},',
                                f'tvmgen_default_fused_tinie_c28_{pack}({src},')
    if variant in ('A2', 'A4'):
        # 32->0->32->16; final unpack expands into offset 0, so it must not alias.
        # Driver, parameters, instruction tables, MMR templates remain unchanged.
        for layer, src, dst in ((1, 32, 0), (2, 0, 32), (3, 32, 16)):
            start = code.index(f'case {layer}:')
            end = code.index(f'case {layer+1}:', start)
            old = code[start:end]
            if len(re.findall(r'^  tvmgen_default_', old, re.M)) != 4:
                raise ValueError('unexpected FC transition')
            pad = ('  ((uint16_t*)global_workspace_0_var)[46] &= 0x00ffU;\n'
                   if layer == 1 else '')
            new = (f'case {layer}:\n' + pad +
                   f'  tvmgen_default_ti_npu_fullyConnectedNHWC_{layer}'
                   f'(&global_workspace_0_var[{src}], &global_workspace_0_var[{dst}], global_workspace_0_var);\n'
                   '  return;\n')
            code = code[:start] + new + code[end:]
    if variant in ('A3', 'A4'):
        code = replace_once(code, 'static float* features_buffer_var;', 'static uint16_t* features_buffer_var;')
        code = replace_once(code, '___tvm_main__(float* features_buffer_var,',
                            '___tvm_main__(uint16_t* features_buffer_var,')
        code = replace_once(code, '___tvm_main__(float* features_buffer_var_arg,',
                            '___tvm_main__(uint16_t* features_buffer_var_arg,')
        code = replace_once(code,
            '  tvmgen_default_fused_multiply_add_floor_clip_cast(features_buffer_var, sid_1_let, global_workspace_0_var);\n'
            '  tvmgen_default_fused_tinie_c28_pack(sid_1_let, sid_2_let, global_workspace_0_var);\n'
            '  tvmgen_default_ti_npu_fullyConnectedNHWC_0(sid_2_let, sid_3_let, global_workspace_0_var);',
            '  tvmgen_default_ti_npu_fullyConnectedNHWC_0((int8_t*)features_buffer_var, sid_3_let, global_workspace_0_var);')
    return code


INPUT_HEADER = '''/* FC stage A: C28 packed integer input, eight 16-bit storage units.
 * Constants are initialized once by the application; only the Vin code changes.
 * Every float operation is the original firmware expression, in the same order. */
#ifndef FC_STAGE_A_INPUT_H
#define FC_STAGE_A_INPUT_H
#include <stdint.h>
#include <math.h>
static inline void DAB_FC_preparePackedInput(float vin_volts, uint16_t *packed)
{
    float normalized = vin_volts / 140.0f;
    float v_ = floorf(((normalized * 6.400000e+01f) + 5.000000e-01f));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    int16_t q = (int16_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f));
    packed[0] = 0x00e0U | ((uint16_t)(q & 0x00ff) << 8);
}
#endif
'''


def application(code, prequant):
    if not prequant:
        return code
    code = '#include "fc_stage_a_input.h"\n' + code
    code = replace_once(code, 'static float s_input[DAB_NPU_RUNTIME_INPUT_DIM];',
        '#pragma DATA_ALIGN(s_input, 16)\n#pragma DATA_SECTION(s_input, "ramgs1")\n'
        'static uint16_t s_input[8] = {0x00e0U, 0x0012U, 0, 0, 0, 0, 0, 0};\n'
        '#if DAB_NPU_DETAIL_PROFILE\nstatic uint32_t s_stageInputTicks;\n#endif')
    code = replace_once(code,
        '    memset(s_input, 0, sizeof(s_input));\n'
        '    s_input[0] = -0.5f; // 原生三维输入；多出的硬件通道严格补零，不把常量折进偏置。\n'
        '    s_input[1] = vin_volts / 140.0f;\n'
        '    s_input[2] = 0.285714f;',
        '#if DAB_NPU_DETAIL_PROFILE\n    s_stageInputTicks = CPUTimer_getTimerCount(CPUTIMER2_BASE);\n#endif\n'
        '    DAB_FC_preparePackedInput(vin_volts, s_input);\n'
        '#if DAB_NPU_DETAIL_PROFILE\n    s_stageInputTicks -= CPUTimer_getTimerCount(CPUTIMER2_BASE);\n#endif')
    code = replace_once(code, '        s_busy = true;',
        '        s_busy = true;\n#if DAB_NPU_DETAIL_PROFILE\n'
        '        s_traceTicks[DAB_NPU_INPUT] = s_stageInputTicks;\n'
        '        s_traceCalls[DAB_NPU_INPUT] = 1U;\n#endif')
    code = replace_once(code, 'void DAB_NN_init(void)\n{\n    memset(s_input, 0, sizeof(s_input));',
        'void DAB_NN_init(void)\n{\n    memset(s_input, 0, sizeof(s_input));\n'
        '    s_input[0] = 0x00e0U;\n    s_input[1] = 0x0012U;')
    return code
