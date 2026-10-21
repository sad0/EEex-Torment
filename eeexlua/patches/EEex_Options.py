# EEex_Options.lua: Torment's uiItem bam_t has no scaletoclip member (eeexlua/notes/uiItem_layout.md: BG
# bam.scaletoclip is absent in Torment, no parser keyword): writing it would raise a Lua error in the bindings.
PATCHES = [
    ('''					columnItem.bam.scaletoclip = 1
''', '''					-- EEex-PTEE: no bam.scaletoclip in Torment
'''),
    ('''				existingButton.bam.scaletoclip = 1
''', '''				-- EEex-PTEE: no bam.scaletoclip in Torment
'''),
]

# Torment's options screens (UI.MENU): ESC_MENU is a ring of 8 OPTBUTT buttons with no free slot, so the owner chose
# the bottom row of OPTIONS_GAMEPLAY (Pause automatique 99, Assigner touches 243 / touch-UI Feedback 243, Feedback
# 388, Retour 552, OK 698; all 138x56 at y 566): the row is re-laid out as 6 buttons of 118 (step 123.8, same span
# 99..836) with "EEex Options" (NORMBUTT, like Feedback) before Retour.
PATCHES.append(('''	local modifyExisting = function()
		if modifyInfinityUI()    then return true end''',
'''	-- EEex-PTEE: Planescape: Torment UI
	local modifyTorment = function()

		local gameplayMenu = EEex_Menu_Find("OPTIONS_GAMEPLAY")
		if gameplayMenu == nil then return false end

		local newX = { [99] = 99, [243] = 223, [388] = 347, [552] = 594, [698] = 718 }
		local row = {}
		local feedbackButton = nil

		local item = gameplayMenu.items
		while item ~= nil do
			local area = item.area
			if area.y == 566 and area.h == 56 and area.w == 138 and newX[area.x] ~= nil then
				table.insert(row, item)
				if area.x == 388 then feedbackButton = item end
			end
			item = item.next
		end
		if feedbackButton == nil or #row < 5 then return false end

		local injectedButton = EEex_Menu_InjectTemplateInstance("OPTIONS_GAMEPLAY", "EEex_Options_TEMPLATE_OpenButton", 0, 0, 0)
		local injectedButtonBam = injectedButton.bam
		local injectedButtonPad = injectedButton.pad
		local feedbackButtonPad = feedbackButton.pad

		injectedButtonBam.resref   = feedbackButton.bam.resref
		injectedButtonBam.sequence = feedbackButton.bam.sequence
		injectedButtonPad.x = feedbackButtonPad.x
		injectedButtonPad.y = feedbackButtonPad.y
		injectedButtonPad.w = feedbackButtonPad.w
		injectedButtonPad.h = feedbackButtonPad.h

		for _, rowButton in ipairs(row) do
			local area = rowButton.area
			area.x = newX[area.x]
			area.w = 118
		end

		local injectedButtonArea = injectedButton.area
		injectedButtonArea.x = 470
		injectedButtonArea.y = 566
		injectedButtonArea.w = 118
		injectedButtonArea.h = 56
		return true
	end

	local modifyExisting = function()
		if modifyTorment()       then return true end -- EEex-PTEE
		if modifyInfinityUI()    then return true end'''))
