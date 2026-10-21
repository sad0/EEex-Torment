# EEex_LuaBindings_Patch.lua (Torment review)

No patch needed (already loaded and working in game through bindings/test/EEex_Main.lua).

| Label (JITAt -> override_<name>) | PT | Verdict |
|---|---|---|
| class_index_event | 0x11f5c0 | unchanged: = BG 0x111b50, fdiff 1.000 |
| class_newindex_event | 0x11f8e0 | unchanged: = BG 0x111e70, 1.000 |
| module_index_event | 0x11fc20 | unchanged: = BG 0x1121b0, 1.000 |
| module_newindex_event | 0x11fd70 | unchanged: = BG 0x112300, 1.000 |
| tolua_beginmodule | 0x120cc0 | unchanged: = BG 0x113250, 1.000 |
| tolua_cclass | 0x121090 | unchanged: = BG 0x113620, 1.000 |
| tolua_module | 0x121360 | unchanged: = BG 0x1138f0, 1.000 |
| tolua_open | 0x121510 | unchanged: = BG 0x113aa0, 1.000 |
| tolua_usertype | 0x1219f0 | unchanged: = BG 0x113f80, 1.000 |

All are PT .pdata function starts with no branch into the patched head.
