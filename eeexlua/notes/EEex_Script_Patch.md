# EEex_Script_Patch.lua (Torment)

| Hook / label | Verdict | Evidence |
|---|---|---|
| `Hook-CAIScript::Read()-OnRead` (AfterCall) | unchanged | PT 0x12d2e6 in CAIScript::Read PT 0x12d240 (same code as BG). Script rsi (PT 0x12d26e `mov rsi, rcx`), bPlayerScript r14 (PT 0x12d26b `mov r14d, r8d`, next write PT 0x12d5f8 after the site). rax overwritten right after the call (PT 0x12d2eb). |
| `Hook-CAIScript::Construct()-OnCopy1` / `-OnCopy2` (BeforeCall) | **not portable -> guarded** | Unsupported labels (PATTERNS.md): Torment's CAIScript::Construct (PT 0x176d80) has no script-cache copy path, it always parses through CAIScript::Read, so OnRead already tags every script. The loop now skips a label that `EEex_TryLabel` does not know (EEex_Label would abort loading). |
| `Hook-CAIScript::Destruct()-OnDestruct` (AfterCall) | unchanged | PT 0x12cf48 (CPtrList destructor call), script rsi (PT 0x12cefe); rax unused afterwards (tail jmp). |

## BG-only features
- Script-cache copy tracking (OnCopy): no equivalent in Torment, not needed.

Label fixes / open questions: none.
