# EEex_Actionbar.lua (Torment review)

No hooks. The file hard-codes BG button types (`EEex_Actionbar_ButtonType`, values of `CInfButtonArray.m_buttonTypes`
+0x1fb0, `m_nSelectedButton` +0x2268 holds a type too) and documents BG states / configs. Patch: `patches/EEex_Actionbar.py`.

## Method
Compared, BG vs PT: `CInfButtonArray::OnLButtonPressed` main type switch (BG 0x264088 `lea eax,[rdx-2]; cmp 0x1c`,
PT 0x2c658e `cmp 0x44`, byte table PT 0x2c73c8), its per-state list switches, `OnRButtonPressed` (PT 0x2c7410),
`UpdateButtons` type switch (BG 0x2678d7 `cmp 0x45` byte table 0x26a5bc, PT 0x2ca6e7 `cmp 0x46` byte table 0x2cd968:
icon frame + ENGINEST tooltip id per handler), its hotkey switch (BG 0x269802, PT 0x2cca65: keymap offset per type),
`SetState` layouts (BG 0x266000, PT 0x2c8a20, every config block), the find-button-by-type helper (BG 0x2633e0 /
PT 0x2c5650) and its `CScreenWorld::OnKeyDown` callers. ENGINEST id 0xf000XX = row XX+1 (ATTACK type 8 -> 0xf000d1 ->
STRREF_GUI_BUTTONS_ATTACK).

## Button types (Torment value -> meaning -> evidence)

| PT | BG | Name in patched table | Meaning | Evidence (PT) |
|---|---|---|---|---|
| 0 | 0 | - | legacy scroll left arrow (icon only, no click) | UpdateButtons 0x2ca713 icon 0x40; no OnLButtonPressed case |
| 1 | 1 | - | legacy scroll right arrow | UpdateButtons 0x2ca7e1 icon 0x42 |
| 2 | 2 | BARD_SONG | battle song / shaman dance modal | OnLButton 0x2c6e55 (modal 1 if class 5 else 5), selected = 2 (0x2c6e97); hotkey slot 0xb50 (BG 0xb48) |
| 3 | 3 | CAST_SPELL | open spell list (states 103 / 113) | OnLButton 0x2c6876 SetState 0x67 / 0x71; tooltip 0xf000d3 CASTSPELL |
| 4 | 4 | FIND_TRAPS | detect traps modal | OnLButton 0x2c6fb2 modal 2, selected 4; tooltip 0xf000d4 DETECTTRAPS |
| 5 | 5 | TALK | talk cursor | OnLButton 0x2c65b2 cursor 0x12, selected 5; tooltip 0xf000d5 DIALOG |
| 6 | 6 | - | unused (no handler in either game) | default in all switches |
| 7 | 7 | GUARD | guard | OnLButton 0x2c66a8 (state 3), selected 7; tooltip 0xf000d6 GUARD |
| 8 | 8 | ATTACK | attack cursor | OnLButton 0x2c662d cursor 0xc, selected 8; tooltip 0xf000d1 ATTACK |
| 9 | 9 | - | shapechange (no click case in either game) | UpdateButtons 0x2caf72 icon 0x28, tooltip 0xf000df SHAPECHANGE |
| 10 | 10 | SPECIAL_ABILITIES | open state 106 | OnLButton 0x2c6cf6 SetState 0x6a; tooltip 0xf000d9 PICKSPECIALABILITY; OnKeyDown 0x35d081 edx = 0xa |
| 11 | 11 | STEALTH | stealth modal | OnLButton 0x2c705e modal 3, selected 0xb (0x2c707a); tooltip 0xf000e0 STEALTH |
| 12 | 12 | THIEVING | thieving cursor 0x24 / 0x28 | OnLButton 0x2c6db9, selected 0xc (0x2c6e2e); tooltip 0xf000e2 THIEVING; OnKeyDown 0x35d040 / 0x35d09d edx = 0xc |
| 13 | 13 | TURN_UNDEAD | turn undead modal | OnLButton 0x2c71be modal 4, selected 0xd (0x2c71df); tooltip 0xf000e3 TURNUNDEAD |
| 14 | 14 | USE_ITEM | open state 105 | OnLButton 0x2c674a SetState 0x69; tooltip 0xf000e4 USEITEM |
| 15 | 15 | STOP | stop action | UpdateButtons 0x2cae9a icon 0x3a, tooltip 0xf000e1 STOPACTION; state 109 slot 2 |
| 16..20 | 16..20 | - | quick formation 1..5 | UpdateButtons 0x2cb747 tooltip 0xf000da QUICKFORMATION; state 109 slots 7..11; OnRButton 0x2c74eb `lea eax,[rcx-0x10]; cmp 4` |
| 21..23 | 21..23 | QUICK_ITEM_1..3 | quick items | OnLButton 0x2c6798 (sub 0x15 at 0x2c6801); UpdateButtons 0x2cb8d7 |
| 24, 25 | - | QUICK_ITEM_4, QUICK_ITEM_5 | Torment-only quick items 4, 5 | same handlers (PT byte table 0x2c73c8: 21..25 -> one case); state 117 slots 3, 4; no hotkey (0x2cd9b0) |
| 26..28 | 24..26 | QUICK_SPELL_1..3 | quick spells | OnLButton 0x2c69bc (sub 0x1a at 0x2c6a13); UpdateButtons 0x2cbc12; PostRenderButton 0x2c828e `sub 0x1a; cmp 2`; hotkeys 0xb34..0xb3c (BG 0xb2c..0xb34) |
| 29..32 | 27..30 | QUICK_WEAPON_1..4 | quick weapons | OnLButton 0x2c6a88 (sub 0x1d at 0x2c6b7e / 0x2c6c88); UpdateButtons 0x2cbfe1; OnRButton 0x2c7ce1 sub 0x1d |
| 33 | - | QUICK_WEAPON_5 | Torment-only 5th quick weapon | same case (29..33); state 115 writes 0x1d + i for GetNumQuickWeaponSlots (or 5) slots (PT 0x2c9f81) |
| 34..44, 56 | 31..42 | - | list entries 1..12 (spells / items / abilities / formations / tablet lists) | SetState state 101: slots 0..10 = 34..44, slot 11 = 56 (PT 0x2c8c6b); UpdateButtons one case 0x2cc5b6 (BG 0x26934e); list switch PT 0x2c5ff1 `add eax,-0x22` byte table 0x2c7324; OnRButton PT 0x2c759b index = m_nListStartIndex + type - 0x22 (so the 12th entry, 56, gives +22: engine quirk) |
| 45, 48..55 | - | - | unused | default in every PT switch |
| 46 | 43 | - | list page left | state 102..105 slot 0; switch 0x2c7324 case 1; UpdateButtons 0x2cc662 |
| 47 | 44 | - | list page right | slot 11 of the list states; UpdateButtons 0x2cc6ff |
| 67 | 67 | - | jump to mage spells | UpdateButtons 0x2cc887 tooltip 0xf000d8 JUMPTOMAGE |
| 69 | 69 | - | jump to cleric spells (states 113 / 114 slot 1) | UpdateButtons 0x2cc799 tooltip 0xf000d7 JUMPTOCLERIC; SetState config 30 (PT 0x2c9026) |
| 70 | - | CHARACTER_ABILITY | Torment-only character special ability (state 118) | OnLButton 0x2c71ff -> 0x257e00 when ENGINE_MODE (0x7cb718) == 3; UpdateButtons 0x2cc574 -> 0x25b550 (object 0x72c8f0, per-button entry 0x34 bytes); OnRButton 0x2c77b8; written by PT 0x25a810 (state 118 builder: NAMELESS (when a thief) / ANNAH get FIND_TRAPS, THIEVING, STEALTH; NAMELESS / GRACE / MORTE get type 70 entries, names table 0x71e480) |
| 100 | 100 | NONE | empty button | all layouts |

