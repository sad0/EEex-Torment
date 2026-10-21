# X-Option.menu: Torment's menu parser has no `scaleToClip` keyword (eeexlua/notes/uiItem_layout.md: bam.scaletoclip is
# absent from Torment's uiItem; the token is rejected as invalid): drop it, the BAM is drawn at its own size.
PATCHES = [
    # scrollbars: Torment's own list scrollbar (CGSCRL1, UI.MENU) instead of BG's GUISCRC (owner request)
    ('@all:2 scrollbar "GUISCRC"', 'scrollbar "CGSCRL1" -- EEex-PTEE: Torment scrollbar'),
    # toggles: a button
    # draws hover / pressed frames (owner: only ON / OFF) and a label takes no click in Torment: a text item does both
    ('''		button
		{
			enabled true
			action "EEex_Options_Private_TEMPLATE_Toggle_Action()"''',
     '''		text -- EEex-PTEE: clickable, no hover frame
		{
			enabled true
			action "EEex_Options_Private_TEMPLATE_Toggle_Action()"'''),
    # toggles: Torment's own option toggles use CHECKBUT (frame 0 off, 2 on, UI.MENU OPTIONS_GAMEPLAY), the same
    # frames EEex's Toggle_Frame returns; BG's ROUNDBUT is a plain grey circle in Torment (owner: barely visible)
    ('bam "ROUNDBUT"', 'bam "CHECKBUT" -- EEex-PTEE: Torment toggle'),
    ('@all:6 ' + '\t\t\tscaleToClip\n', ''),
]
# "Reset All" header button (patches/EEex_Options.py) and its Yes / No confirmation, a copy of Torment's
# POPUP_TWOBUTTON (UI.MENU: POPUP2 mosaic, POPUPIMG, label_parchment, widebutt) with an EEex string
PATCHES += [
    ('''		name "EEex_Options_TEMPLATE_ExitButton"
	}
''', '''		name "EEex_Options_TEMPLATE_ExitButton"
	}

	template -- EEex-PTEE
	{
		button
		{
			enabled true
			action "EEex_Options_Private_TEMPLATE_PTEE_ResetAllButton_Action()"
			bam SHRTBUTT
			text lua "getUiString('EEex_Options_TRANSLATION_Reset_All_to_Default')"
			text style "button"
		}
		name "EEex_Options_TEMPLATE_PTEE_ResetAllButton"
	}
'''),
    ('@file-end', '''
menu -- EEex-PTEE
{
	name "EEex_Options_PTEE_ResetConfirm"
	align center center
	modal
	popupSound 1
	label
	{
		area 0 0 917 393
		mosaic POPUP2
	}
	label
	{
		area 81 65 204 220
		bam "POPUPIMG"
		sequence 1
	}
	label
	{
		area 334 82 540 224
		text lua "getUiString('EEex_Options_TRANSLATION_Reset_All_Confirm')"
		text style "label_parchment"
	}
	button
	{
		area 522 320 170 54
		bam widebutt
		text lua "t('NO_BUTTON')"
		text style "button"
		on escape
		action "Infinity_PopMenu('EEex_Options_PTEE_ResetConfirm')"
	}
	button
	{
		area 706 320 170 54
		bam widebutt
		text lua "t('YES_BUTTON')"
		text style "button"
		on return
		action
		"
			Infinity_PopMenu('EEex_Options_PTEE_ResetConfirm')
			EEex_Options_Private_PTEE_ResetAll()
		"
	}
}
'''),
]
