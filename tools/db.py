import sys,re,collections
exe=open(sys.argv[1],'rb').read()
c=collections.Counter(); miss=[]
for db in sys.argv[2:]:
    for name,pat in re.findall(r'\[([^\]]+)\]\s*\nPattern=([0-9A-F]+)',open(db,encoding='utf-8',errors='ignore').read()):
        if name.startswith('!ExeSwitch') and 'Baldur.exe' not in name: continue
        n=len(re.findall(re.escape(bytes.fromhex(pat)),exe))
        k='1' if n==1 else ('0' if n==0 else 'many'); c[k]+=1
        if n!=1: miss.append((name,n))
print(c)
for m in miss[:400]: print(m)
