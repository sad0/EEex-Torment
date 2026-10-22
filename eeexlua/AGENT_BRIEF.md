# Phase 5 brief: port EEex Lua hook files to Torment (PST:EE, Torment.exe)

EEex (a BG2EE engine extender, upstream Lua in `ref/EEex/EEex/copy/EEex_scripts/`) is being ported to
Planescape: Torment EE. The engine code is the same family as BG2EE, but Torment.exe is a different build:
different register allocation, struct offsets, inlining, and sometimes different code. EEex's Lua hooks
patch machine code at pattern labels, so every hook must be checked against Torment's code.

Already done (do NOT redo): every pattern label has a Torment address (`tools/gen_report.json`, `addr`);
`tools/port2.json` gives the BG2EE address (`bg_key`). The C++ side (EEex.dll, LuaBindings with Torment struct
layouts) is ported and tested. Labels like `EEex::Foo` / `CGameSprite::Override_X` used in `#L(...)` are
EEex.dll exports: fine. `#OFFSET_OF(Type.field)` uses the Torment bindings: fine (but check the field exists
in Torment: `bindings/` headers; if unsure, note it).

## Tools (run from `E:\Enhanced Edition\EEex-PSTEE\tools`, Python, read-only use)
- `python hookreview.py <File>.lua [before] [after]` -> for every hook of the file: hook call, registers and
  frame slots its code reads, a BG->Torment register map guess, issues, and BG / Torment instructions side by
  side (`*` = the hook address). The register map is a heuristic: always confirm by reading the code.
- `python hookview.py <label> [before] [after]` or `python hookview.py 0x<bg> 0x<pt> [before] [after]`.
- `python -c "from luahooks import *; ..."`: `insns(PT, rva, n)`, `func_body(PT, rva)` (whole function body,
  address order), `BG`, `PT` PE objects (`.read(rva, n)`, `.rfunc(rva)`).
- `python fdiff.py 0x<bg_func> 0x<pt_func>`: whole-function diff.
- `tools/luahooks.json`: the audit list (all hooks, issues). Do NOT re-run `luahooks.py` (shared output).
- Hook API semantics: `ref/EEex/EEex/copy/EEex_scripts/EEex_Assembly_x86-64.lua` (e.g. ConditionalJump hooks
  overwrite jcc + restoreSize bytes, needs >= 5; restored bytes are copied verbatim, so they must not contain
  RIP-relative operands or relative branches; Restore hooks: (address, restoreDelay, restoreSize, returnDelay)).

## What to check for EVERY hook (also the ones not flagged)
1. The Torment label is in the right function and at the equivalent instruction (compare contexts; if the
   label looks wrong, find the right Torment address and REPORT it: do not edit tools/manual.json).
2. Patched bytes: instruction kinds/lengths in the overwritten region (short vs near jcc, restore sizes,
   instruction boundaries, relocatable restored bytes, inverted conditions).
3. Every register / stack slot / frame slot (`[rbp-x]`, `[rsp+x]`, `#LAST_FRAME_TOP(x)`) the hook code reads or
   writes: what value it holds in BG at that point, and where that value is in Torment (trace the function).
   Registers the hook clobbers must be dead in Torment at that point too (e.g. rax after a call is overwritten
   before use?).
4. Hard-coded struct offsets in the assembly (`[rdi+0x1136]`): find the Torment offset (compare the engine
   code that uses the same field), or use `#OFFSET_OF`.
5. Function signatures of engine functions the hook calls or whose arguments it reads (Torment changed a few:
   AUDIT.md "Argument registers read by every bound engine function").
6. Semantics: if Torment's code differs (different branch structure, extra arguments, value used later),
   adapt the hook so Torment's behavior is preserved (example: SetCharacterToolTip in the reference patch).
Also read the WHOLE Lua file: hooks whose address comes from a variable / helper function, `EEex_Write*`,
`EEex_ForceJump`, vtable writes, `EEex_Label("Data-...")`, hard-coded constants that are BG engine values.

## Output (only these files; other sessions work in parallel on other Lua files)
- `eeexlua/patches/<LuaFileNameWithoutExt>.py` defining `PATCHES = [(old, new), ...]`: exact text
  replacements on the upstream file (each `old` must match exactly once; `'@all:N old'` = exactly N matches;
  `'@file'` = whole-file replacement, avoid). Comment each patch with the Torment evidence (PT addresses).
  Mark changed Lua lines with `-- EEex-PSTEE:` or `; EEex-PSTEE:` in asm. Torment-specific addresses relative
  to a label are OK (`EEex_Label("X") + 9` through a label pair, see reference).
  Reference example: `eeexlua/patches/EEex_Sprite_Patch.py`.
- `eeexlua/notes/<LuaFileNameWithoutExt>.md`: one line per hook (label, verdict: unchanged / patched /
  label wrong / not portable, evidence: PT addresses + registers). List separately: label fixes needed,
  BG-only features that cannot work in Torment (and what you did: disabled with a guard, etc.), open
  questions.
- Check your patches apply: `cd eeexlua && python build.py` (rebuilds eeexlua/generated; safe to run).
Do not edit anything else (no tools/*.json, no ref/, no game files). Do not launch the game. No git commits.
Be exhaustive and precise: the owner wants 100% coverage, no blind spots. Wrong registers crash the game.
