# EEex_Action_Patch.lua (Torment)

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-CGameAIBase::ExecuteAction()-DefaultCase` (BeforeRestore) | **patched** | PT 0x172220 (default of the 0x1d5-case switch, only reached from the `ja` PT 0x16c99c). this in **rdi** (PT 0x16c914 `mov rdi, rcx`; BG rbx). esi = -2 (PT 0x16c944) and the Lua result goes to esi as in BG; `Hook-...-NormalBranch` PT 0x172234 stores si / ebx (rbx = 0 there, PT 0x16c912 / 0x16c987, = BG r13 = 0). The 7 overwritten bytes are `lea rdx, [rip+X]` (RIP-relative; upstream restores it verbatim, only on the Lua-error path, giving a wrong string): Torment hook restores nothing (0,0,7) and the error path loads the string address computed from the original displacement before returning to PT 0x172227 (`lea rcx, [rbp-0x80]; call` CString assign). Bytes checked at load. |
| `CGameSprite::SetCurrAction()-LastCall` (AfterCall) | **patched (hook type)** | Known phase-5 case. Torment has no CString local, so no last call: label PT 0x42bbd1 is the epilogue start `mov rbx, [rsp+0x48]` (5 bytes, relocatable) reached by all paths (fallthrough, PT 0x42b9cd, 0x42bbc9; single ret PT 0x42bbe9). Replaced by BeforeRestore(0,5,5) before it. Sprite in **rbx** (PT 0x42b632, only write; BG rdi), action in **rsi** (PT 0x42b62f, only write; BG r14). rsp 16-aligned (3 pushes + 0x20), the callee's home space is the function's own outgoing area; volatile registers dead (void function). NoAction id 0 at offset 0 as in Torment's own compares (PT 0x42b669). |

## Label fixes needed
- none (`CGameSprite::SetCurrAction()-LastCall` stays at PT 0x42bbd1, used by a restore hook now).

## BG-only features
- none.
