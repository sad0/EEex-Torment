# EEex_ReplaceLua.lua (run by EEex_EarlyMain.lua only when [General].LuaPatchMode=REPLACE_INTERNAL_WITH_EXTERNAL).
# Torment.exe has no lua_resume and no standalone lua_xmove (pattern DB: Unsupported=1): the coroutine library is
# stripped and the debug library inlines xmove. EEex_Label() would raise "Label not defined" and abort the whole
# file. In BG2EE their only callers are the coroutine library (BG 0xdbe80) and the debug library (BG 0xe34a0 /
# 0xe3d80 -> PT 0xf14c0 / 0xf1dc0, inlined), and luaopen_debug is itself redirected: nothing to redirect.
# All 85 other redirected functions: identical bodies BG vs PT (tools/fdiff.py ratio 1.000), function starts.
PATCHES = [
    ('	redirectLuaProc("lua_resume")\n',
     '	-- redirectLuaProc("lua_resume") -- EEex-PSTEE: absent from Torment.exe (coroutine library stripped)\n'),
    ('	redirectLuaProc("lua_xmove")\n',
     '	-- redirectLuaProc("lua_xmove") -- EEex-PSTEE: absent from Torment.exe (inlined in the debug library, which is redirected)\n'),
]
