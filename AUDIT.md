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
| CGameAIBase::ApplyTriggers | EEex.cpp | 0.98 | check the 2% delta |
| CGameAIBase::SetTrigger | EEex.cpp | 0.99 | check the 1% delta |
| CGameEffectList::Unmarshal | EEex.cpp | 1.00 | valid |
| CMessageSetLastObject::Run | EEex.cpp | 1.00 | valid |
| Infinity_WriteINILine | EEex.cpp | 1.00 | valid |
| fontWrap | EEex.cpp | 1.00 | valid |
| CGameEffect::CheckSave | EEex.cpp (EEex opcodes only) | 0.41 | PT save logic differs |
| CGameEffectUsability::CheckUsability | EEex.cpp | 0.75 | **rewritten for PT**: param2=8 effective alignment (PT 0x3c4fe0, Law/Good globals), PT-only param2=12 (CRE byte +0x87); other modes identical |
| CDerivedStats::GetSpellState / SetSpellState | EEex.cpp | 0.45 / 0.14 | valid: same bit logic on m_spellStates (PT only dropped the bit < 256 guard, which EEex handles) |
| CGameSprite::Damage | EEex.cpp (wrapper) | 0.57 | wrapper only: calls the engine function |
| CScreenMap::OnLButtonDblClk | EEex.cpp | 0.58 | PT differs |
| uiDoFile | EEex.cpp | 0.77 | PT differs |
| uiEventMenuStack | EEex.cpp | 0.39 | PT differs |
| CGameSprite::Hit / Swing (fakeAttackRoll, getAttackChance) | EEex.cpp | 0.56 / 0.68 | attack math differs |
| CVisibilityMap::*, CInfinity::*, CScreenWorld::*, CChitin::Update/WinMain, render | stubs | 0.32..1.00 | phase 4d |

Overrides are only reached when EEex's Lua patches redirect the engine (phase 5); until then the
engine's own PT functions run.
