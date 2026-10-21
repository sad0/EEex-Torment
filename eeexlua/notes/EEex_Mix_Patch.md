# EEex_Mix_Patch.lua (Torment): CGameSprite::Swing (PT 0x4334e0) weapon-immunity hooks

Frame map BG -> PT (from the shared loads and Hit() arguments): weapon item `[rsp+0x58]` -> `[rbp-0x68]` (PT 0x433766),
ability `[rsp+0x68]` -> `[rbp-0x70]` (PT 0x4337dd; tested for type 2 at PT 0x433ddc as BG `[r13]`), launcher item
`[rsp+0x70]` -> `[rbp-0x60]` (PT 0x433810), word `[rsp+0x50]` -> `[rbp-0x7c]`; attacker rbx (PT 0x433522), target r15
(PT 0x4336a9), r13 = target + 0xC (PT 0x43383f). rbp is the frame pointer (PT 0x4334f0), never rewritten.

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-CGameSprite::Swing()-CImmunitiesWeapon::OnList()-Melee` (AfterCall) | **patched** | PT 0x434296 (call PT 0x21c0e0). Torment passes the weapon to Hit() straight from `[rbp-0x68]` (PT 0x434215; BG r12) -> weapon `[rbp-0x68]`, ability `[rbp-0x70]` (BG `#LAST_FRAME_TOP(68h)`). Same polarity after the call (PT 0x43429d `jne` immune). |
| `Hook-CGameSprite::Swing()-CImmunitiesWeapon::OnList()-Ranged` (AfterCall) | **patched + second site** | BG has one ranged block (the missing-projectile case decodes then jumps back, BG 0x3b90f0); Torment duplicates the block: OnList at PT 0x433eb2 (label) and PT 0x433fb8 (= label + 0x106, after DecodeProjectile PT 0x433f43). Both are hooked (second site checked at load: E8 call to the same target). Weapon in r12 (PT 0x433e6f / 0x433f75; BG rdi), ability `[rbp-0x70]`. |
| `Hook-CGameSprite::Swing()-NoCImmunitiesWeaponElseContinue` | used, boilerplate patched | PT 0x4340bc `mov r8, rdi; mov rdx, r12; mov rcx, rbx` (BG `mov r8, rsi; mov rdx, rdi`). Both Torment immune blocks end with `mov rdi, [rbp-0x60]; jmp 0x4340bc` (PT 0x433f28 / 0x43402a), so the skip boilerplate is `mov rdi, [rbp-0x60]` (BG `mov rsi, [rsp+0x70]; lea r13, [r15+0xC]`; r13 already holds target + 0xC in Torment). |

## Torment differences kept
- Torment's immune feedback is also skipped for action 0x191 (PT 0x433ecc); the hook skips the whole block like upstream.
- Torment calls Hit() with the same arguments in both ranged copies; the miss path (`je 0x433f1c` / `0x43401e`) is shared with the immune tail, not hooked (as in BG).

Label fixes / open questions: none.
