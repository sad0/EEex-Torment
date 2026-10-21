# B3Timer.lua: Torment has no RIGHT_SIDEBAR; the party portraits are a horizontal row in WORLD_ACTIONBAR_LEFT
# (UI.MENU: `button { area 769 4 74 58; portrait 5; enabled "Infinity_GetNumCharacters() > 5" ... }`, one every 85 px
# over a 85x85 mosaic background). The timer bars stay vertical, stacked against the left edge of each portrait
# (BG's "hug portraits" placement, there is no screen edge to start from). WORLD_ACTIONBAR_LEFT_TABLET (touch
# actionbar option) is not covered.
PATCHES = [
    ('B3Timer_Private_InjectingMenu = "RIGHT_SIDEBAR"',
     'B3Timer_Private_InjectingMenu = "WORLD_ACTIONBAR_LEFT" -- EEex-PTEE: Torment portraits'),
    ('''						local startX = (B3Timer_Private_HugPortraits:get() == 1 and portraitArea.x or 0) - 3''',
     '''						local startX = portraitArea.x - 3 -- EEex-PTEE: always against the portrait (horizontal row)'''),
]
