T=open(r'C:\Users\jnthn\Tools\gproj\Torment.exe','rb').read()
def uniq(a):
    for L in range(8,64):
        if T.count(T[a:a+L])==1: return T[a:a+L].hex().upper()
e=[('CSound::Construct',0x4933e0,None),('CTlkTable::Fetch',0x49fc40,None),('OpenIniFile',0x48f3c0,None),
   ('lang',0x489d2e-8,'ADD 8, PUSH, READ DWORD, ADD, ADD 4'),('Hook-CChitin::ShutDown()-FirstInstruction',0x4a53d0,None),
   ('Hook-OpenIniFile()-_wfopen()',0x48f451,None)]
out='\n;---------------------------------\n;-- EEex-PSTEE: Torment.exe switch --\n;---------------------------------\n\n'
for n,a,ops in e:
    out+=f'[!ExeSwitch-Torment.exe-{n}]\nPattern={uniq(a)}\n'+(f'Operations={ops}\n' if ops else '')+'\n'
out+='; TODO(EEex-PSTEE): PSTEE dimmInit() differs from BG; real hook location not identified yet.\n[!ExeSwitch-Torment.exe-Hook-dimmInit()-uiLoadMenu()]\nPattern=DEADBEEFDEADBEEFDEADBEEF\n'
p=r'E:\Enhanced Edition\EEex-PSTEE\poc\InfinityLoader.db'
open(p,'a',encoding='utf-8',newline='').write(out); print(out)
