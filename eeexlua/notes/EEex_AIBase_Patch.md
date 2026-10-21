# EEex_AIBase_Patch.lua (Torment)

| Label | Verdict | Evidence |
|---|---|---|
| `Hook-CGameAIBase::ApplyTriggers()-FirstInstruction` -> CGameAIBase::Override_ApplyTriggers | unchanged | PT 0x1640c0 = .pdata function start (191 bytes), fmap prop0 from BG 0x155570; AUDIT.md: EEex.dll reimplementation valid (code identical, only jump-table data differs). |
| `Hook-CGameAIBase::SetTrigger()-FirstInstruction` -> Override_SetTrigger | unchanged | PT 0x175df0 function start (88 bytes), fmap sig; AUDIT.md valid. |
| `Hook-CMessageSetLastObject::Run()-FirstInstruction` -> Override_Run | unchanged | PT 0x2384a0 function start (642 bytes), fmap fuzzy 1.00; AUDIT.md valid. |

JITAt writes a jmp (at most 14 bytes) over a function that is entirely replaced: no restore, no register concerns.

Label fixes / BG-only features / open questions: none.
