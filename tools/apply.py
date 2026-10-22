# Apply ported Torment patterns (ported.json) and Unsupported flags to the PSTEE InfinityLoader.db.
import json,re,sys
p=r'E:\Enhanced Edition\EEex-PSTEE\poc\InfinityLoader.db'
db=open(p,encoding='utf-8').read()
ported=json.load(open('ported.json'))
unsupported=sys.argv[1:]
for k,v in ported.items():
    db,n=re.subn(r'(\['+re.escape(k)+r'\]\s*\n)Pattern=[0-9A-F]+(\s*\nOperations=[^\n]*)?', lambda m: m.group(1)+'Pattern='+v, db); print(k,n)
for k in unsupported:
    db,n=re.subn(r'(\['+re.escape(k)+r'\]\s*\n)', lambda m: m.group(1)+'Unsupported=1\n', db,count=1); print(k,'unsupported',n)
open(p,'w',encoding='utf-8',newline='').write(db)
