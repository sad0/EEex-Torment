# EEex_Trigger_Patch.lua (Torment review)

Patches: `eeexlua/patches/EEex_Trigger_Patch.py` (2 code + 5 header-comment replacements) and
`eeexlua/patches/EEex_Trigger.py` (4 replacements, trigger renumbering). `python build.py` OK.
PT = Torment.exe RVA, BG = BG2EE RVA.

## Hooks and label uses

| # | Label / site | Verdict | Evidence |
|---|---|---|---|
| 1 | `Hook-CGameAIBase::EvaluateStatusTrigger()-DefaultJmp` (CondJumpOnSuccess, restore 0) | **patched** (r14 -> r15, [rbp+350h] -> [rbp+370h]) | PT 0x1657ac near `ja 0x16c455` (BG 0x15684e). Function PT 0x1656b0: `mov r15, rcx` (0x1656e0, BG `mov r14, rcx`), CAITrigger copy built at [rbp+0x370] (0x1656e7 lea + copy ctor 0x123e40; 0x16578d `movsx eax, word ptr [rbp+0x370]`), frame 0x20 larger (lea rbp, [rsp-0x4b0]). Default target PT 0x16c455 `mov r13d, esi` (result in esi, as BG 0x15d050); rax/rcx/rdx/r8-r11 dead there (CString destructors). rbx/rdi loaded before the ja (0x165794/0x1657a0) are nonvolatile: preserved by the Lua call. |

## Trigger ids (Torment collision)

Torment's switch: `add eax, -0x400A; cmp eax, 0x106; ja default` (PT 0x16579b..0x1657ac; BG bound 0x102).
Byte/dword jump tables PT 0x16c7d8 / 0x16c4fc: 0x410D..0x4110 each have their own case (none maps to the default
target), so EEex's hook never sees EEex's ids 0x410D..0x4110 in Torment: they are ExtraProficiency (0x410d),
ExtraProficiencyGT (0x410e), ExtraProficiencyLT (0x410f), LastPersonTalkedTo (0x4110) in PT TRIGGER.IDS.
Every id > 0x4110 takes the `ja` into the hook. 0x4111 NearSavedLocationPST is listed in TRIGGER.IDS but has no case
and no other handler (no 0x4111 / -0x4111 immediate in Torment.exe): it reaches the hook, whose Lua returns false
for unknown ids = the engine's default result, so vanilla behavior is kept.
Ids below 0x400A also take the `ja` (unsigned), as in BG.

New EEex ids (EEex_Trigger.py renumbers the dispatch in `EEex_Trigger_Hook_OnEvaluatingUnknown`):

```
0x4112 EEex_HasDispellableEffect(O:Object*)
0x4113 EEex_LuaTrigger(S:Chunk*)
0x4114 EEex_IsImmuneToOpcode(O:Object*,I:Opcode*)
0x4115 EEex_MatchObject(S:Chunk*)
0x4115 EEex_MatchObjectEx(S:Chunk*,I:Nth*,I:Range*,I:Flags*X-MATOBJ)
```

These lines must replace upstream `EEex/patch/TRIGGER.IDS` for the Torment install (the installer appends that file
to TRIGGER.IDS; not done here: ref/ is read-only for this task). No other EEex Lua file uses the ids (grep of
0x410D..0x4110 / 16653..16656 over EEex_scripts).

Objects (EEex_Object_Patch.lua): EEex's OBJECT.IDS 115..118 do not collide (PT OBJECT.IDS ends at 114) and reach the
Decode DefaultJmp hook (`dec eax; cmp eax, 0x71; ja`, PT 0x1297af). Actions 472..479 are not in these files.

## Label fixes needed
None.

## BG-only features
None.

## Open questions
- The installer (EEex.tp2, TRIGGER.IDS append) must use the 0x4112..0x4115 lines above for Torment.
