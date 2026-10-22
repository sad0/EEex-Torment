# EEex_Key_Patch.lua: CChitin::ProcessEvents (PT 0x4a5100). Both SDL_PollEvent hook sites (PT 0x4a5139, 0x4a5e2a)
# are the same calls as in BG (lea rcx, <event>; call SDL_PollEvent; test eax, eax), but Torment's frame keeps the
# SDL_Event at [rbp-0x49] (PT 0x4a5135 / 0x4a5e26 lea rcx, [rbp-0x49]; BG [rbp-0x51]). rbp is the same value at
# both sites (one function, fixed frame), and the shared JIT helper is called (not jumped to), so rbp is still the
# ProcessEvents frame pointer inside it.
PATCHES = [
    ('''					lea rcx, qword ptr ds:[rbp-51h]''',
     '''					lea rcx, qword ptr ds:[rbp-49h] ; EEex-PSTEE: Torment's SDL_Event slot (PT 0x4a5135)'''),
]
