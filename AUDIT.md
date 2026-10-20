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
| CGameSprite::Hit / Swing (fakeAttackRoll, getAttackChance) | EEex.cpp | 0.56 / 0.68 | attack math differs |
| CVisibilityMap::*, CInfinity::*, CScreenWorld::*, CChitin::Update/WinMain, render | stubs | 0.32..1.00 | phase 4d |

Overrides are only reached when EEex's Lua patches redirect the engine (phase 5); until then the
engine's own PT functions run.
