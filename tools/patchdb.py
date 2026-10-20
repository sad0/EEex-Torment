import re,sys
T=open(r'C:\Users\jnthn\Tools\gproj\Torment.exe','rb').read()
def uniq(a):
    for L in range(8,64):
        if T.count(T[a:a+L])==1: return T[a:a+L].hex().upper()
new={'Hardcoded_lua_getfield':0xe3ad0,'Hardcoded_lua_rawlen':0xe35a0,'Hardcoded_lua_setglobal':0xe3d20,'Hardcoded_tolua_endmodule':0x1206d0}
src,dst=sys.argv[1],sys.argv[2]
db=open(src,encoding='utf-8').read()
for k,a in new.items():
    db,n=re.subn(r'(\['+re.escape(k)+r'\]\s*\n)Pattern=[0-9A-F]+(\s*\nOperations=[^\n]+)?', lambda m: m.group(1)+'Pattern='+uniq(a), db)
    print(k,n,uniq(a))
open(dst,'w',encoding='utf-8',newline='').write(db)
