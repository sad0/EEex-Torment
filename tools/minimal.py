# Build a loader-only pattern DB for the POC: keep Lua/tolua/SDL/Hardcoded entries, drop EEex engine patterns.
import re
src=r'E:\Enhanced Edition\EEex-PTEE\poc\InfinityLoader.db'; dst=r'E:\Enhanced Edition\EEex-PTEE\poc\InfinityLoader.minimal.db'
txt=open(src,encoding='utf-8').read()
blocks=re.split(r'\n(?=\[)',txt)
keep=[]; 
for b in blocks:
    m=re.match(r'\[([^\]]+)\]',b)
    if not m: continue
    n=m.group(1)
    if re.match(r'(Hardcoded_|lua|tolua|SDL_)',n): keep.append(b.strip()+'\n')
open(dst,'w',encoding='utf-8',newline='').write('\n'.join(keep)); print(len(keep),'kept of',len(blocks))
