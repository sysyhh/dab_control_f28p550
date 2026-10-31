"""Independent fixed-B1 register write set, retaining full immutable MMR tables."""
import re
from common_c import *
from verify_mmr_host import SET


def patch(s):
    old=body(s,'write_configMMR')
    dynamic=old[old.index('    // Part 2:'):]
    new='\n    volatile uint32_t *mmrs = (uint32_t *) (TINIE_BASE_ADDR + TINIE_MMR_OFS);\n'
    new+='    /* Fixed B1-only write set, exactly the native NNC explicit FC register set. */\n'
    new+=''.join(f'    mmrs[{r} * 2] = layer->mmrs[{r}];\n' for r in SET)
    return replace_once(s,old,new+dynamic)


def main():
    protect();source=(BASE/'dab_tinie_c28.c').read_text(encoding='utf-8')
    patched=patch(source);dest=HERE/'candidates/static_mmr_driver.c';dest.write_text(patched,encoding='utf-8')
    mmr=json.loads((HERE/'results/mmr_data.json').read_text())
    assert all(len(r['full'])==33 for r in mmr['layers'])
    # Reuse actual full decoder harness, adding actual candidate function body.
    host=(HERE/'host/actual_decoder.c').read_text()
    candidate=body(patched,'write_configMMR')
    candidate=re.sub(r'mmrs\[([^\]\n]+)\]\s*=\s*(.*?);',r'writeMmr(\1,\2);',candidate,flags=re.S)
    pos=host.index('static const uint32_t full')
    host=host[:pos]+'static void write_static(TINIE_layer_t*layer){'+candidate+'}\n'+host[pos:]
    host=host.replace('l.num_mmrs=6;l.mmrs=packed[layer];','l.num_mmrs=33;l.mmrs=full[layer];').replace('write_configMMR(&l);assert(writes==13);','write_static(&l);assert(writes==13);')
    src=HERE/'host/static_mmr.c';src.write_text(host,encoding='utf-8');exe=src.with_suffix('.exe')
    run([A/'host_tools/ziglang/zig.exe','cc',src,'-o',exe,'-O2','-Wno-pointer-to-int-cast'],cwd=HERE/'host')
    message=run([exe]).strip()
    dump(HERE/'results/static_mmr_host.json',dict(ok=True,dirty_four_layer_chains=1000,actual_C_body_compiled=True,
      driver_sha256=sha(dest),registers=list(SET),dynamic_registers=[4,29,30],writes_each_layer=13,
      admission='Only frozen B1 full 33-word tables, no residual FC; no cross-layer value caching. All live fields reinitialized every task.',
      motivation='native compressed decoder is slower; remove decoding while preserving the exact same write set',message=message))
    print('static B1 MMR actual C host PASS');protect()


if __name__=='__main__':main()
