# EEex_EngineLua_Patch.lua (Torment review)

No patch needed.

| Line | Hook / label | Verdict | Evidence |
|---|---|---|---|
| 18 | ReplaceCall Hook-OpenIniFile()-_wfopen() | unchanged | PT 0x490051 `call 0x5944a8` (= BG _wfopen 0x50faa0, same thunk bytes); OpenIniFile PT 0x48ffc0 = BG 0x409230, fdiff 1.000 |
| 21 | HookRemoveCall Hook-chReadIniFile()-luaL_loadfilexptr() | unchanged | PT 0x490115 `call 0xe7090` (= BG 0xd8870); same arguments (rcx = g_lua, rdx = FILE* from rax, r8d = 0); the hook adds r9 = chunk name |
| 27 | JITAt chWriteInifile -> EEex::Override_chWriteInifile | unchanged | PT 0x490340 = BG 0x4095b0, fdiff 1.000; file "Baldur.lua" (PT 0x65c6b0), mode "wb", Lua "printIni", as in the override |
| 35 | JITAt EEex_CFuncToPtr(Infinity_WriteINILine) | unchanged | function taken from the Lua global at runtime; reimplementation valid for PT (AUDIT.md, similarity 1.00) |
| 41 | HookAfterCall Hook-dimmInit()-uiLoadFunctions() | unchanged | PT 0x48bb7e `call 0x458710` (= BG 0x3d93f0); next instructions `lea rcx; call` (rax unused) |
| 58 | ForceJump Hook-chReadIniFile()-CheckDoBackupProcessingJmp | unchanged | PT 0x490159 near `je` (6 bytes), same `test ebx, ebx` context |

## Label fixes needed / BG-only features / open questions
None.
