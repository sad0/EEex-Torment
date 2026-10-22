# EEex_Actionbar.lua: Torment button types (CInfButtonArray.m_buttonTypes, +0x1fb0) and actionbar states / configs.
# Evidence: notes/EEex_Actionbar.md. Summary:
#  - types 0..20 have the same meaning as BG (same OnLButtonPressed / UpdateButtons handlers and ENGINEST tooltips);
#  - Torment has 5 quick items (21..25), 3 quick spells (26..28), 5 quick weapons (29..33): OnLButtonPressed PT
#    0x2c6801 sub 0x15 / 0x2c6a13 sub 0x1a / 0x2c6b7e sub 0x1d (BG 0x15 / 0x18 / 0x1b), main switch byte table PT
#    0x2c73c8 (21..25 / 26..28 / 29..33);
#  - type 70 is Torment-only: a character special ability of the PST "special abilities" context bar (state 118).
#  - THIEVING stays 12 (PT 0x2c6e2e mov edi, 0xc -> m_nSelectedButton; thieving hotkey PT 0x35d040 edx = 0xc), so
#    EEex_Actionbar_Hook_IsPartyLeader is unchanged; EEex_Actionbar_Hook_HasFullThieving's class 5 is Torment's own
#    test too (PT 0x2c6e0f cmp al, [0x61f29e] = 5; PST CLASS.IDS 5 = BARD).
#  - No BG value is dropped: every upstream name exists in Torment's handlers.
PATCHES = [
    # GetState docs: Torment-only states 115..121 (names from Torment's BGEE.lua `const` table:
    # ACTIONBAR_STATE_WEAPONS = 115 .. ACTIONBAR_STATE_PST_TABLET_MISC = 121). The class states 1..21 keep BG's
    # meaning (PST CLASS.IDS = BG's list, same SetState layouts), but Torment's engine never selects them:
    # CInfGame::SelectToolbar (PT 0x2f24ec) calls the context-bar refresh (PT 0x25a1e0) when ENGINE_MODE == 3.
    ('''-- | 114   | Cleric / Mage Spells (Select Quick Spell)         |
-- +-------+---------------------------------------------------+
''',
     '''-- | 114   | Cleric / Mage Spells (Select Quick Spell)         |
-- +-------+---------------------------------------------------+
-- | 115   | Torment: Weapons context bar                      |
-- +-------+---------------------------------------------------+
-- | 116   | Torment: Spells context bar                       |
-- +-------+---------------------------------------------------+
-- | 117   | Torment: Items context bar (Quick Items 1-5)      |
-- +-------+---------------------------------------------------+
-- | 118   | Torment: Special Abilities context bar            |
-- +-------+---------------------------------------------------+
-- | 119   | Torment: Formations context bar                   |
-- +-------+---------------------------------------------------+
-- | 120   | Torment: Tablet "football" menu                   |
-- +-------+---------------------------------------------------+
-- | 121   | Torment: Tablet misc menu                         |
-- +-------+---------------------------------------------------+
--
-- EEex-PSTEE: states 115-121 are Torment's (const.ACTIONBAR_STATE_*). Torment's engine never selects the class
-- states 1-21 itself (the PST UI uses its own bar + the context bar states), but they can still be set.
''',
     ),
    # Button types: Torment values (notes/EEex_Actionbar.md).
    ('''	["QUICK_ITEM_1"] = 21,
	["QUICK_ITEM_2"] = 22,
	["QUICK_ITEM_3"] = 23,
	["QUICK_SPELL_1"] = 24,
	["QUICK_SPELL_2"] = 25,
	["QUICK_SPELL_3"] = 26,
	["QUICK_WEAPON_1"] = 27,
	["QUICK_WEAPON_2"] = 28,
	["QUICK_WEAPON_3"] = 29,
	["QUICK_WEAPON_4"] = 30,
	["NONE"] = 100,
}''',
     '''	-- EEex-PSTEE: Torment has 5 quick items, 3 quick spells and 5 quick weapons (PT 0x2c73c8: 21..25 / 26..28 / 29..33)
	["QUICK_ITEM_1"] = 21,
	["QUICK_ITEM_2"] = 22,
	["QUICK_ITEM_3"] = 23,
	["QUICK_ITEM_4"] = 24,     -- EEex-PSTEE: Torment-only
	["QUICK_ITEM_5"] = 25,     -- EEex-PSTEE: Torment-only
	["QUICK_SPELL_1"] = 26,    -- EEex-PSTEE: BG 24
	["QUICK_SPELL_2"] = 27,    -- EEex-PSTEE: BG 25
	["QUICK_SPELL_3"] = 28,    -- EEex-PSTEE: BG 26
	["QUICK_WEAPON_1"] = 29,   -- EEex-PSTEE: BG 27
	["QUICK_WEAPON_2"] = 30,   -- EEex-PSTEE: BG 28
	["QUICK_WEAPON_3"] = 31,   -- EEex-PSTEE: BG 29
	["QUICK_WEAPON_4"] = 32,   -- EEex-PSTEE: BG 30
	["QUICK_WEAPON_5"] = 33,   -- EEex-PSTEE: Torment-only
	-- EEex-PSTEE: Torment-only, an entry of the special abilities context bar (state 118). Its icon / action come
	-- from a per-button list that only state 118 fills (PT 0x25a810), so it is not useful on other states.
	["CHARACTER_ABILITY"] = 70,
	["NONE"] = 100,
}''',
     ),
    # SetButton docs: list the Torment-only names.
    ('''-- | QUICK_ITEM_3      |
-- +-------------------+
''',
     '''-- | QUICK_ITEM_3      |
-- +-------------------+
-- | QUICK_ITEM_4      |
-- +-------------------+
-- | QUICK_ITEM_5      |
-- +-------------------+
''',
     ),
    ('''-- | QUICK_WEAPON_4    |
-- +-------------------+
''',
     '''-- | QUICK_WEAPON_4    |
-- +-------------------+
-- | QUICK_WEAPON_5    |
-- +-------------------+
-- | CHARACTER_ABILITY |
-- +-------------------+
''',
     ),
    # AddListener docs: Torment configs 31..37 = states 115..121; 38 = default (PT byte table 0x2ca438).
    ('''-- | 30     | 113, 114        |
-- +--------+-----------------+
''',
     '''-- | 30     | 113, 114        |
-- +--------+-----------------+
-- | 31     | 115             |
-- +--------+-----------------+
-- | 32     | 116             |
-- +--------+-----------------+
-- | 33     | 117             |
-- +--------+-----------------+
-- | 34     | 118             |
-- +--------+-----------------+
-- | 35     | 119             |
-- +--------+-----------------+
-- | 36     | 120             |
-- +--------+-----------------+
-- | 37     | 121             |
-- +--------+-----------------+
-- | 38     | any other state |
-- |        | in 1-121        |
-- +--------+-----------------+
--
-- EEex-PSTEE: Torment configs 31-37 are its context bar states. Config 38 (BG 31) is the default case; unlike
-- BG it leaves the buttons and m_nState unchanged. States outside 1-121 give config -1.
''',
     ),
    # Hook docs: same list.
    ('''    [30]      |  = 113, -- Cleric / Mage Spells (Cast)
              |    114, -- Cleric / Mage Spells (Select Quick Spell)
              |
--]]''',
     '''    [30]      |  = 113, -- Cleric / Mage Spells (Cast)
              |    114, -- Cleric / Mage Spells (Select Quick Spell)
              |
    EEex-PSTEE: Torment-only configs (PT 0x2ca438):
    [31]      |  = 115, -- Weapons context bar (quick weapons, Guard)
    [32]      |  = 116, -- Spells context bar (spell list)
    [33]      |  = 117, -- Items context bar (Quick Items 1-5)
    [34]      |  = 118, -- Special Abilities context bar (Find Traps / Thieving / Stealth, character abilities)
    [35]      |  = 119, -- Formations context bar
    [36]      |  = 120, -- Tablet "football" menu
    [37]      |  = 121, -- Tablet misc menu
    [38]      |  = default (BG 31), buttons and state left unchanged
--]]''',
     ),
]
