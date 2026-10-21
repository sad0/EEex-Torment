# B3Invis.lua (Torment review)

| Hook (label) | Verdict | Evidence |
|---|---|---|
| Hook-CGameSprite::IsOver()-B3Invis | unchanged | PT 0x3d1ab9 (BG 0x35f859): short jbe + 7 restored bytes `cmp byte ptr [rbx+0x3c8d], 0` (relocatable; flags reach the next `je` PT 0x3d1ac2 unchanged). rbx / rdi preserved; rax / rcx rewritten on both paths (PT 0x3d1acb / 0x3d1ae9). No jump target inside the patched bytes. |
| Hook-CGameSprite::RenderMarkers()-B3Invis1 | patched | PT 0x3e1b2f (BG 0x36f261): short jbe + 7 bytes `cmp byte ptr [rsi+0x3c8d], dil`. Torment keeps the area ([rsi+0x18]) in r8 (PT 0x3e1add, read at PT 0x3e1be7 mov eax, [r8+0x654]); BG keeps it in r9. Hook saves / restores r8 instead of r9 (r9 dead in PT until 0x3e1e15); watchdog ignore list R8 -> R9. |
| Hook-CGameSprite::Render()-B3Invis | patched (upstream bug) | PT 0x3dd99e (BG 0x36bb70): near jne (0F 85, 6 bytes). Restore 6 -> 0: the restored `test ecx, ecx` (PT 0x3dd9a4) is the target of PT 0x3dd98f jbe / 0x3dd998 je; with 6 restored bytes it became a NOP and those paths skipped `cmove rbx, r13` (rbx stays 0x11e0 from PT 0x3dd87b instead of 0x1e90). Same latent bug in BG (0x36bb76). rcx / rdx saved; r8 / r9 / rax rewritten before use (PT 0x3dd9b6 / 0x3dd9bb / 0x3dda50). |
| Hook-CGameSprite::RenderMarkers()-B3Invis2 | patched | PT 0x3e1bb5 (BG 0x36f2ea), only when B3Invis_Private_RenderAsInvisible = false. 6 restored bytes `mov eax, [rcx+0xb558]` (relocatable); flags of PT 0x3e1bae cmp; sprite in rsi (PT 0x3e1b73 test [rsi+0x570]); rcx / rdx / rax saved. Area in r8 -> save / restore r8 (BG r9); watchdog ignore R8 -> R9. |

Label fixes needed: none.
BG-only features: none.
Lua side: CGameSprite.m_bInvisible and CDerivedStats.m_bSeeInvisible exist in the Torment bindings.
Open questions: Torment's "invisible" test (`[sprite+0x38] > global` and `[sprite+0x3c8d]`) has the same shape as BG's; op193 (see invisible) semantics in PST data not checked here.
