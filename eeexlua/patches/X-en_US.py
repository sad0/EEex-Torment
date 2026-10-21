# X-en_US.lua: the scale option is a percentage in the Torment port (patches/B3Scale.py).
PATCHES = [
    ('uiStrings["EEex_Options_TRANSLATION_Scale_Percentage"] = "Scale Percentage [0-1]"',
     'uiStrings["EEex_Options_TRANSLATION_Scale_Percentage"] = "Scale Percentage [0-100]"'),
    ('''This field is a decimal between 0 and 1.

For example, a value of '0.5' would force the game to use a 50% scaling factor.''',
     '''This field is a whole percentage between 0 and 100.

For example, a value of '50' would force the game to use a 50% scaling factor.'''),
    # Torment's render cap is not BG's 30 FPS (CChitin::WinMain "Maximum Frame Rate", default 40)
    ('''Removes the engine's usual 30 FPS cap, allowing the game to render at your monitor's refresh rate.''',
     '''Removes the engine's usual frame rate cap, allowing the game to render at your monitor's refresh rate.'''),
]
PATCHES += [
    ('''uiStrings["EEex_Options_TRANSLATION_Reset_to_Default"]     = "Reset to Default"''',
     '''uiStrings["EEex_Options_TRANSLATION_Reset_to_Default"]     = "Reset to Default"
uiStrings["EEex_Options_TRANSLATION_Reset_All_to_Default"] = "Reset All" -- EEex-PTEE
uiStrings["EEex_Options_TRANSLATION_Reset_All_Confirm"]    = "Reset every EEex option to its default value?" -- EEex-PTEE'''),
]
