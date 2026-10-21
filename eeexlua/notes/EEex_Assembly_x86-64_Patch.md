# EEex_Assembly_x86-64_Patch.lua (Torment review)

No patch needed (already loaded and working in game). EEex_Assembly_Patch.lua only dispatches to this file (no labels).

| Label used in the JIT code | PT | Verdict |
|---|---|---|
| Hardcoded_lua_tolstring | 0xe40e0 | unchanged: = BG lua_tolstring 0xd58c0, fdiff 1.000 |
| Hardcoded_lua_getglobal | 0xe4610 | unchanged: = BG 0xd5df0, 1.000 |
| Hardcoded_lua_pushstring | 0xe4350 | unchanged: = BG 0xd5b30, 1.000 |
| Hardcoded_lua_pcallk | 0xe4ef0 | unchanged: = BG 0xd66d0, 1.000 (same 6-argument Lua 5.2 signature) |
| Hardcoded_lua_settop | 0xe3b50 | unchanged: = BG 0xd5330, 1.000 |

No engine structs or offsets.
