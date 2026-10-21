# EEex_Debug_Patch.lua (Torment; hooks installed only with EEex_Debug_LogActions / EEex_Debug_LogFontWraps)

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-CGameAIBase::ExecuteAction()-DefaultJmp` (BeforeConditionalJump, restore 0) | **patched** | PT 0x16c99c near `ja 0x172220` (6 bytes). this in **rdi** (PT 0x16c914; BG rbx). r8 (switch index) saved and `cmp r8d, 0x1D5` rebuilt as in Torment (PT 0x16c995). After the ja Torment writes r14 / rax / rcx before use; the default case writes rdx / rcx; rdx and r9..r11 are undefined on the `jne` path (PT 0x16c960), so the upstream ignore list stays valid. |
| `Hook-CGameSprite::ExecuteAction()-DefaultJmp` (BeforeConditionalJump, restore 0) | **patched** | PT 0x40bd90 near `ja 0x40e653`. Sprite rdi (as BG). Torment's switch: `movsx rax, r8w; cmp eax, 0x1d7` and indexes with rax (PT 0x40bd87..0x40bd9d); BG used rcx. Live across the jcc in Torment: rax, rdx (word, used PT 0x40bdb9), r8 (action id), r9 (global pointer, used PT 0x40bdc4); r10 written right after, rcx before use. The hook now saves rax / rdx / r8 / r9 (was rcx / rdx / r9 / r10) and rebuilds the flags with `cmp eax, 0x1D7`. |
| `Hook-fontWrap()-FirstInstruction` (JITAt -> EEex::Override_fontWrap) | unchanged | PT 0x4cbb40 function start (123 bytes), same prologue; AUDIT.md: fontWrap reimplementation valid (1.00). |

Label fixes / BG-only features / open questions: none.
