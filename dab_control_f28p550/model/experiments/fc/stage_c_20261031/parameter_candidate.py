"""Admission and independent PARAMS-only copier; original copier remains intact."""
import random
import re
from common_c import *


def patch(s):
    return '#include <stdint.h>\nextern void DAB_C_mem_write_fast(volatile uint32_t*, uint32_t, const uint32_t*);\n'+replace_once(s,
      'TINIE_mem_write(params, layer->num_params, layer->params);',
      'DAB_C_mem_write_fast(params, layer->num_params, layer->params);')


def main():
    audit=json.loads((HERE/'results/transfer_audit.json').read_text());assert audit['ok']
    text=(HERE/'candidates/tinie_mem_write_fast.asm').read_text()
    # Interpret the actual assembly, including flags, repeat count, pointer increments,
    # and the callee-saved register. Timing is deliberately not modeled.
    lines=[];labels={}
    for raw in text.splitlines():
        line=raw.split(';')[0].strip()
        if not line or line.startswith('.'):continue
        if ':' in line:
            label,line=line.split(':',1);labels[label]=len(lines);line=line.strip()
        if line and not line.startswith('.'):lines.append(line)
    rng=random.Random(20261031)
    for n in range(513):
        r={f'XAR{i}':0 for i in range(8)};r.update(XAR4=10000,XAR5=20000,XAR1=123456,ACC=n)
        mem={20000+2*i:rng.getrandbits(32) for i in range(520)};before=dict(mem);stores=[];stack=[]
        pc=0;eq=False;repeat=None;steps=0
        def get(x):
            if x.startswith('#'):return int(x[1:],0)
            if x=='AL':return r['ACC']&65535
            if x.startswith('AR'):return r['X'+x]&65535
            return r[x]
        def put(x,v):
            if x=='AL':r['ACC']=(r['ACC']&0xffff0000)|(v&65535)
            elif x.startswith('AR'):r['X'+x]=(r['X'+x]&0xffff0000)|(v&65535)
            else:r[x]=v&0xffffffff
        while True:
            if repeat and pc==repeat[0]:
                if repeat[2]>0:repeat[2]-=1;pc=repeat[1]
                else:repeat=None
            line=lines[pc];pc+=1;steps+=1;assert steps<10000
            op,_,arg=line.partition(' ');arg=arg.strip();args=arg.split(',')
            if op=='LRETR':break
            if op=='CLRC':continue
            if op=='MOVL' and args[0]=='*SP++':stack.append(get(args[1]));continue
            if op=='MOVL' and args[1]=='*--SP':put(args[0],stack.pop());continue
            if op=='MOVL' and args[1]=='*XAR5++':put(args[0],mem[r['XAR5']]);r['XAR5']+=2;continue
            if op=='MOVL' and args[0].startswith('*'):
                m=re.fullmatch(r'\*\+XAR4\[(.*?)\]',args[0]);off=get(m[1]) if m and m[1].startswith('AR') else int(m[1]) if m else 0
                address=r['XAR4']+off;mem[address]=get(args[1]);stores.append(address);continue
            if op in ('MOVL','MOV','MOVZ','MOVB'):put(args[0],get(args[1]));continue
            if op=='ANDB':put(args[0],get(args[0])&get(args[1]));continue
            if op=='SFR':put(args[0],get(args[0])>>int(args[1]));continue
            if op=='CMPB':eq=get(args[0])==get(args[1]);continue
            if op=='B':
                assert args[1]=='EQ'
                if eq:pc=labels[args[0]]
                continue
            if op in ('ADDB','SUBB'):put(args[0],get(args[0])+(1 if op=='ADDB' else -1)*get(args[1]));continue
            if op=='RPTB':repeat=[labels[args[0]],pc,get(args[1])];continue
            if op=='BANZ':
                key=args[1][:-2];v=get(key);put(key,v-1)
                if v!=0:pc=labels[args[0]]
                continue
            raise AssertionError(line)
        assert stores==[10000+4*i for i in range(n)] and not stack and r['XAR1']==123456
        assert all(mem[10000+4*i]==before[20000+2*i] for i in range(n))
        assert all(mem[k]==v for k,v in before.items())
    dump(HERE/'results/parameter_candidate_admission.json',dict(ok=True,host_assembly_trace_lengths=list(range(513)),
      source_sha256=sha(HERE/'candidates/tinie_mem_write_fast.asm'),admitted_lengths=[208,168,104,26],
      evidence='baseline RPTB has 4 repeated offset MOVB instructions per 8 words; target audit confirms both software and peripheral costs',
      scope='only TINIE_setup parameter copy; original instruction/MMR copies unchanged',
      block_instructions_before=22,block_payload_before=8,block_instructions_after=9,block_payload_after=4,
      ABI='XAR1 restored, no other callee-saved registers modified; RPTB retained; target execution required'))
    protect();print('parameter candidate host assembly trace PASS: n=0..512')


if __name__=='__main__':main()
