# B3Scale.lua: owner request, the scale option is a whole percentage 0..100 instead of a decimal 0..1 (new INI key so
# an old decimal value is not read as a percentage; the public B3Scale_SetPercentage keeps its [0-1] argument).
PATCHES = [
    ('''	["default"]  = 1,
	["type"]     = EEex_Options_EditType.new(),
	["accessor"] = EEex_Options_ClampedAccessor.new({ ["min"] = 0, ["max"] = 1, ["floating"] = true }),
	["storage"]  = EEex_Options_NumberLuaStorage.new({ ["section"] = "EEex", ["key"] = "Scale Module: Percentage" }),''',
     '''	["default"]  = 100, -- EEex-PTEE: percent
	["type"]     = EEex_Options_EditType.new(),
	["accessor"] = EEex_Options_ClampedAccessor.new({ ["min"] = 0, ["max"] = 100 }),
	["storage"]  = EEex_Options_NumberLuaStorage.new({ ["section"] = "EEex", ["key"] = "Scale Module: Percent" }),'''),
    ('''				["maxCharacters"] = 5,''', '''				["maxCharacters"] = 3, -- EEex-PTEE: 0..100'''),
    ('''	B3Scale_Private_Percentage:set(p)''', '''	B3Scale_Private_Percentage:set(math.floor(p * 100 + 0.5)) -- EEex-PTEE: stored as percent'''),
    ('''		and 768 + (1 - B3Scale_Private_Percentage:get()) * (h - 768)''',
     '''		and 768 + (1 - B3Scale_Private_Percentage:get() / 100) * (h - 768) -- EEex-PTEE: percent'''),
]