`m_nSelectedButton` (+0x2268) holds a button type in both games (UpdateButtons PT 0x2ca6cd `cmp [r14+0x2268], type`).
Torment's +0x2274 (padding in the bindings) receives the pressed button index (PT 0x2c5ad9).

## States / configs
- States 1..114 and configs 0..30: same as BG (PT SetState byte table 0x2ca438; layouts use the shifted types
  above). PST CLASS.IDS has BG's class list, so the class states keep their names, but Torment's engine never selects
  them: CInfGame::SelectToolbar returns into PT 0x25a1e0 (context bar refresh) when ENGINE_MODE == 3 (PT 0x2f24ec).
- Torment-only (names: `const` in Torment's BGEE.lua): 115 WEAPONS (config 31, PT 0x2c9f12: quick weapons + GUARD),
  116 SPELLS (32, PT 0x2ca077: list), 117 ITEMS (33, PT 0x2c9fe6: QUICK_ITEM_1..5), 118 SPECIAL_ABILITES (34,
  PT 0x2ca198 -> 0x25a810), 119 FORMATIONS (35, PT 0x2ca1cd: list like 107), 120 PST_TABLET_FOOTBALL (36, list of 8,
  click switch PT 0x2c5b90 type - 0x22), 121 PST_TABLET_MISC (37, list of 6, PT 0x2c5c26).
- Default config 38 (BG 31) = states 19, 22..100: PT 0x2ca362 only calls UpdateButtons (BG also sets every button to
  NONE and m_nState to 0). States outside 1..121 -> config -1 (EEex_Actionbar_Patch hook).
- B3Hotkey / EEex_Keybinds `config == 28` (state 111) is unchanged.

## Other checks
- EEex_Actionbar_Hook_IsPartyLeader (THIEVING = 12): unchanged.
- EEex_Actionbar_Hook_HasFullThieving (`getClass() ~= 5`): unchanged, the engine site compares the class with 5 too
  (PT 0x2c6e0f `cmp al, [0x61f29e]` = 5, BG 0x2647d7 same rule; PST CLASS.IDS 5 = BARD).
- No other EEex script uses EEex_Actionbar_ButtonType or m_buttonTypes (grep of copy/: only EEex_Actionbar.lua);
  EEex_Stats' EEex_DerivedStats_DisabledButtonType is another enum (opcode 144), not covered here.
- EEex_Actionbar_GetOp214ButtonDataIterator filters SPWI110 / SPWI124 (BG Identify / Nahal's): neither resource
  exists in Torment, so the filter is a harmless no-op; left as is.

## Open questions
- Torment's 12th list entry is type 56 instead of 45; right-click info on it uses index list start + 22
  (PT 0x2c759b `lea edx,[rbx-0x22]`), an engine quirk, not touched.
- CHARACTER_ABILITY only works on the state 118 bar (its data list is filled by PT 0x25a810); setting it with
  EEex_Actionbar_SetButton elsewhere shows / triggers whatever that list holds.
