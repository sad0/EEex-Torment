EEex for Planescape: Torment Enhanced Edition
=============================================

A port of Bubb's EEex v1.3.1 (https://github.com/Bubb13/EEex) to Planescape: Torment EE v3.2.2.0.
EEex extends the Infinity Engine for modders (new opcodes, actions, triggers, objects, extended stats,
Lua access to the engine) and adds optional quality-of-life modules.

Requirements
------------
- Planescape: Torment: Enhanced Edition v3.2.2.0, Steam build (Torment.exe, 8028040 bytes).
  The installer refuses any other executable: EEex patches the engine in memory and each build differs.
- Windows x64.

Install
-------
1. Extract the archive into the game folder (where Torment.exe is).
2. Run setup-EEex.exe and pick "Minimal" or "Full" (Full turns every optional module on).
3. Start the game with InfinityLoader.exe from the game folder. Torment.exe (and Steam's Play
   button) still starts the game without EEex.

Some antivirus tools flag InfinityLoader.exe because it injects EEex into the game process. It is
Bubb's upstream loader, unchanged.

Uninstall: run setup-EEex.exe again and uninstall the components; WeiDU restores every file.

Components
----------
- EEex (main): engine extensions for modders; EEex Options menu (Options > Game > EEex Options).
- Optional modules, each can be turned on or off later in EEex Options:
  attack info, effect menu (hold Left Shift over a creature), empty containers, hotkeys,
  UI scale (a percentage), time step, timers on the party portraits.
- Not offered: upstream's experimental LuaJIT component (never tested on Torment).

Torment differences
-------------------
- EEex triggers use ids 0x4112..0x4115 (Torment already uses 0x410D..0x4110); EEex actions 472+ and
  objects 115+ keep their upstream numbers. Scripts compiled against the installed IDS files are fine.
- Opcode 146 (Cast Spell): Torment's own "special" value 1 keeps its meaning (no feedback);
  EEex's no-decrement mode is special bit 2 (value 2).
- Timers sit against each party portrait (Torment's horizontal portrait row).
- Interface: Torment buttons, scrollbars and toggles; English and French strings.

Known limitations
-----------------
- Keybinds / hotkey module: casting a spell that is not in the creature's internal spell list is disabled.
- 25 Torment-only projectile decode sources report a nil decodeSource to projectile mutators (op408).
- Extensions of existing opcodes (101, 148, 214, 248, 249, 280, 326, 333, 342) are verified in the code
  but were not exercised in game.

Credits
-------
EEex, InfinityLoader and the B3 modules: Bubb. Torment port: sad0.
