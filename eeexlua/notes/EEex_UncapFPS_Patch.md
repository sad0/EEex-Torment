# EEex_UncapFPS_Patch.lua (Torment review)

Patch: `patches/EEex_UncapFPS_Patch.py` (3 changes, identical to the phase 4d in-game test
`bindings/test/make_uncap_test.py` -> `PTEE_UncapTest.lua`; the generated file was diffed against it: only comments
differ). The C++ overrides/hooks are the phase 4d ports (eeexdll uncap_fps.cpp, AUDIT.md "Uncap FPS").

| Line | Hook / label | Verdict | Evidence |
|---|---|---|---|
| 14 | JITAt Hook-CChitin::Update()-FirstInstruction | unchanged | PT 0x4a6350 = function start, same prologue as BG 0x41cac0 |
| 24 | CondJumpOnFail Hook-CScreenWorld::OnEvent()-OnHandleMiddleMouseDragJmp | **patched** (restore 0 -> 7) | PT 0x35ba0a `je` is short (2 bytes; BG near, 6). Restored `add rbx, 0x5d8` (PT 0x35ba0c, 7 bytes, relocatable). pEvent = rdi in both (PT 0x35ba4b `add r8d, [rdi+0x1c]`; hookreview's rdi->rbp guess is wrong). The replaced fail block = BG's (+ Torment's window->screen conversion, done in C++). Success target PT 0x35b9b6 reads rdi/r14 only (callee-saved) |
| 45 | JITAt Hook-CInfinity::AdjustViewPosition()-FirstInstruction | unchanged | PT 0x302090 function start |
| 57 | JITAt Hook-CInfinity::Scroll()-FirstInstruction | unchanged | PT 0x3084d0 |
| 58 | JITAt Hook-CInfinity::SetScrollDest()-FirstInstruction | unchanged | PT 0x309450 function start (body differs: cinematic check, handled in C++) |
| 59 | JITAt Hook-CScreenWorld::StartScroll()-FirstInstruction | unchanged | PT 0x366ac0 |
| 78 | ForceJump Hook-CScreenMap::TimerAsynchronousUpdate()-ScrollHandlingJmp | unchanged | PT 0x33cb23 near `je` (6 bytes), same `cmp eax, 8` context |
| 81 | ForceJump Hook-CScreenWorld::AsynchronousUpdate()-AutoZoomJmp | unchanged | PT 0x353b8f near `je` (6 bytes), same auto-zoom flag test `[rcx+0xc58]` (BG 0xba8) |
| 83 | JITAt Hook-CScreenWorld::ResetZoom()-FirstInstruction | unchanged | PT 0x363080 leaf, function start (option test inverted in PT: handled in C++) |
| 84 | JITAt Hook-CScreenWorld::ZoomToMap()-FirstInstruction | unchanged | PT 0x3686e0 function start |
| 86 | JITAt Hook-CGameArea::RenderZoomed()-FirstInstruction | unchanged | PT 0x19f8a0 |
| 99 | HookBeforeCall Hook-CGameArea::OnMouseMove()-OnAfterAreaEdgeScrollPossiblyStarted | unchanged | PT 0x19e032 `call 0x4a3aa0` (= BG 0x41a1a0, one-argument getter; the hook saves rcx). rbx = CGameArea (PT 0x19d825 `mov rbx, rcx`, never rewritten in the body); same `[rbx+0x230]` scroll-state writes before the site |
| 134 | JITAt Hook-CInfinity::FitViewPosition()-FirstInstruction | unchanged | PT 0x304c20 function start |
| 135 | JITAt Hook-CScreenMap::CenterViewPort()-FirstInstruction | unchanged | PT 0x33ab90 |
| 137 | HookBeforeCall Hook-CScreenWorld::EngineDeactivated()-FirstCall | unchanged | PT 0x35802d `call 0x4585f0` (= BG 0x3d9310): takes no argument (its body reads no rcx/rdx before its own calls), so the clobbered volatiles are fine |
| 156 | JITAt Hook-Infinity_TransitionMenu()-FirstInstruction | unchanged | PT 0x44a1f0 |
| 158 | CondJumpOnFail Hook-drawTop()-HandleTransitionMenuFadeJmp | unchanged | PT 0x4521f3 near `jle` (6 bytes, restore 0 ok); fade block PT 0x4521f9..0x4522e2 identical to BG; success target PT 0x4522e4 `xor al, al` + epilogue (no volatile read) |
| 179 | RelativeJump Hook-CGameArea::OnActivation()-LastCall | **patched** -> HookAfterCall, `mov rcx, rdi` | BG tail `jmp` (pArea in rdx); PT 0x19d3ca is `call 0x33c6e0` (= BG 0x2d4df0) followed by Torment code, so HookRelativeJump would refuse it (not E9). pArea = rdi (PT 0x19cfce `mov rdi, rcx`, 0x19d3c0 `mov rdx, rdi`, read again at 0x19d3d4). Volatiles are written before being read after the call; rax unused |
| 202 | HookBeforeRestore Hook-CGameArea::OnDeactivation()-FirstInstruction (0,6,6) | unchanged | PT 0x19d450 `push rbx; sub rsp, 0x20` = the same 6 bytes; rcx = pArea |
| 228 | JITAt Hook-CScreenWorld::EndDialog()-FirstInstruction | unchanged | PT 0x357830 |
| 240 | JITAt Hook-CInfinity::SetScreenShake()-FirstInstruction | unchanged | PT 0x3093d0 leaf, same code (fields 0x424.. vs BG 0x46c..) |
| 242 | CondJumpOnFail Hook-CInfinity::Render()-HandleScreenShakeJmp | unchanged | Torment moved the block into helper PT 0x3078c0 (called from the area render, PT 0x19e707). PT 0x307908 near `jne` (6 bytes, restore 0 ok). rbx = CInfinity (PT 0x3078d3). Success = helper epilogue PT 0x307a40 (caller ignores rax). The skipped fail path's Torment saved-position fields (+0x454/+0x458) are only read by the post helper's fail path, which is hooked too (whole-exe scan) |
| 255 | CondJumpOnFail Hook-CInfinity::Render()-HandleScreenShakePostJmp | **patched** (restore 3 -> 0) | PT 0x307a88 near `jne` (BG: short + 3 restored bytes `mov eax, [rbp-0x39]`, a BG local absent in PT). rbx = CInfinity (PT 0x307a5d); success = helper epilogue PT 0x307b0e (caller PT 0x19efd6 ignores rax) |
| 280 | HookAfterCall Hook-CVidMode::SetDisplayMode()-DrawInit() | unchanged | PT 0x4a0265 `call 0x49c480` (= BG DrawInit 0x4133a0); `test al, al` follows in both; the hook preserves rax |
| 303 | JITAt Hook-CVidTile::RenderTexture()-FirstInstruction | unchanged | PT 0x4aed20 function start |
| 313 | JITAt Hook-uiDrawMenuStack()-FirstInstruction | unchanged | PT 0x456f60 function start (body differs: Torment UI rect, handled in C++) |
| 321 | JITAt Hook-CChitin::SynchronousUpdate()-CVidMode::Flip() | unchanged | PT 0x4a62b2 tail `jmp 0x4a6f20` (5 bytes, = BG Flip 0x41d8d0, fdiff 1.000) after `pop rbx`: `ret` + 4 nop fits exactly |
| 332 | JITAt Hook-CChitin::WinMain()-FirstInstruction | unchanged | PT 0x4a65c0 |
| 340 | JITAt Hook-DrawReadPixels()-FirstInstruction | unchanged | PT 0x49c530 |

No hard-coded struct offsets or BG constants in the file's assembly (the line-269 debug write is commented out).
All JIT targets are PT .pdata function starts (or leaf functions) with no branch into the patched head.

## Label fixes needed
None.

## BG-only features
None in this file.

## Open questions
- OnActivation: the hook now runs right after Torment's map-engine call, before Torment's extra tail
  (PT 0x19d3d4 `[rdi+0x1130] = r15d`, then conditional calls 0x2572d0 / 0x2f2df0). BG had nothing after the
  map-engine call. Tested OK in game (phase 4d); it only matters when the local map is open during an area change.
- EEex_UncapFPS.lua (not this file): the AI-speed option default must be Torment's 40 (AUDIT.md).
