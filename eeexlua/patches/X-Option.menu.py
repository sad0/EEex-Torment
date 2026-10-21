# X-Option.menu: Torment's menu parser has no `scaleToClip` keyword (eeexlua/notes/uiItem_layout.md: bam.scaletoclip is
# absent from Torment's uiItem; the token is rejected as invalid): drop it, the BAM is drawn at its own size.
PATCHES = [
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
