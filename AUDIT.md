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
| CVisibilityMap::* + CGameSprite::CheckIfVisible / SetVisualRange + CGameArea::AddClairvoyanceObject (FoW-clearing cap, visibility_map.cpp) | EEex_Fix_Patch.lua | 0.99..1.00 (tools/fdiff.py, whole bodies) | **ported**: Torment's vismap is BG's (TraverseTree, ClimbWall, BuildTree, PrivateAddCharacter, GetTileCode identical; only m_nWidth moved to +8 and BG's m_nMapSize bounds checks are gone; readers mask 0x7FFF like BG; SSToVS table identical; no Torment-only caller). One constant differs: the sprite update spreading mask (BG 1, PT 7) gives m_canBeSeen = 32 in Torment, EEex hard-coded 8 -> every creature blinked; now `PTEE::CanBeSeenTicks()` (ptee.db label). In game: fog clears normally, no blinking, m_canBeSeen 24..32 as vanilla |
| CGameArea::GetNearest (both overloads), AdjustTarget, CAIGroup::GroupSetTarget, CGameArea::GetTintColor, CVidPalette::RealizeResource3d (engine_reimplementations.cpp, debug.cpp) | none | 0.72..1.00 | **not installed by EEex**: no Lua patch jumps to them, all `$nobinding`: unreachable upstream code, kept out of the build (ptee_stubs.cpp) |
| MatchObject (EEex_CheckMatch) | EEex.cpp | n/a | **patched**: Torment's target searches (GetNearest, GetAllInRange, ~40 sites) also require a Torment-only activity flag (CGameSprite +0x3910, cleared during spell cinematics such as Abyssal Fury / Celestial Host): `PTEE::IsActiveCinematic` |
| CInfinity::*, CScreenWorld::*, CChitin::Update/WinMain, render (Uncap FPS) | stubs | 0.43..1.00 | phase 4d |

| Projectile start positions (CProjectileBAM / SpellHit / TravelDoor) | EEex.cpp | 0.78 / 0.69 / 0.94 | valid: start/target/distance logic identical in PT's Fire functions (differences: DetermineHeight call, which EEex already uses; jump-table data with the same object-type mapping; a sound channel) |
| IsDefaultAttackCursor | EEex.cpp | n/a | logic valid (EA cut-offs from engine constants, EA.IDS identical); the cursor ids tested by B3AttackInfo.lua (12, 101) are phase 5 |
| Fix_Hook_ImplementWSPECIALSpeedColumn | EEex.cpp | n/a | **disabled for PT**: Torment's WSPECIAL.2DA has no SPEED column |
| Hand bonus feedback (+Right / +Left) | EEex.cpp | n/a | fixed: m_hitBonusesRight/Left are CStrings (engine appends "(text)"), upstream formatted them with %d |
| Engine constants in identical code (trigger ids in Hold/ApplyTriggers/SetTrigger/SetLastObject, opcode 187, colour 0xBED7D7, dead-state mask 0xFC0) | EEex.cpp | 1.00 | valid: same values in PT's own code |

## Virtual slot order (tools/bindings/vtsolve.py + vtheader.py)
Torment's vtables differ from BG2EE: CGameObject drops SetVertListType (slot 9, all later slots -1),
CGameAIBase adds 2 slots after ClearActions, CProjectile adds one, CGameAnimationType / CVidCell /
CInfToolTip insert slots, etc. The generated headers used BG order, so every `virtual_*` call past a
changed slot hit the wrong function. Now:
- BG vtable per class: constructor store, ctor/dtor named in bgnames, or the .rdata vtable whose slots
  carry the header method names (own override required, <=20% name contradictions, unique best);
- PT vtable: constructor counterpart, aligned LEA sites, or slot-content match;
- slot map: same function (fmap) / same body, equal gaps between anchors, removed slots, destructor
  slot 0, inherited prefix = base map; consensus per introducing class across all solved classes;
- check: 213/216 typed virtual calls in aligned BG/PT code agree (3 single-vote mispairings verified).
Header: 710 vtbl structs in PT order (72 changed; PT-only slots = `ptee_slot_N`, removed slots dropped),
65 unproven classes keep BG order renamed `ptee_unproven_*` (not callable). Of the 305 classes in
EEex.dll's header, 7 are unproven and unused (CException, CFileException, CTimer; Steam interfaces kept
as SDK ABI: same interface versions).

