# EEex_UncapFPS.lua options: Torment's CChitin::WinMain reads "Maximum Frame Rate" with default 40 and keeps it only
# in 10..90 (else 40) (AUDIT.md, ported in uncap_fps.cpp's WinMain): same default and range for EEex's option.
PATCHES = [
    ('''EEex_Options_Register("EEex_UncapFPS_AISpeed", EEex_Options_Option.new({
	["default"]  = 30,
	["type"]     = EEex_Options_EditType.new(),
	["accessor"] = EEex_Options_ClampedAccessor.new({ ["min"] = 1, ["max"] = 90 }),''',
     '''EEex_Options_Register("EEex_UncapFPS_AISpeed", EEex_Options_Option.new({
	["default"]  = 40, -- EEex-PTEE: Torment's default
	["type"]     = EEex_Options_EditType.new(),
	["accessor"] = EEex_Options_ClampedAccessor.new({ ["min"] = 10, ["max"] = 90 }), -- EEex-PTEE: Torment accepts 10..90'''),
]
