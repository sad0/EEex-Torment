# EEex_Main.lua (Torment review)

No patch needed for its label use. (The startup-file and module lists are covered by the other files' reviews.)

| Line | Label | Verdict | Evidence |
|---|---|---|---|
| 138 | Write32 Data-EngineConsoleAttachedPtr = 0 | unchanged | DB pattern `40554883EC30488D6C2430` (ADD 13, rip-relative) is unique in PT at 0x4d0de0 = fmap counterpart of BG 0x447fa0. The first instruction after the prologue, `cmp dword ptr [rip+...], 0`, gives PT 0x641b850 (.data; BG 0x34b45e0). Function body identical (SDL console attach check: same `jne`, GetStdHandle(-1), file types 6 / 0x1f / 5) |
