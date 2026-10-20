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
- Bindings: 5640/5870 BG fields placed in Torment layouts (2339 direct evidence since the tracker uses
  EEex's BG symbol names as typed roots, + 109 hand-verified); unproven bytes are opaque `nobinding`
  padding. Compiled layout == solved layout.
- EEex_Main.lua runs before g_pBaldurChitin is set; engine reads must wait for UI/game activity.
- Windows Defender flags InfinityLoader.exe (Behavior:Win32/DefenseEvasion.A!ml): game + repo folders
  must be excluded.
- tools/gamectl.py drives the game window (screenshot of the game only, clicks, keys) for tests.
- CGameSpriteEquipment is pointer-based in PTEE: `CItem** m_items` (slot count from ITMSLOTS.2DA), 0x20 bytes,
  at CGameSprite+0xfb8. Slot indices match BG (FIST 10, SPECIAL 34, WEAPONS 35-38) except slot 9 = TATTOO3:
  PTEE has no off-hand slot (EEex.cpp left-hand logic patched by eeexdll/patch_sources.py).
- CDerivedStatsTemplate: PTEE inserts 12 bytes after m_nCHR (0x5a) and drops BG 0x27c (m_nClassTypeOverride*):
  +12 from m_nXPValue, +8 from 0x280. CMessageAddEffect has no m_CommType (manual_types_pt.txt).
- EEex's v2.6.6.0 extra pattern DB matches neither our BG exe nor Torment: functions located by name
  (function_names.db -> tools/bgnames.py -> ptnames.json), written to poc/extra_pattern_dbs/ptee.db.
- Dev env skips the startup movies (PTEE_SkipIntro.lua, labels in ptee.db).

## Phases
1. [x] POC: loader + Lua 5.2 provider run EEex_Main.lua in Torment.exe (poc/, loader-only DB).
2. [x] Port all engine patterns: 821 ported, 13 unsupported, full DB loads in-game (PATTERNS.md, tools/).
3. [x] LuaBindings for v3.2.2.0: struct layouts solved from BG2EE types + code evidence (tools/bindings),
       bindings/LuaBindings-PTEE builds LuaBindings.dll; in-game reads OK (party names, HP, XP, gold).
       Bubb's 2022 LuaBindings-PSTEE was an empty skeleton (62 structs, all bytes undefined), not reused.
4. [ ] Port EEex.dll (C++ hooks, EEex-Core-Shared-Files) to PSTEE structs.
       Done: eeexdll/ builds EEex.dll, loads in-game, EEex.* struct functions tested (equipment, left hand).
       Not ported (stubs log once, ptee_stubs.cpp): Uncap FPS, visibility map, engine reimplementations,
       debug.cpp; CGameSprite::MakeLocal pattern; function_names.db (profiler names).
       Field audit (tools/bindings/audit*.py, strict header build): 274/645 fields used by EEex.dll proven.
       Still unproven: CGameAIBase trigger lists/scripts, some CGameSprite/CDerivedStats/CChitin fields,
       UI/font structs (slicedRect, font_t, uiItem: phase 5 menus), CGameAreaClairvoyanceEntry (stubbed).
   Phase 4 completion checklist (John: 100%, zero blind spots):
   - [ ] 4a Fields: every bindings field proven (evidence / manual / span) or removed; coverage report
   - [ ] 4b Semantic audit of every EEex.dll function vs the PT engine; in-game test of every export
   - [ ] 4c 13 Unsupported patterns: PT alternative or proven absence
   - [ ] 4d Port stubbed code: Uncap FPS, visibility map, engine reimplementations, debug.cpp,
         CGameSprite::MakeLocal, function_names.db, extra-DB menu hooks
5. [ ] Port EEex Lua (77 files, ~24k lines) and drop BG-only features.
6. [ ] WeiDU installer (setup-EEex-PTEE), test on a real playthrough.