## In-game test of the exports (bindings/test/EEex_Main.lua, save ptee-test)
All 19 standalone exports run without error on Torment: CanAttackWithLeftHand, GetWeaponHitChance (35%,
full PT breakdown), FakeAttackRoll, IsImmuneToWeapon, GetExtendedStatValue, GetHighestRefreshRate,
GetMicroseconds, Get/SetINIString (round trip), GetTextWidthHeight, IsDefaultAttackCursor,
IsMarshallingCopy, IsPlayerScript, ShouldEffectBypassOp120, MatchObject, FormatPointerAsEngine, DeepCopy.
MatchObject finds Morte (nearest party member, match chunk ran 20 times over the area's vertical list)
once the sprites are placed in the area. Virtual calls through the bindings return engine values
(GetObjectType 0x31 = SPRITE, GetVisualRange 544, GetAIType = sprite + 0x30, GetAboveGround 1).
The other exports need the phase-5 Lua layer (menus/templates, sliced rects, profiler, Uncap FPS).

Overrides are only reached when EEex's Lua patches redirect the engine (phase 5); until then the
engine's own PT functions run.

## Proof hardening (phase 4d)
- Packed structs: BG sizeof bounds the alignment (CAreaVariable/CVariable 84, SDL text events 44/52,
  ARE static/sound/rest entries): the header had them 4 bytes too large.
- BG function names: bgnames.py snapped 61 symbols onto the wrong function; bgnames_merge.py keeps
  EEex's names only where three consecutive anchors agree. Re-run of the field tracker: no proven field
  moved, +45 proven.
- Single-function evidence is a candidate only (coverage.py): CGameArea.INIFile had been placed at
  0x1088 from one mispaired access; Torment has two CMemINI there (0x1080 = INIFile, 0x10c8 Torment-only).
  Fields EEex uses that fell below the bar were re-proven by hand (manual_fields.json): CChitin
  bEngineActive, CBaldurChitin m_cTlkTable, CProjectileFall side move, uiItem.edit, uiMenu ha/va,
  CAIIdList / CGameAreaClairvoyanceEntry / CWeaponIdentification (identical code), CDerivedStats
  m_disabledSpellTypes = 0xb68 and **no m_disableSpells in Torment** (op145 has no "all spells" case):
  EEex's spell-disable change detection compares the three type flags only.

## Uncap FPS (uncap_fps.cpp, ported; in-game test: smooth, edge/drag scroll, zoom, local map, dialog OK)
Torment differences carried into EEex's reimplementations (eeexdll/patch_sources.py, ptee_engine.hpp):
- WinMain: SDL_SetHint("SDL_WINDOWS_NO_CLOSE_ON_ALT_F4", "1"); Maximum Frame Rate default 40, valid
  10..90 (else 40); no frame-time log. Update: Lua stack emptied after the leak dump.
- AdjustViewPosition: speed = scroll speed x (15 - m_nScrollDelay) / 15 / (MAXZOOM_OUT + 1 - zoom), no
  resolution factor; no movement in Torment mode while CScreenWorld::m_scrollLockId != -1.
- FitViewPosition: rewritten from PT 0x304c20 (black space also while auto-zooming and then no
  sidebar/actionbar margins; Torment-mode bottom margin = WORLD_ACTIONBAR_LEFT[_TABLET] ("Use Touch
  Actionbar", CGameOptions+0x280); scroll-lock keeps the cursor; centered axes drop their scroll direction).
- ZoomToMap: Torment mode fits into AREA_MAP_TARGET (Infinity_GetAreaScreen); "Disable Area Map Zoom"
  (CGameOptions+0x274, inverted) replaces m_bAreaMapZoom. CInfinity::SetZoom has a third argument
  (bForce, "Zoom Lock"): header signature changed, EEex passes false like vanilla.
- EndDialog: "Zoom Lock" re-disables zooming; UI reset (pop WORLD_DIALOG, push WORLD_ACTIONBAR) unless the
  store screen is active, without the WORLD_DIALOG / JOURNAL checks.
- uiDrawMenuStack: menus drawn in Torment's UI rect (PT 0x4a3180, CChitin+0x1f4 inset); tooltip switched
  off below the delay. Middle-mouse drag: deltas converted window -> screen first (CVidMode 0x4a7fe0).
- SetScrollDest: no clamping while a spell cinematic drives the camera (CInfinity+0x45c).
- RenderTexture: no grey tone flag. Scroll: no m_nScrollAttempts (absent).
- Identical: SynchronousUpdate, RenderZoomed, StartScroll, SetScreenShake, TransitionMenu, DrawReadPixels,
  CenterViewPort, ResetZoom (but the option), screen shake blocks (moved by Torment into PT 0x3078c0 /
  0x307a50 helpers, same code), transition fade, edge-scroll and deactivate hook sites.
- Lua patch (phase 5): three hook sites have another instruction layout in Torment
  (bindings/test/make_uncap_test.py): middle-mouse `je` is short (restore 7), screen-shake post `jne` is
  near (restore 0), OnActivation ends with a call (HookAfterCall, pArea in rdi). EEex's AI-speed option
  default must be Torment's 40, not 30.

## Pattern labels and signatures (tools/labelcheck.py, tools/argcheck.py)
- Two Torment labels pointed at the wrong function (the upstream pattern also matched elsewhere):
  CChitin::ProcessEvents (now 0x4a5100) and eventMenu (now 0x4525f0); 392 other labels agree with the
  function map. The 167 others (leaf functions without .pdata, data) were checked by tools/datacheck.py:
  identical code, or the BG callers' Torment counterparts call the label (functions Torment changed:
  Draw*, GetAtOffset, GetSpellState, ...), or the aligned RIP references load the label (data), or an
  independent derivation agrees (VFTables = vtmap.json); SetCurrAction()-LastCall is the known phase-5 case.
- Argument registers read by every bound engine function, BG vs PT: Torment adds or drops a parameter in
  CInfinity::SetZoom (fixed), CAIObjectType::GetShare (+r9), CGameAIBase::GetTargetShare (+rdx),
  GetTargetShareType (+r8), CGameSprite::ReadyOffInternalList (+rdx), CProjectile::DecodeProjectile (+r8),
  CVidFont::GetStringHeight / GetStringLength (+r9b), CAIScript::Construct(CResRef,int) (no int). The
  Torment signatures are in bindings/in/make_manual_types_pt.py (manual_types_pt.txt). EEex.dll only builds
  CAIScripts (op 82 / screen effects): patched to PTEE::NewScript(res, bPlayerScript), which re-reads the
  script with CAIScript::Read(res, 1) (PT 0x12d240) for player scripts. Lua callers are phase 5.

## Menu hooks of the version extra DB (EEex_Menu_Patch.lua, phase 5 notes)
Located by context in Torment (tools/port_extra.py): OnResizeWindow()-B3Scale (call SDL_GL_GetDrawableSize
after SCREENWIDTH/HEIGHT, PT 0x4a41af), drawItem()-AfterEnabledCheck (PT 0x44eb2b), -CheckScrollbarContentHeight
(PT 0x450db3), -FixForcedScrollbarDivideByZero2 (PT 0x451199, same 11 restored bytes). Torment's drawItem keeps
the uiItem in r13 (BG r15): every drawItem hook's assembly must use r13, and CheckScrollbarContentHeight is a
short `jg` (content taller than the item) where BG has a near `jle`: success/fail paths swap.

## Phase 5: EEex Lua (eeexlua/)
Upstream Lua is copied and patched by eeexlua/build.py (eeexlua/patches/<file>.py, one review note per file in
eeexlua/notes/). Every hook site of the 188 (tools/luahooks.py) was compared BG/Torment (registers, frame slots,
overwritten bytes, relocatable restore bytes, call targets). Main Torment differences found:
- Wrong labels fixed: CGameEffectDamage::ApplyEffect()-OnDone (was in CGameEffectDisintegrate), ForceSpellPoint
  DecodeProjectile RetPtr (+2). tools/labelcheck.py now also checks Hook- labels; all 54 RetPtr labels follow a call.
- Restore sizes: CVisibilityMap::Destruct prologue is 6 bytes (push rsi; sub rsp,0x20), the phase-4d vismap test
  restored 5; ExecuteAction default case restores a RIP-relative lea (not copyable); B3Invis Render restored a jump target.
- Frames: CDerivedStats::GetAtOffset has a 0x38 frame in Torment (BG none): the extended-stat early return must pop it.
- Triggers: EEex's 0x410D..0x4110 are real Torment triggers (ExtraProficiency*, LastPersonTalkedTo): EEex's moved
  to 0x4112..0x4115 (eeexlua/src/patch/TRIGGER.IDS). Actions 472+ / objects 115+ are free.
- op146: Torment already uses `special` != 0 (ForceSpellRESNoFeedback; vanilla data: special 0 x97, 1 x1 IGARM): EEex's
  SpellNoDec switch moved to special bit 1 (value 2) in Torment (owner decision), tested in game (action 191 started).
- CProjectile::AddEffect is virtual in Torment (Area / BAM overrides): all three bodies hooked.
- Struct sizes matter for arrays: uiMenu is 0x98 in Torment (menus memset 0x9800, parser imul 0x98), BG 0x70; the
  interpolated 0x78 broke EngineGlobals.menus. Array element types used by EEex are now size-proven.
- Fields proven for the Lua: CAbilityId / CButtonData (operator= identical), uiColumn, CInfGame keymap (500 entries,
  flags at 0xc350), CChitin cMousePosition 0xfd0 / bPointerUpdated 0xfcc (Torment moved bInTimer/m_AIStale before
  them: ptlayout keeps hand-proven members out of BG order), CInfButtonArray m_nSelectedButton, uiMenu tail fields.
- Options: AI speed option default 40, range 10..90 (Torment's WinMain).
- Projectile decode sources: Torment's spell actions (Spell/SpellNoDec, SpellPoint/SpellPointNoDec, ForceSpell family,
  ForceSpellPoint family) run Torment-only handlers that decode their projectile themselves: their 4 return
  addresses are ptee.db labels mapped to the BG sources. 25 more decode calls live in PST-only projectile classes
  (PT 0x25d..0x290) and op handler 0x1e5ba0: no BG counterpart, decodeSource is nil there.
- Runtime-parsed script strings (ParseConditionalString / ParseResponseString, e.g. EEex_LuaTrigger in a string)
  lose spaces and most punctuation in both games (identical parser); compiled BCS keep them.
- Modder feature battery (bindings/test/PTEE_FeatureTest.lua, F10 in the dev game): EEex triggers / objects /
  actions, extended stats, op400..403, 408, 409, script loading with the Torment constructor: 18/18 in game.
- Known limitation: casting off the op214 internal list from a keybind (B3Hotkey / EEex_Keybinds) is disabled:
  Torment's ReadyOffInternalList takes an index into a different array than GetInternalButtonList's list.

## Game-session battery (bindings/test/PTEE_Battery.lua, tools/battery.py)
A scripted session on the dev game, run end to end by `python tools/battery.py` (69 pass / 0 fail on 2026-10-21; keys sent with PostMessage:
no focus change). Steps: API sweep (1095 calls on the 6 party members, 0 Lua error), companions join (party of 6,
timer instances per portrait), XP, opcode extensions, op326, combat (rats + skeletons), 26 real casts (decode hook),
126 player spells applied (SPWI/SPPR/SPIN), travel through 5 areas and back, rest, quick save, reload, companions leave.
Results, opcode extensions (all in game now, beyond the code review):
- op101 + saving throw bit 23 bypasses the immunity; op146 special 2 -> SpellNoDec (191); op148 special 1 ->
  SpellPointNoDec (192); op214 param2 3 calls the Lua hook and the resource function; op248 special 1: the .EFF
  reaches a creature immune to weapons (op120); op333 copy hook called; op326 flip (special 2): SPLPROT
  ENOUGHINT / NOTENOINT checked on the source instead of the target, 5/5 cases incl. controls.
- op326: upstream's doc says `special & 1`, EEex.dll (upstream and ours) tests `special & 2`: the code is the
  reference. SPLPROT's EA rows go through an EA-category helper (Torment 0x12b770), not the raw EA: unusable to tell
  source from target (EA == 2 is false even on a PC).
- op219 / op280 / op342 / op319 / op249: applied without error (EEex.dll only, no Lua-visible result); op249 needs a
  ranged attacker (none in the party).
- Marshal handlers: Lua data saved with TNO comes back after the reload (importer run on load).
Vanilla Torment behaviour found on the way (same without EEex, reproduced in the vanilla game from the same save):
- `RestParty()` forced where resting is not allowed (the Mortuary) never returns. Root cause (static analysis, matches
  the RIP samples): the endless loop is the "heal party on rest" loop of CInfGame::RestPartyPrivate (PT 0x2edd50..
  0x2eddf8, BG 0x288370, identical code); PartyHeal (PT 0x3d66e0) only shows up in the samples because it is called
  6x6 times per pass (PT 0x2de370 -> 0x3d66e0) and itself always returns.
  - The loop runs while `[game+0xb954]` (most likely CGameOptions::m_bRestHealParty) and `game.m_bPartyHurt`
    (`[game+0xce9c]`, set by PT 0x2de370 when a member still misses more HP than the threshold) are set; when the
    hour cap flag (RestParty r9b, `[rsp+0x30]`) is 0 there is no other exit.
  - Each pass adds the per-rest heal amount (RestParty r8d, `[rsp+0x48]`) to the threshold (r14d) handed to
    PartyHeal: missing HP is compared to the accumulated rest healing, so the loop ends once that sum covers the worst
    wound. PartyHeal also casts memorized op17 healing spells (consumed, memorized again only on pass 0).
  - Script action RestParty (CGameAIBase::ExecuteAction, PT 0x16eeea): heal amount = `action+0x444`, plus 1 only
    when ENGINE_MODE != 3 (PT 0x16eeff `cmp ENGINE_MODE, 3` / `je` over `inc r8d`). BG2EE always adds 1 (BG
    0x15f6d7). In Torment `RestParty()` passes 0, hour cap flag 0 (`action+0x440` == 0).
  - Result: with any party member hurt beyond what the memorized healing spells cover, the threshold stays 0,
    m_bPartyHurt stays 1, the loop never ends. The UI passes 10 in Torment (PT 0x36228b), so it ends. The area
    (no-rest Mortuary) is not the cause: the script action never checks CanRestParty; expected to hang anywhere
    with "heal party on rest" on and a hurt party (not re-tested).
  - Fixed (John's choice, shipped in EEex_Fix_Patch.lua, label Hook-PTEE-CInfGame::RestPartyPrivate()-HealPartyCall;
    live test 2026-10-21: party of 6 hurt in the Mortuary, scripted RestParty() twice, no hang, the memorized healing
    spells still heal). Design notes kept below.
  - Fix design: an EEex_Fix_Patch-style hook after the heal call in
    RestPartyPrivate (PT 0x2edd60): leave the loop (jmp PT 0x2ede14) when the call returned 0 and the per-rest heal
    amount `[rsp+0x48]` is 0 (no progress possible). Keeps Torment's "RestParty() heals nothing" behaviour. The
    alternative, NOP the 2-byte `je` at PT 0x16ef13 (BG2EE behaviour, +1 HP per pass), changes how much a scripted
    RestParty() heals.
- The scripted `Rest()` heals nobody; plot / cutscene SPL (BBRIDGE, BDBUMP...) applied by script start cutscenes;
  AR0500 triggers Morte's kidnapping (area event).
