import sys; exec(open('pe.py').read())
import numpy as np
def refs(pe,t):
    n,va,vs,ra,rs=pe.text(); a=np.frombuffer(pe.d[ra:ra+rs],dtype=np.uint8)
    # int32 little endian at every offset
    x=(a[:-3].astype(np.int64)|(a[1:-2].astype(np.int64)<<8)|(a[2:-1].astype(np.int64)<<16)|(a[3:].astype(np.int64)<<24))
    x=np.where(x>=2**31,x-2**32,x)
    idx=np.nonzero(np.arange(len(x))+va+4+x==t)[0]
    return [int(i)+ra for i in idx]
for path in sys.argv[1:]:
    pe=PE(path); s=pe.d.find(b'cannot resume non-suspended coroutine')
    sr=pe.rva(s); r=refs(pe,sr)
    fns=sorted({pe.fstart(p) for p in r})
    print(path[-12:],'string refs',[hex(p) for p in r],'funcs',[hex(f) for f in fns])
    for f in fns:
        r2=refs(pe,pe.rva(f)); callers=sorted({pe.fstart(p) for p in r2})
        print('  ',hex(f),'referenced from funcs',[hex(c) for c in callers])
