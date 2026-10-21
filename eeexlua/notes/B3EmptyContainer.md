# B3EmptyContainer.lua (Torment review)

| Hook (label) | Verdict | Evidence |
|---|---|---|
| Hook-CGameContainer::Render()-B3EmptyContainer | unchanged | PT 0x1aaed5 (BG 0x194deb): same outline call (PT 0x305e50, 5 args). Container in r14 (PT 0x1aaeb8 mov rdx, [r14+0x548], 0x1aaece lea r9, [r14+0x538]); color = 5th argument at [rsp+0x20] (PT 0x1aaeb4), read through #LAST_FRAME_TOP(32). Same color constants (0xff00 trap/selected, 0xffff00 default) as BG. rcx / rdx / r8 / r9 saved and restored; stack slot 0x20 watchdog exception unchanged. |

Label fixes needed: none. BG-only features: none.
Lua side: CGameContainer.m_lstItems.m_nCount via the Torment bindings. The grey 0x808080 for empty containers is cosmetic.
