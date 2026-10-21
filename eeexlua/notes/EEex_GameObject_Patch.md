# EEex_GameObject_Patch.lua (Torment)

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-CGameObjectArray::Delete()-DeleteJmp` (ConditionalJumpOnSuccess, restore 5) | unchanged | PT 0x2d707f in CGameObjectArray::Delete PT 0x2d7020 (BG code). Short `je 0x2d7094` (2 bytes) + 5 restored bytes `mov rdi, [rsp+0x48]` (PT 0x2d7081, not RIP-relative) = 7 >= 5. Object id in ebp (PT 0x2d7027 `mov ebp, edx`); rcx / rdx saved by the hook; the success target is the same delete path. |

Label fixes / BG-only features / open questions: none.
