# EEex_Stats_Patch.lua (Torment review)

Patch: `eeexlua/patches/EEex_Stats_Patch.py` (3 replacements, `python build.py` OK). PT = Torment.exe RVA, BG = BG2EE RVA.

## Hooks and label uses

| # | Label / site | Verdict | Evidence |
|---|---|---|---|
| 1 | `Hook-CDerivedStats::Construct()-FirstCall` (AfterCall) | unchanged | PT 0x15c00b (first call of PT 0x15bfe0), rsi = this (0x15c001 `mov rsi, rcx`). |
| 2 | `Hook-CDerivedStats::Destruct()-FirstCall` (AfterCall) | unchanged | PT 0x1bb9f0 (first call of 0x1bb9c0), rdi = this (0x1bb9df). |
| 3 | `Hook-CGameSprite::QuickLoad()-CDerivedStats::Reload()` (AfterCall) | unchanged | PT 0x3d9dbf call Reload 0x161200; rdi = sprite (0x3d9dc4 `mov rcx, rdi`, stats = sprite+0xfe8). |
| 4 | `Hook-CGameSprite::Unmarshal()-CDerivedStats::Reload()-1` (AfterCall, JIT'd rbx helper) | unchanged | PT 0x3edfd6, rbx = sprite (0x3edfc2 `lea r12, [rbx+0xfe8]`). |
| 5 | `Hook-CGameSprite::Unmarshal()-CDerivedStats::Reload()-2` (AfterCall) | unchanged | PT 0x3ee6c5, rbx = sprite (0x3ee6ad `lea r9, [rbx+0xb78]`). |
| 6 | `Hook-CGameSprite::ProcessEffectList()-CDerivedStats::Reload()` (AfterCall) | unchanged | PT 0x423d3a, rsi = sprite (0x423d33 `lea rcx, [rsi+0xfe8]`). |
| 7 | (new) Torment-only Reload call PT 0x17421e (AfterCall, r15) | **added** | Reload has 5 callers in PT, 4 in BG. Extra one in a Torment-only sprite routine PT 0x173c00 (called once, from CGameAIBase::ExecuteAction PT 0x1711cb), sprite in r15 (0x173c2e `mov r15, rcx`, 0x174217 `lea rcx, [r15+0xfe8]`, 0x174229 `mov rcx, r15`). No label there: site = `CGameAIBase::GetTargetShareType(byte)` (PT 0x173440) + 0xDDE, hooked only if it is an E8 call to the same target as the QuickLoad site. It is followed by ProcessEffectList(r15, 1) (which reloads again with hook #6), so this mainly covers ProcessEffectList's early-out path. Volatiles after the call: rcx/edx rewritten, r8/r9 unused before the next call. |
| 8 | `Hook-CDerivedStats::operator_equ()-FirstCall` (AfterCall) | unchanged | PT 0x15c91c (first call of 0x15c660); r14 = this (0x15c683), rsi = other (0x15c67e). |
| 9 | `Hook-CDerivedStats::operator_plus_equ()-FirstCall` (BeforeCall) | unchanged | PT 0x15d5d6 (first call of 0x15d580); rbx = this (0x15d593), rdi = other (0x15d59a); rcx (call argument) saved/restored; rdx dead after. |
| 10 | `Hook-CDerivedStats::GetAtOffset()-OutOfBoundsJmp` (CondJumpOnSuccess, restore 0) | **patched** (stack) | PT 0x15f1fe near `ja 0x15fb55`. Torment's GetAtOffset (0x15f1f0) starts with `sub rsp, 0x38` (BG 0x151bc0 has no frame): hook site is 16-byte aligned (stack_mod 8 removed) and the hook's own `ret` must first `add rsp, 38h` (as PT's exit 0x15fb57). rax = id-1 (`movsx eax, dx; dec eax`), rcx = this unchanged; same bound 0xc9 (stats 1..202), FIRST_EXTENDED_STAT_ID 203 stays. Unpatched: return into the caller's frame -> crash on the first extended-stat read. |
| 11 | `Hook-CDerivedStats::GetSpellState()-FirstInstruction` (JITAt jmp) | unchanged | PT 0x160c30: whole function replaced by EEex.dll Override (ported, AUDIT.md). First 5 bytes = `mov eax, edx; mov r8d, edx` (instruction boundary, no jump into them). |
| 12 | `Hook-CDerivedStats::SetSpellState()-FirstInstruction` (JITAt jmp) | unchanged | PT 0x161aa0: `mov r8, rcx; mov eax, edx` = 5 bytes, replaced by the Override. |

## Label fixes needed
None (a label for the Torment-only Reload site PT 0x17421e would be cleaner than the label + 0xDDE offset).

## BG-only features
None.

## Open questions
- What the Torment-only routine PT 0x173c00 is (an ExecuteAction case resetting the sprite's stats, then
  ProcessEffectList(sprite, 1)): hooked anyway for full coverage.
