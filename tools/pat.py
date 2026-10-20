import sys,re
exe=open(sys.argv[1],'rb').read()
ini=open(sys.argv[2],encoding='utf-8',errors='ignore').read()
for name,pat in re.findall(r'\[(Hardcoded_[^\]]+)\]\s*Pattern=([0-9A-F?]+)',ini):
    rx=re.escape(bytes.fromhex(pat))
    n=len(re.findall(rx,exe))
    print(f"{name:40} {n} hits")
