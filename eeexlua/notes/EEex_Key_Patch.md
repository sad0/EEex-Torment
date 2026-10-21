# EEex_Key_Patch.lua (Torment review)

| Hook (label) | Verdict | Evidence |
|---|---|---|
| Hook-CChitin::ProcessEvents()-SDL_PollEvent()-1 | patched | PT 0x4a5139 (BG 0x41b8ac): same `lea rcx, <event>; call SDL_PollEvent; test eax, eax` loop head. Torment's SDL_Event is at [rbp-0x49] (PT 0x4a5135; BG [rbp-0x51]): the shared JIT helper reads `lea rcx, [rbp-49h]`. The helper is called (not jumped to), so rbp is ProcessEvents' frame pointer. |
| Hook-CChitin::ProcessEvents()-SDL_PollEvent()-2 | patched (same helper) | PT 0x4a5e2a (BG 0x41c60b): `lea rcx, [rbp-0x49]` at PT 0x4a5e26, same function / frame. Return-value semantics unchanged (PT 0x4a5e2f test eax, eax; jne loop). |

Label fixes needed: none (ProcessEvents label already corrected to PT 0x4a5100 in phase 4).
BG-only features: none.
Open questions: none (SDL_Event layout is SDL2's, same DLL family).
