"""Full finite Vin domain, decoded NNC integer parameters, and Stage-A goldens."""
import hashlib
import json
from pathlib import Path
import re
import struct
import numpy as np
from audit_stage_b import HERE,FC,STAGE_A,arrays,mapping,dump,protect


def section(code,name):
    return re.search(r'static const uint32_t '+re.escape(name)+r'\[\] = \{(.*?)\};',code,re.S)[1]


def words(text):return [int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',text)]


def decode(path,widths):
    code=(path/'lib2.c').read_text(encoding='utf-8');mmrs=arrays(code,'FC_MMR');mp=mapping(path)
    layers=[]
    for i,layer in enumerate(mp['layers']):
        ws=[];bs=[];sc=[];sh=[]
        nin=widths[i]
        for pname,mname,ins in zip(layer['parameters'],layer['mmrs'],layer['instructions']):
            s=section(code,pname)
            wtxt,rest=s.split('// 24-bit bias in little-endian:')
            btxt,stxt=rest.split('// (8-bit scale, 5-bit shift (store as 8-bit)) pairs in little-endian:')
            wp,bp,sp=words(wtxt),words(btxt),words(stxt)
            block=4 if ins.endswith('_oCm4_INS') else 1
            assert block==4 or ins.endswith('_oC1LL_INS')
            groups=mmrs[mname][8]+1;nout=block*groups
            w=np.zeros((nout,((nin+7)//8)*8),np.int64);cursor=0
            for group in range(groups):
                for ib in range(w.shape[1]//4):
                    for oc in range(block):
                        word=wp[cursor];cursor+=1
                        for k in range(4):
                            v=sum(((word>>(j*8+k*2))&3)<<(j*2) for j in range(4))
                            w[group*block+oc,ib*4+k]=v-256 if v>=128 else v
            assert cursor==len(wp)
            b=[]
            assert len(bp)==nout*2
            for k in range(nout):
                hi=(bp[2*k+1]>>16)&65535;hi=hi-65536 if hi>=32768 else hi
                b.append((bp[2*k]&65535)+hi*256)
            ss=[(x>>(16*k))&65535 for x in sp for k in (0,1)][:nout]
            assert len(ss)==nout
            ws.append(w[:,:nin]);bs.extend(b);sc.extend(x>>8 for x in ss);sh.extend(x&31 for x in ss)
        w=np.concatenate(ws,axis=0)
        layers.append(dict(weights=w,bias=np.array(bs,np.int64),scale=np.array(sc,np.int64),shift=np.array(sh,np.int64)))
        assert mmrs[layer['mmrs'][0]][3]==(0x7f0180 if i==3 else 0xff0000)
    return layers


def forward(layers,q):
    x=np.array([-32,q,18]+[0]*13,np.int64);traces=[]
    for i,l in enumerate(layers):
        v=(l['weights']@x+l['bias'])*l['scale']
        x=np.clip(np.right_shift(v,l['shift']),-128 if i==3 else 0,127 if i==3 else 255)
        traces.append(x.copy())
    return traces


def unpack(row,n):return np.array([(row[i//2]>>(8*(i%2)))&255 for i in range(n)],np.int64)


def main():
    protect();assert json.loads((HERE/'results/mapping_gate.json').read_text())['ok']
    a=decode(STAGE_A/'validated/A4',[16,29,16,16]);b=decode(HERE/'generated/B1_raw',[16,32,16,16])
    for field in ('weights','bias','scale','shift'):
        assert np.array_equal(a[0][field],b[0][field][:29])
    assert not np.any(b[0]['weights'][29:]) and not np.any(b[0]['bias'][29:])
    for field in ('bias','scale','shift'):
        assert np.array_equal(a[1][field],b[1][field])
    assert np.array_equal(a[1]['weights'],b[1]['weights'][:,:29]) and not np.any(b[1]['weights'][:,29:])
    for i in (2,3):
        for f in a[i]:assert np.array_equal(a[i][f],b[i][f])
    lo=np.float32(90).view(np.uint32).item();hi=np.float32(140).view(np.uint32).item()
    counts={};digest=hashlib.sha256();first={};last={}
    for start in range(lo,hi+1,1_000_000):
        bits=np.arange(start,min(start+1_000_000,hi+1),dtype=np.uint32);v=bits.view(np.float32)
        norm=(v/np.float32(140)).astype(np.float32)
        q=np.floor(norm*np.float32(64)+np.float32(.5)).astype(np.int16)
        q2=np.floor((norm+np.float32(1/128))*np.float32(2048)*np.float32(1/32)).astype(np.int16)
        assert np.array_equal(q,q2),'ONNX versus A4 quantization boundary mismatch'
        digest.update(q.astype('<i2').tobytes())
        for code in np.unique(q):
            ix=np.flatnonzero(q==code);c=int(code);counts[c]=counts.get(c,0)+len(ix)
            first.setdefault(c,int(bits[ix[0]]));last[c]=int(bits[ix[-1]])
    assert sorted(counts)==list(range(41,65))
    traces={}
    for q in counts:
        ta,tb=forward(a,q),forward(b,q)
        assert np.array_equal(ta[0],tb[0][:29]) and not np.any(tb[0][29:])
        for i in (1,2,3):assert np.array_equal(ta[i],tb[i])
        traces[q]=ta
    golden=json.loads((STAGE_A/'results/capture/A4.json').read_text(encoding='utf-8'))['points']
    for row in golden:
        q=(row['input'][0]>>8)&255;ta=traces[q]
        for i,(offset,n) in enumerate(((0,29),(15,16),(23,16),(31,4))):
            actual=unpack(row['layer_packed'][offset:],n)
            if i==3:actual=np.where(actual>=128,actual-256,actual)
            assert np.array_equal(ta[i],actual),(row['vin'],i,ta[i].tolist(),actual.tolist())
        out=(ta[3].astype(np.float32)*np.float32(1/64)).astype('<f4').view('<u2').tolist()
        assert out==row['output_bits']
    digest_data={str(q):dict(float32_count=counts[q],first_bits=first[q],last_bits=last[q],
                   layers=[t.tolist() for t in traces[q]]) for q in counts}
    dump(HERE/'results/reachable_input_traces.json',digest_data)
    dump(HERE/'results/host_verification.json',dict(ok=True,all_finite_float32_vin_count=hi-lo+1,
         range=[90,140],unique_input_codes=sorted(counts),input_sequence_sha256=digest.hexdigest(),
         canonical_onnx_input_and_original_A4_formula_exact=True,decoded_active_parameters_exact=True,
         new_channels_zero=True,all_reachable_input_codes_layerwise_exact=True,
         matches_stage_A_real_board_golden_points=len(golden),final_float_bits_exact=True,
         note='Integer decoded-kernel host model is checked against all Stage-A real-board golden traces; no host timing is reported as hardware performance.'))
    print(json.dumps(dict(ok=True,float32_vins=hi-lo+1,input_codes=len(counts),stage_A_board_goldens=len(golden))))


if __name__=='__main__':main()
