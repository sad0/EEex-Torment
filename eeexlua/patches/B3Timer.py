# B3Timer.lua: Torment has no RIGHT_SIDEBAR; the party portraits are a horizontal row in WORLD_ACTIONBAR_LEFT
# (UI.MENU: `button { area 769 4 74 58; portrait 5; enabled "Infinity_GetNumCharacters() > 5" ... }`, one every 85 px
# over a 85x85 mosaic background). The timer bars stay vertical, stacked against the left edge of each portrait
# (BG's "hug portraits" placement, there is no screen edge to start from). With Torment's "Use Touch Actionbar"
# option the portraits are in WORLD_ACTIONBAR_LEFT_TABLET instead (UI.MENU pushes one or the other): instances are
# injected into both, each remembers its menu, and the menu on the stack is the one the enabled/frame callbacks use.
PATCHES = [
    ('B3Timer_Private_InjectingMenu = "RIGHT_SIDEBAR"',
     'B3Timer_Private_InjectingMenu = "WORLD_ACTIONBAR_LEFT" -- EEex-PTEE: Torment portraits'),
    ('''						local startX = (B3Timer_Private_HugPortraits:get() == 1 and portraitArea.x or 0) - 3''',
     '''						local startX = portraitArea.x - 3 -- EEex-PTEE: always against the portrait (horizontal row)'''),
    ('''	local instanceEntry = B3Timer_Private_CreateInstance(menuName, templateName, x, y, w, h)
	instanceEntry.portraitItem = portraitItem''',
     '''	local instanceEntry = B3Timer_Private_CreateInstance(menuName, templateName, x, y, w, h)
	instanceEntry.menuName = menuName -- EEex-PTEE: two portrait menus
	instanceEntry.portraitItem = portraitItem'''),
    ('''	local item = EEex_Menu_Find(B3Timer_Private_InjectingMenu).items
	while item do''',
     '''	for _, injectingMenu in ipairs({"WORLD_ACTIONBAR_LEFT", "WORLD_ACTIONBAR_LEFT_TABLET"}) do -- EEex-PTEE
	B3Timer_Private_InjectingMenu = injectingMenu
	local item = EEex_Menu_Find(B3Timer_Private_InjectingMenu).items
	while item do'''),
    ('''			B3Timer_Private_CreateInstanceForPortrait(B3Timer_Private_InjectingMenu, "B3Timer_Menu_TEMPLATE_TimerCast",        nil, nil, 2,  nil, item)
		end
		item = item.next
	end''',
     '''			B3Timer_Private_CreateInstanceForPortrait(B3Timer_Private_InjectingMenu, "B3Timer_Menu_TEMPLATE_TimerCast",        nil, nil, 2,  nil, item)
		end
		item = item.next
	end
	end -- EEex-PTEE
	B3Timer_Private_InjectingMenu = "WORLD_ACTIONBAR_LEFT"'''),
    ('''	B3Timer_Private_NextUpdateTick = curTick + 33
''',
     '''	B3Timer_Private_NextUpdateTick = curTick + 33

	-- EEex-PTEE: the portrait menu currently shown (touch actionbar option)
	B3Timer_Private_InjectingMenu = Infinity_IsMenuOnStack("WORLD_ACTIONBAR_LEFT_TABLET") and "WORLD_ACTIONBAR_LEFT_TABLET" or "WORLD_ACTIONBAR_LEFT"
'''),
    ('''						EEex_Menu_SetTemplateArea(B3Timer_Private_InjectingMenu, templateName, instanceEntry.id, curX, portraitArea.y, rgWidth, portraitArea.h)''',
     '''						EEex_Menu_SetTemplateArea(instanceEntry.menuName, templateName, instanceEntry.id, curX, portraitArea.y, rgWidth, portraitArea.h) -- EEex-PTEE'''),
    ('''					EEex_Menu_SetTemplateArea(B3Timer_Private_InjectingMenu, "B3Timer_Menu_TEMPLATE_Background", backgroundEntry.id, curX + 2, portraitArea.y, startX - curX + rgDif, portraitArea.h)''',
     '''					EEex_Menu_SetTemplateArea(backgroundEntry.menuName, "B3Timer_Menu_TEMPLATE_Background", backgroundEntry.id, curX + 2, portraitArea.y, startX - curX + rgDif, portraitArea.h) -- EEex-PTEE'''),
    # the "Hug Portraits" option has no effect in Torment (bars always against the portrait): not listed in the menu
    ('''		EEex_Options_DisplayEntry.new({
			["optionID"]    = "B3Timer_HugPortraits",
			["label"]       = "EEex_Options_TRANSLATION_Timer_HugPortraits",
			["description"] = "EEex_Options_TRANSLATION_Timer_HugPortraits_Description",
			["widget"]      = EEex_Options_ToggleWidget.new(),
		}),
''', '''		-- EEex-PTEE: "Hug Portraits" hidden (no effect in Torment, the bars always touch the portrait)
'''),
]
