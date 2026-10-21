# EEex_ReplaceLua.lua (Torment review)

Only runs when `[General].LuaPatchMode=REPLACE_INTERNAL_WITH_EXTERNAL` (EEex_EarlyMain.lua); the dev install uses
INTERNAL. Patch: `patches/EEex_ReplaceLua.py` (2 changes).

| Label | Verdict | Evidence |
|---|---|---|
| bootstrapLua (JITAt -> EEex::Override_bootstrapLua) | unchanged | PT 0x144420 = BG 0x1366e0, fdiff 1.000 (109/109): the reimplementation matches Torment |
| 85 redirected lua_* / luaL_* / luaopen_* labels | unchanged | every PT label is a function start with a body identical to BG (fdiff 1.000). Kind-B labels checked against their BG call targets: lua_error 0xe5430, lua_len 0xe5520, lua_rawlen 0xe41a0, lua_setglobal 0xe4920, lua_typename 0xe3d30; luaopen_table 0xebad0 = BG 0xddab0 |
| lua_resume | **patched** (redirect removed) | label Unsupported in Torment: coroutine library stripped; EEex_Label() would abort the whole file. Only BG caller = coroutine library (BG 0xdbe80) |
| lua_xmove | **patched** (redirect removed) | label Unsupported: no standalone body. BG callers = coroutine library + debug library (BG 0xe34a0 / 0xe3d80 -> PT 0xf14c0 / 0xf1dc0 inline it); luaopen_debug is redirected anyway |
| Data-LUA_REGISTRYINDEX (Write32 -10000 at every match) | unchanged | pattern `BA D8 B9 F0 FF` (mov edx, -1001000): BG 95 / PT 99 matches, all on instruction boundaries. The 95 map to the BG sites (same count per function); the 4 extra PT sites are Torment code using the registry the same way (PT 0x440706: one more luaL_ref; 0x450aa4 / 0x45364a / 0x455d3b: lua_rawgeti). Other encodings of -1001000 (cmp / mov ecx) exist only inside the Lua library in both exes (same set) |

## Label fixes needed
None.

## BG-only features
lua_resume / lua_xmove redirection (absent from Torment.exe): skipped.
