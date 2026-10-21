# X-en_US.lua: the scale option is a percentage in the Torment port (patches/B3Scale.py).
PATCHES = [
    ('uiStrings["EEex_Options_TRANSLATION_Scale_Percentage"] = "Scale Percentage [0-1]"',
     'uiStrings["EEex_Options_TRANSLATION_Scale_Percentage"] = "Scale Percentage [0-100]"'),
    ('''This field is a decimal between 0 and 1.

For example, a value of '0.5' would force the game to use a 50% scaling factor.''',
     '''This field is a whole percentage between 0 and 100.

For example, a value of '50' would force the game to use a 50% scaling factor.'''),
]
