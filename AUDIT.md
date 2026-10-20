# EEex.dll semantic audit for Torment (phase 4b)

## Engine data that differs from BG2EE (PT v3.2.2.0 game data, tools/bifextract.py)
- Effect opcodes (tools/opcodes.py, CGameEffect::DecodeEffect jump tables): BG 0..367, PT 0..383.
  284 opcodes keep the same effect class, 70 differ, 30 are PT-only (347..383). PT maps
  113/118/121/313/338/360 to one shared class (disabled), 125/142/149/150/319 to one class,
  127/218/331/359/377 to the base CGameEffect. Opcodes hooked by EEex.dll: 101, 120, 248, 249, 280,
  342 same class (ApplyEffect identical); 319 shares a class with 125/142/149/150 -> to check.
- STATS.IDS: 23 ids differ (PT reuses 166.. as DMWW slots), 2 BG-only.
- SLOTS.IDS: same indices, different meaning (ITMSLOTS.2DA: slot 9 = TATTOO3, no off-hand).
- RACE.IDS: almost entirely different. CLASS.IDS: PT is a 29-entry subset.
- ACTION.IDS / TRIGGER.IDS: PT adds 51 actions / 11 triggers, a few signatures differ.
- SPLSTATE.IDS: PT adds 17 states. File formats: BG formats except STOR V1.1 (see PLAN.md).

## Engine functions reimplemented by EEex.dll (whole-function similarity BG vs PT)
| Function | EEex code | Similarity | Verdict |
|---|---|---|---|
| CAICondition::Hold | EEex.cpp | 1.00 | reimplementation valid |
| CAICondition::TriggerHolds | EEex.cpp | 1.00 | valid |
| CChitin::SynchronousUpdate | EEex.cpp | 1.00 | valid |
| CGameAIBase::ApplyTriggers | EEex.cpp | 0.98 | valid: only jump-table data bytes differ, code identical |
| CGameAIBase::SetTrigger | EEex.cpp | 0.99 | valid: only jump-table data bytes differ, code identical |
| CGameEffectList::Unmarshal | EEex.cpp | 1.00 | valid |
| CMessageSetLastObject::Run | EEex.cpp | 1.00 | valid |
| Infinity_WriteINILine | EEex.cpp | 1.00 | valid |
| fontWrap | EEex.cpp | 1.00 | valid |
| CGameEffect::CheckSave | EEex.cpp (exported, not installed by EEex's Lua) | 0.41 | **forwards to PT's own CheckSave** (base vtable slot 7, verified = PT 0x1ec460) |
| CGameEffectUsability::CheckUsability | EEex.cpp | 0.75 | **rewritten for PT**: param2=8 effective alignment (PT 0x3c4fe0, Law/Good globals), PT-only param2=12 (CRE byte +0x87); other modes identical |
| CDerivedStats::GetSpellState / SetSpellState | EEex.cpp | 0.45 / 0.14 | valid: same bit logic on m_spellStates (PT only dropped the bit < 256 guard, which EEex handles) |
| CGameSprite::Damage | EEex.cpp (wrapper) | 0.57 | valid: wrapper calling the engine's own Damage + Lua hook (left-hand flag patched: no off-hand in PT) |
| CGameText::Render | EEex.cpp | 0.11 | PT renderer is a different routine; EEex's BG fixes do not apply: **not installed on PT** (body logs once) |
| CScreenMap::OnLButtonDblClk | EEex.cpp (vtable slot 28) | n/a | valid: PT's slot function (0x33b770) is exactly `pActiveEngine->OnLeftPanelButtonClick(0)`, as the override (+ EEex Lua hook); OnLeftPanelButtonClick(0) = back to world in both |
| uiDoFile | EEex.cpp | 0.77 | **rewritten for PT**: loads the CResText string (+0x58) with its length, releases with dimmDump |
| uiEventMenuStack | EEex.cpp | 0.39 | **rewritten for PT**: keyboard/controller navigation first (PT 0x459ff0), overlay swallows, A-button skip, PT pass-through filter; EEex capture fix kept |
| CGameSprite::Hit (fakeAttackRoll, getAttackChance, adjustFakeAttackRoll) | EEex.cpp | 0.56 | **ported to PT**: segment-by-segment diff of PT 0x4147b0 vs BG; PT adds NTOKEN (+3 needed) and Dead_Truce (+4 needed) threshold modifiers, Fist of Iron (+3 roll, opcode 382), skips attacks of opportunity and the state-bit-22 invisibility in Torment mode; crit hit/miss, luck, AC, hit bonus, hand, invisibility, range, hated race, protections identical (BG-only side effects are not simulated by EEex) |
| CDerivedStats::GetAtOffset (extended stats) | Lua hook | n/a | valid: PT accepts the same engine stat range 1..202 (bound 0xc9), FIRST_EXTENDED_STAT_ID 203 stays |
| CVisibilityMap::*, CInfinity::*, CScreenWorld::*, CChitin::Update/WinMain, render | stubs | 0.32..1.00 | phase 4d |

| Projectile start positions (CProjectileBAM / SpellHit / TravelDoor) | EEex.cpp | 0.78 / 0.69 / 0.94 | valid: start/target/distance logic identical in PT's Fire functions (differences: DetermineHeight call, which EEex already uses; jump-table data with the same object-type mapping; a sound channel) |
| IsDefaultAttackCursor | EEex.cpp | n/a | logic valid (EA cut-offs from engine constants, EA.IDS identical); the cursor ids tested by B3AttackInfo.lua (12, 101) are phase 5 |
| Fix_Hook_ImplementWSPECIALSpeedColumn | EEex.cpp | n/a | **disabled for PT**: Torment's WSPECIAL.2DA has no SPEED column |
| Hand bonus feedback (+Right / +Left) | EEex.cpp | n/a | fixed: m_hitBonusesRight/Left are CStrings (engine appends "(text)"), upstream formatted them with %d |
| Engine constants in identical code (trigger ids in Hold/ApplyTriggers/SetTrigger/SetLastObject, opcode 187, colour 0xBED7D7, dead-state mask 0xFC0) | EEex.cpp | 1.00 | valid: same values in PT's own code |

## In-game test of the exports (bindings/test/EEex_Main.lua, save ptee-test)
All 19 standalone exports run without error on Torment: CanAttackWithLeftHand, GetWeaponHitChance (35%,
full PT breakdown), FakeAttackRoll, IsImmuneToWeapon, GetExtendedStatValue, GetHighestRefreshRate,
GetMicroseconds, Get/SetINIString (round trip), GetTextWidthHeight, IsDefaultAttackCursor,
IsMarshallingCopy, IsPlayerScript, ShouldEffectBypassOp120, MatchObject, FormatPointerAsEngine, DeepCopy.
The other exports need the phase-5 Lua layer (menus/templates, sliced rects, profiler, Uncap FPS).

Overrides are only reached when EEex's Lua patches redirect the engine (phase 5); until then the
engine's own PT functions run.
