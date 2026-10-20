import struct,re
class PE:
    def __init__(s,path):
        s.d=open(path,'rb').read(); d=s.d
        pe=struct.unpack_from('<I',d,0x3c)[0]; n=struct.unpack_from('<H',d,pe+6)[0]; osz=struct.unpack_from('<H',d,pe+20)[0]
        s.base=struct.unpack_from('<Q',d,pe+24+24)[0]; s.secs=[]
        for i in range(n):
            o=pe+24+osz+i*40; name=d[o:o+8].rstrip(b'\0').decode(); vs,va,rs,ra=struct.unpack_from('<IIII',d,o+8)
            s.secs.append((name,va,vs,ra,rs))
    def rva(s,off):
        for n,va,vs,ra,rs in s.secs:
            if ra<=off<ra+rs: return off-ra+va
    def off(s,rva):
        for n,va,vs,ra,rs in s.secs:
            if va<=rva<va+max(vs,rs): return rva-va+ra
    def text(s): return [x for x in s.secs if x[0]=='.text'][0]
    def riprefs(s,target_rva):
        n,va,vs,ra,rs=s.text(); d=s.d; out=[]
        for i in range(ra,ra+rs-7):
            # disp32 at i+3 for 7-byte REX lea/mov, generic: check any disp32 whose rip-relative target matches for instr end at i+4+k
            pass
        # faster: search all positions p where int32 at p + (p+4) == target (instruction ending right after disp)
        t=target_rva
        for p in range(ra,ra+rs-4):
            disp=struct.unpack_from('<i',d,p)[0]
            if s.rva(p)+4+disp==t: out.append(p)
        return out
    def fstart(s,p):
        while not (s.d[p-1]==0xCC and s.d[p-2]==0xCC): p-=1
        return p
