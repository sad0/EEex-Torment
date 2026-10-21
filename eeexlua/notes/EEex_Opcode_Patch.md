# EEex_Opcode_Patch.lua (Torment review)

Patch: `eeexlua/patches/EEex_Opcode_Patch.py` (9 replacements, `python build.py` OK). PT = Torment.exe RVA, BG = BG2EE RVA.
Opcode classes (tools/opcodes.json): 101, 148, 214, 219, 248, 249, 280, 326, 333, 342 keep the BG class; 146 is
"changed" (see #5); 319 shares one class with 125/142/149/150 in Torment, but op319 is only consumed through the
non-virtual CheckUsability / GetUsabilityText (EEex.dll Override rewritten for PT, AUDIT.md). New opcodes 400..409 are
free (Torment's DecodeEffect table ends at 383).

## Hooks and label uses

| # | Label / site | Verdict | Evidence |
|---|---|---|---|
| 1 | `Hook-CGameEffect::Destruct()_FirstCall` (AfterCall) | unchanged | PT 0x159cb0, rdi = effect (0x159ca1). |
| 2 | `Hook-CGameEffect::CopyFromBase()-FirstCall` (AfterCall) + `Data-CGameEffect::DecodeEffectFromBase()-After-CGameEffect::CopyFromBase()` | **patched** (rdi <-> rsi) | PT 0x1fce60 in 0x1fce30: dst (this) in rsi, source base in rdi (0x1fce4e/0x1fce51; BG the reverse). Return address still [rsp+0x38] (push rdi; sub rsp, 0x30). All 352 PT callers checked: every one except DecodeEffectFromBase (PT 0x20376c, data label 0x203771 OK) is a Copy() passing `lea rdx, [rsi+8]`. |
| 3 | `Hook-CGameSprite::ProcessEffectList()-AfterListsResolved-1` / `-2` (CondJumpOnSuccess, restore 7 / 3) | unchanged | PT 0x425cd7 short `je` + 7 bytes `cmp dword ptr [rsi+0x4bd8], 0`; PT 0x425ce0 short `jne` + 3 bytes `mov rcx, rsi`; both relocatable, same boundaries as BG; rsi = sprite. |
| 4 | `Hook-CGameSprite::ProcessEffectList()-AfterListsResolved-3` (AfterCall) | unchanged | PT 0x425ce5, rsi = sprite. |
| 5 | `Hook-CGameSprite::ProcessAI()-BeforeReturn` (BeforeRestore 0,8,8) | **patched** (rsi -> rbx) | PT 0x42319f `mov r15, [rsp+0x158]` (8 bytes, rsp-relative). Sprite: PT rbx (0x421858 `mov rbx, rcx`, temporarily reused at 0x421e69, reloaded 0x421f22 from [rsp+0x60]; all 13 jumps to the site come later). |
| 6 | `Hook-CGameEffectCastSpell::ApplyEffect()-CMessageHandler::AddMessage()` (op146, BeforeCall) | **not portable: disabled** (`if false then`) | PT 0x1c2be3, rsi = effect, rdx = message as BG; but Torment's param2 == 0 path already uses m_special: `cmp dword ptr [rsi+0x48], 0; je; mov eax, 0x1d2` (PT 0x1c2ae1..0x1c2aeb) queues 466 ForceSpellRESNoFeedback when special != 0. EEex's (special & 1) -> 191 SpellNoDec would overwrite Torment's vanilla no-feedback casts. |
| 7 | `Hook-CGameEffectCastSpellPoint::ApplyEffect()-CMessageHandler::AddMessage()` (op148) | unchanged | PT 0x1c2e9f, rdi = effect (0x1c2c8a), rdx = message; no Torment use of m_special; action 192 SpellPointNoDec exists in PT ACTION.IDS; m_actionID at message+0x10 (PT 0x1c2b5e). |
| 8 | `Hook-CGameEffectSecondaryCastList::ApplyEffect()` (op214, BeforeRestore 0,5,5, stack_mod 8, early ret) + IgnoreRegistersForInstance | unchanged | PT 0x1e1c80 identical function (fdiff 1.000); 5-byte `mov [rsp+0x18], rbx`. |
| 9 | `Hook-CGameEffectProtectionCircle::ApplyEffect()-AddTail` (op219, BeforeCall) | unchanged | PT 0x1dad30, rbx = effect, rdi = CSelectiveBonus (`mov dword ptr [rdi+0x18], 2` 0x1dad26 = m_bonus). |
| 10 | `Hook-CGameEffectMeleeEffect::ApplyEffect()-AddTail` (op248, AfterCall) | unchanged | PT 0x1d6bfb, rbx = new effect, rdi = op248 (0x1d6be2 `test byte ptr [rdi+0x20], 4`). |
| 11 | `Hook-CGameEffectRangeEffect::ApplyEffect()` (op249, BeforeRestore 0,6,6) | unchanged | PT 0x1dc600 `push rdi; sub rsp, 0x40` = 6 bytes; rcx = effect. |
| 12 | `Hook-CGameEffectRangeEffect::ApplyEffect()-AddTail` (AfterCall) | unchanged | PT 0x1dc67a, rbx = new effect. |
| 13 | `Hook-CGameEffectForceSurge::ApplyEffect()-FirstInstruction` (op280, BeforeRestore 0,9,9, stack_mod 8) | unchanged | PT 0x1cf460 identical 5-instruction leaf (fdiff 1.000); 9 bytes = `mov eax, [rcx+0x20]` + `mov [rdx+0x121c], eax`. |
| 14 | `Hook-CGameSprite::WildSpell()-OverrideSurgeNumber` (BeforeRestore 0,9,9) | unchanged | PT 0x43bdb5 `test r12, r12` + `mov r12d, 0x64` = 9 bytes; r14 = sprite (0x43bbcb), r13d = roll. |
| 15 | `Hook-CGameSprite::WildSpell()-CGameSprite::Feedback()` (BeforeCall) | unchanged | PT 0x43c694, rcx = r14 = sprite (reloaded from [rsp+0x58], BG [rsp+0x60]). |
| 16 | `Hook-CGameSprite::WildSpell()-SuppressVisualEffectJmp` (CondJumpOnFail, restore 0) | unchanged | PT 0x43c6c5 near `je`, r14 = sprite. |
| 17 | `Hook-CGameSprite::WildSpell()-CVisualEffect::Load()-SPFLESHS` (BeforeCall, CString::Destruct) | unchanged | PT 0x43d396; CVisualEffect::Load PT 0x2baed0 identical (fdiff 1.000), so it destroys its CString argument like BG; r14 = sprite. |
| 18 | `Hook-CGameSprite::WildSpell()-operator_new()-SPFLESHS` (BeforeCall) | unchanged | PT 0x43d3be, same null path (0x43d43c `mov r14, rsi`). |
| 19 | `Hook-CGameSprite::WildSpell()-CMessageHandler::AddMessage()-SPFLESHS` (BeforeCall) | unchanged | PT 0x43d453, rdx = message. |
| 20 | `Hook-CGameEffectUsability::CheckUsability()-FirstInstruction` (op319, JITAt jmp) | unchanged | PT 0x1ed180, 5-byte `mov [rsp+0x18], rbx`; Override rewritten for PT in EEex.dll. |
| 21 | `Hook-CItem::GetUsabilityText()-IsOp319InvertedJmp` (BeforeCondJump, restore 4) | unchanged | PT 0x2227c2: `cmp dword ptr [rcx+0x18], 1` (4 bytes) + short `jne`; rcx = effect. |
| 22 | `Hook-CGameEffectApplySpell::ApplyEffect()-OverrideSplprotContext` (op326, AfterRestore 0,7,7) + IgnoreRegistersForInstance | unchanged | PT 0x1c1312 `mov rcx, [rax+0x10c8]` (7 bytes, not RIP-relative); rbx = effect, edx = param2, r8 = source, r9 = target as BG; SPLPROT call PT 0x1c1320. |
| 23 | `Hook-CGameEffectStaticCharge::ApplyEffect()-CopyOp333Call` (op333, AfterRestore 0,9,9) | unchanged | PT 0x1e68ca `call [rax+8]` (3) + `mov edx, [rbx+0x150]` (6); rax = copy after the restore. |
| 24 | `Hook-CGameEffectOverrideAnimation::ApplyEffect()-LastParam2Jmp` (op342, CondJumpOnSuccess) | unchanged | PT 0x1d80f8 near `jne`, rsi = effect, rdi = sprite; same param2 1/2/4 cases. |
| 25 | `Hook-CGameSprite::OneSwing()-GetAttackFrameType()` (HookNOPs 1, rdi) | unchanged | PT 0x41e4b2 `call qword ptr [rax+0x198]` (6 bytes; Torment vtable slot, BG 0x190: the EEex.dll body calls through the PT-order bindings); rdi = sprite, dl = numAttacks after `sub dl, 5`. |
| 26 | `Hook-CGameSprite::Swing()-GetAttackFrameType()` (HookNOPs 1, rbx) | unchanged | PT 0x433a2a, same, rbx = sprite. |
| 27 | `Hook-CImmunitiesEffect::OnList()-Entry` (BeforeRestore 0,5,5, stack_mod 8, early ret) + IgnoreRegistersForInstance | unchanged | PT 0x21bed0, 5-byte `mov [rsp+0x18], rbx`, rdx = effect. |
| 28 | `Hook-CGameEffect::CheckAdd()-LastProbabilityJmp` (CondJumpOnFail) + `-ProbabilityFailed` | **patched** (r14 -> rsi) | PT CheckAdd 0x1eba60 is restructured (frame 0x50, BG 0x238): sprite in rsi (0x1eba8d `mov rsi, rdx`; 0x1ebace `[rsi+0x4bbc]`, BG `[r14+0x4ea4]`), rdi = effect; near `jb` PT 0x1ebaa1; ProbabilityFailed PT 0x1ebbea `xor eax, eax` + epilogue (= BG 0x1cc9a5); rdx = sprite read after (preserved). |
| 29 | `Hook-CGameSprite::AddEffect()-noSave-Override` (CondJumpOnSuccess, restore 3) | unchanged | PT 0x3fb165 short `jne` + `test rbx, rbx` (3 bytes). |
| 30 | `Hook-CGameEffect::DecodeEffect()-DefaultJmp` + genOpcodeDecode (`-Fail`, `-Success`, `CGameEffect::Construct`, `CGameEffect::GetItemEffect`, `CGameEffect::CopyFromBase`, `operator_new`, `Data-CGameEffect::vftable`) + IgnoreStackSizes | **patched** | PT 0x1fe3b6 near `ja` (`cmp eax, 0x17f`); rdi/r14/ebp/rsi/eax/rbx(0) as BG; r15 already saved at [rsp+0x60] by Torment (0x1fe3ac). Copy(): `mov ecx, 158h` -> CGameEffect.sizeof (0x160 in PT: every PT Copy, e.g. 0x1ed3ac); rest identical (PT 0x1ed390 vs BG 0x1ce100). Construct (PT 0x1b5440) same 7 args (fdiff 0.989, one extra member at +0x154). GetItemEffect identical. vtbl: PT CGameEffect vtable keeps BG's 11-slot order. Join: see label fixes. |
| 31 | `EEex_HookIntegrityWatchdog_IgnoreStackSizes(DefaultJmp, {{0x60, 8}})` | unchanged | Same frame (3 pushes + sub rsp, 0x40). |
| 32 | Hard-coded opcode numbers 400..409, action ids 191/192 | unchanged | Free opcodes in PT; 191 SpellNoDec / 192 SpellPointNoDec in PT ACTION.IDS. |
| 33 | `Hardcoded_free` (writeCopy) | unchanged | InfinityLoader symbol; BG/PT Copy call the sized delete (BG 0x45e690 / PT 0x4e8140) with 0x30. |

## Label fixes needed
- `Hook-CGameEffect::DecodeEffect()-Success` (PT 0x2030a3) is not BG's `mov rbx, rax` join: in Torment it is
  `mov dword ptr [rbx+0x1c], eax` inside the default case (rbx = new base effect). Torment has no shared
  `mov rbx, rax`: each case does `mov rbx, rax; jmp 0x2030a6`. No exact counterpart exists.
- `Hook-CGameEffect::DecodeEffect()-Fail` (PT 0x2030ad `mov r15, [rsp+0x60]`) skips Torment's join instruction
  `mov eax, [rsp+0x80]` (PT 0x2030a6, reordered before the r15 restore). The right Torment join is PT 0x2030a6.
  The patch uses `Fail - 7` (= 0x2030a6) and does `mov rbx, rax` itself; no DB change needed for EEex, but the
  labels should be documented (or moved: Fail -> 0x2030a6, Success -> none).

## BG-only features
- op146 (special & 1) -> SpellNoDec: disabled (Torment's op146 special != 0 = ForceSpellRESNoFeedback).

## Open questions
- op146: if EEex's SpellNoDec mode is wanted on Torment, it needs another switch (e.g. a special bit Torment never
  sets would still hit Torment's `special != 0` test first): needs a design decision.
