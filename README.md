# EEex for Planescape: Torment EE

A port of [Bubb's EEex](https://github.com/Bubb13/EEex) v1.3.1 (with InfinityLoader) to
**Planescape: Torment: Enhanced Edition v3.2.2.0** (Steam build, x64, Lua 5.2).

Everything EEex does on BG2EE runs on Torment: the loader, the full pattern database, LuaBindings for Torment's
structs, EEex.dll, the whole Lua layer (hooks, opcodes 400-409, actions / triggers / objects, extended stats,
options menu, B3 modules) and a WeiDU installer. Torment's own behaviour is kept where it differs from BG.

**Download:** see the Releases page (`EEex-PSTEE-v1.3.1-pstee2.zip`: extract into the game folder, run
`setup-EEex.exe`, start the game with `InfinityLoader.exe`). Player readme: [installer/readme-EEex-PSTEE.txt](installer/readme-EEex-PSTEE.txt).

## Status

| Phase | |
|---|---|
| 1. Loader POC | done: upstream InfinityLoader binaries inject into Torment.exe unchanged |
| 2. Pattern DB | done: 821 ported, 13 proven absent in Torment, 0 unresolved ([PATTERNS.md](PATTERNS.md)) |
| 3. LuaBindings | done: Torment struct layouts solved from BG2EE types + code evidence; unproven bytes are opaque padding |
| 4. EEex.dll | done: every EEex.dll function audited against Torment's engine, Torment-specific rewrites ([AUDIT.md](AUDIT.md)) |
| 5. EEex Lua | done: all 188 hook sites reviewed and adapted; English + French strings |
| 6. Installer | done: WeiDU, same tp2 name / component numbers / labels as upstream (mods that check EEex work unchanged) |

Verification: in-game feature battery (triggers, objects, actions, extended stats, op400-409) and a scripted
game session (`tools/battery.py`: API sweep, companions, combat, every opcode extension, real casts, every player
spell, area travel, save / reload): **69 pass / 0 fail**. Details and every proof are in [AUDIT.md](AUDIT.md);
the work log is [PLAN.md](PLAN.md).

## Torment differences worth knowing (modders)

- EEex triggers use ids 0x4112..0x4115 (Torment already uses 0x410D..0x4110). Actions 472+ and objects 115+ keep
  their upstream numbers.
- Opcode 146: Torment already uses `special != 0` (no-feedback cast); EEex's SpellNoDec mode is special bit 1
  (value 2). Opcode 326: the flip is `special & 2` (as in upstream's EEex.dll; upstream's doc says bit 0).
- CGameEffect is 0x160 bytes in Torment (extra CResRef at +0x154), CGameSprite 0x52c8, CAIAction 0x80.
- Torment-only engine fix: a scripted `RestParty()` with a hurt party hangs the vanilla game (heal-on-rest loop with
  a heal amount of 0); EEex_Fix_Patch leaves the loop when no progress is possible.

Known limitations: casting off the op214 internal list from a keybind is disabled; 25 Torment-only projectile
decode sources report `nil`; op249 / op319 are code-verified only (no ranged attacker / usability item in the tests).

## Repository layout

- `tools/` — pattern porting pipeline, struct layout solver (`tools/bindings/`), audits, test drivers
  (`gamekey.py` sends keys to the game window with PostMessage, `battery.py` runs the session battery),
  `rebuild_all.sh` (header -> DLLs -> Lua), `package.py` (release zip).
- `poc/` — Torment `InfinityLoader.db`, extra pattern DB (`pstee.db`), profiler names.
- `bindings/` — LuaBindings-PSTEE project and generated header (`bindings/in/Torment-v3.2.2.0.h`); `bindings/test/`
  holds dev-only test scripts and resources (never shipped).
- `eeexdll/` — EEex.dll for Torment: upstream sources + `patch_sources.py` (Torment semantic patches) + `source/`.
- `eeexlua/` — the Lua port: upstream copy + `patches/*.py` (exact replacements), `src/` (Torment-only files),
  `notes/` (one review note per upstream file), `build.py [--deploy]`.
- `installer/` — WeiDU tp2, English / French tra, player readme.
- Not committed: `ref/` (upstream EEex and InfinityLoader clones), `ghidra/`, `build/`.

## Building

Needs Visual Studio (MSBuild, x64), Python 3 with capstone, the upstream clones in `ref/`, and a Torment v3.2.2.0
install for the dev deploy (path in `eeexlua/build.py` / `tools/deploy.py`).

```
sh tools/rebuild_all.sh [--deploy]
python tools/package.py
```

## Credits

EEex, InfinityLoader, LuaBindings and the B3 modules: Bubb. Torment port: sad0.
