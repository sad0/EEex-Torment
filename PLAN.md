# EEex-PTEE plan

Target: Planescape: Torment EE v3.2.2.0 (Steam, x64, Lua 5.2). Reference: BG2EE (EEex v1.3.1).

## Findings
- InfinityLoader (upstream binaries) injects into Torment.exe unchanged.
- Torment.exe main object is 0x1910 bytes (BG: 0x1918) -> `Hardcoded_InternalPatchLocation` = `B910190000`.
- Lua coroutine library is stripped from Torment.exe: `lua_resume` absent -> `Unsupported=1`.
- ~57% of the 840 EEex patterns match uniquely as-is; byte-window voting (tools/port.py) ports many more.
- Bubb13 already generated PSTEE struct headers in 2022 (InfinityLoader/LuaBindings-PSTEE), for an older exe.
- PTEE loads UI.MENU outside `dimmInit()` (fn 0x140d10); the uiLoadMenu hook is the call at 0x140ead.
- Torment keeps the BG link order (98.8% of mapped function pairs): used to map functions PST modified.
- Some upstream patterns match uniquely in Torment but at the wrong place (e.g. GetQuickButtons, GetKitMask,
  lua_xmove -> lua_atpanic): unique != correct, every entry was cross-checked (see PATTERNS.md).
- Lua: coroutine lib, lua_resume, lua_xmove absent; libs are opened one by one in fn 0x144420.
- Bindings: 5420/5870 BG fields placed in Torment layouts (666 direct evidence, rest interpolated /
  assumed identical); unproven bytes are opaque `nobinding` padding. Compiled layout == solved layout.
- EEex_Main.lua runs before g_pBaldurChitin is set; engine reads must wait for UI/game activity.
- Windows Defender flags InfinityLoader.exe (Behavior:Win32/DefenseEvasion.A!ml): game + repo folders
  must be excluded.
- tools/gamectl.py drives the game window (screenshot of the game only, clicks, keys) for tests.

## Phases
1. [x] POC: loader + Lua 5.2 provider run EEex_Main.lua in Torment.exe (poc/, loader-only DB).
2. [x] Port all engine patterns: 821 ported, 13 unsupported, full DB loads in-game (PATTERNS.md, tools/).
3. [x] LuaBindings for v3.2.2.0: struct layouts solved from BG2EE types + code evidence (tools/bindings),
       bindings/LuaBindings-PTEE builds LuaBindings.dll; in-game reads OK (party names, HP, XP, gold).
       Bubb's 2022 LuaBindings-PSTEE was an empty skeleton (62 structs, all bytes undefined), not reused.
4. [ ] Port EEex.dll (C++ hooks, EEex-Core-Shared-Files) to PSTEE structs.
5. [ ] Port EEex Lua (77 files, ~24k lines) and drop BG-only features.
6. [ ] WeiDU installer (setup-EEex-PTEE), test on a real playthrough.
