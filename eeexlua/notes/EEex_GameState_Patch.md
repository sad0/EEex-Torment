# EEex_GameState_Patch.lua (Torment)

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-SDL_main()-CLUAConsole::LuaInit()` (AfterCall) | unchanged | PT 0x144eb7 `call 0x226220` (= BG CLUAConsole::LuaInit 0x202c90, fmap sig), same preceding block ("Program Options" INI read, flag store). No register read. |
| `Hook-CInfGame::DestroyGame()-LastCall` (AfterCall) | unchanged | PT 0x2d861d `call __security_check_cookie` (PT 0x57fd90) in PT 0x2d7600 (fmap of BG 0x272a20), epilogue follows as in BG. No register read. |
| `Hook-CInfGame::Unmarshal()-AfterGlobalVariablesUnmarshalled` (BeforeCall) | unchanged | PT 0x2fa574 `call 0x2de900` (BG 0x2799e0, fmap sig, identical prologue, reads rcx only) right after the global-variable loop (PT 0x2fa55f / BG 0x2935ab CVariableHash add). The hook preserves rcx (loaded from rsi in Torment). |
| `Hook-dimmInit-uiDoFile()` (BeforeAndAfterCall) | unchanged | PT 0x48bb8a `call uiDoFile` (PT 0x456d60, reads rcx only) with rcx = "includes" (PT 0x65c488). After the call Torment destroys a CString and returns 1. |
| `Hook-CChitin::ShutDown()-FirstInstruction` (BeforeRestore 0,6,6) | unchanged | PT 0x4a5fd0: `push rsi; push r14; push r15` = 6 bytes as in BG (each 2 bytes), rcx / rdx / r8 / r9 saved and restored. |

## Open questions
- BG dimmInit loads UI.MENU right after `uiDoFile("includes")` (so EEex's AfterIncludes listeners run before UI.MENU); Torment's dimmInit returns right after includes and loads its menus elsewhere. EEex itself registers no AfterIncludes listener (only a BeforeIncludes one, EEex_OptionsLate.lua); a third-party AfterIncludes listener that expects to run before UI.MENU was not checked.
