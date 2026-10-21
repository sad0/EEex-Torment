# EEex_CrashHandler_Patch.lua (Torment review)

No patch needed.

| Label | Verdict | Evidence |
|---|---|---|
| Hook-WinMain$filt$0-FirstInstruction (JITAt -> EEex::Override_crashHandler) | unchanged | PT 0x6191f0 = BG 0x586ad0, fdiff 1.000 (11/11): same SEH filter (`push rbp; sub rsp, 0x20; lea rbp, [rdx+0x20]`, rcx = EXCEPTION_POINTERS*); the engine handler it calls is identical too (BG 0x567840 / PT 0x5f9ff0, 1.000) |
