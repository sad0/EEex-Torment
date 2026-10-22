# Port InfinityLoader.db patterns from BG2EE Baldur.exe to Torment.exe by byte-window voting.
import re,collections,struct,sys,json
B=open(r'C:\Users\jnthn\Tools\gproj\Baldur_bg2ee.exe','rb').read()
T=open(r'C:\Users\jnthn\Tools\gproj\Torment.exe','rb').read()
dbs=[r'E:\Enhanced Edition\EEex-PSTEE\ref\EEex\EEex\loader\InfinityLoader.db',r'E:\Enhanced Edition\EEex-PSTEE\ref\EEex\EEex\loader\v2.7.3.0\pattern_dbs\v2.7.3.0.db']
entries={}
for d in dbs:
    for name,pat,ops in re.findall(r'\[([^\]]+)\]\s*\nPattern=([0-9A-F]+)(?:\s*\nOperations=([^\n]*))?',open(d,encoding='utf-8').read()):
        entries.setdefault(name,(pat,ops))
def resolve(buf,pat,ops):
    hs=[h.start() for h in re.finditer(re.escape(bytes.fromhex(pat)),buf)]
    if len(hs)!=1: return None
    a=hs[0]; st=[]
    for op in [o.strip() for o in ops.split(',')] if ops else []:
        if op.startswith('ADD '): a+=int(op[4:])
        elif op=='PUSH': st.append(a)
        elif op=='READ DWORD': a=struct.unpack('<i',buf[a:a+4])[0]
        elif op=='ADD': a+=st.pop()
        else: return None
    return a
def locate(a,span=96):
    v=collections.Counter()
    for off in range(-span,span,2):
        for L in (10,12,16):
            w=B[a+off:a+off+L]
            if len(w)<L: continue
            hs=[x.start() for x in re.finditer(re.escape(w),T)]
            if len(hs)==1: v[hs[0]-off]+=1
    return v.most_common(2)
def uniq(a):
    for L in range(8,64):
        if T.count(T[a:a+L])==1: return T[a:a+L].hex().upper()
res={}
for n in sys.argv[1:]:
    pat,ops=entries[n]
    a=resolve(B,pat,ops)
    if a is None: print(n,'BG2 unresolved'); continue
    c=locate(a)
    conf = c and c[0][1]>=6 and (len(c)<2 or c[0][1]>=3*c[1][1])
    print(f'{n:30} votes={[(hex(x),v) for x,v in c]} {"OK" if conf else "WEAK"}')
    if conf: res[n]=uniq(c[0][0])
json.dump(res,open('ported.json','w'),indent=1)
