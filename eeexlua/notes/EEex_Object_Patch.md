# EEex_Object_Patch.lua (Torment review)

Patch: `eeexlua/patches/EEex_Object_Patch.py` (2 replacements, `python build.py` OK). PT = Torment.exe RVA, BG = BG2EE RVA.

CAIObjectType::Decode (PT 0x129470, BG 0x11bba0) register map: this BG r13 -> PT rbx (0x1294a4 `mov rbx, rcx`),
caller BG r12 -> PT r13 (0x12949a `mov r13, rdx`), OBJECT.IDS loop index BG r15 -> PT r12 (0x12976c `mov r12, r15`,
0x12979a `movzx r14d, byte ptr [r12+rbx+0x10]`, 0x12ae55 `inc r12; cmp r12, 5`). Same frame (lea rbp, [rsp-0x2f];
sub rsp, 0xa8).

## Hooks and label uses

| # | Label / site | Verdict | Evidence |
|---|---|---|---|
| 1 | `Hook-CAIObjectType::Decode()-TargetNameOverride` (CondJumpOnFail, restore 0) | **patched** (r13 -> rbx) | PT 0x1294eb near `je 0x129612` (6 bytes, BG 0x11bc1c). Fall-through PT 0x1294f1 `cmp dword ptr [rbx+0xc], -1` (BG [r13+0xc]). rax/rcx dead (next: lea rcx / call). Torment's fall-through adds a sprite-type (0x71) branch for the name lookup: irrelevant to the hook (skip goes to the same success target). |
| 2 | `Hook-CAIObjectType::Decode()-DefaultJmp` (CondJumpOnSuccess, restore 0) | **patched** (r13 -> rbx, r12 -> r13, r15 -> r12) | PT 0x1297b2 near `ja 0x12adf7` (BG 0x11bed8), `dec eax; cmp eax, 0x71` as BG (ids 1..114; PT OBJECT.IDS ends at 114, EEex's 115..118 reach the hook). Default target PT 0x12adf7 `mov rax, [r13]; mov rcx, r13; call [rax+0x20]` (caller = r13, BG r12). `[rbp-0x11]` = curAIType unchanged (PT 0x1297db / 0x12ae35). rdx = [rbp-0x29] kept and restored by the hook (PT 0x12ae51 reload before NormalBranch). |
| 3 | `Hook-CAIObjectType::Decode()-NormalBranch` (jmp target) | unchanged (label OK) | PT 0x12ae55 `inc r12` = BG 0x11d7fc `inc r15`: loop continue. |
| 4 | `Hook-CAIObjectType::Decode()-ReturnBranch` (jmp target) | unchanged (label OK) | PT 0x129ad3 `mov r14, [rsp+0xa0]` = BG 0x11c201 (restores of the shrink-wrapped nonvolatiles), also the loop-exit target (PT 0x12ae60 `jge 0x129ad3`). |
| 5 | `EEex_HookIntegrityWatchdog_IgnoreStackSizes(DefaultJmp, {{0x68, sizeof}})` | unchanged | [rbp-0x11] = rsp+0x68 in both frames. |

## Label fixes needed
None.

## BG-only features
None.

## Open questions
None.
