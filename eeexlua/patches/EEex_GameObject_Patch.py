# EEex_GameObject_Patch.lua: no change needed.
# CGameObjectArray::Delete (PT 0x2d7020) is BG's code: the object id is in ebp (PT 0x2d7027 mov ebp, edx), the hooked
# jcc is a short je (PT 0x2d707f, 2 bytes) and the 5 restored bytes are mov rdi, [rsp+0x48] (PT 0x2d7081, not
# RIP-relative); the success target (PT 0x2d7094) is the same delete path.
PATCHES = []
