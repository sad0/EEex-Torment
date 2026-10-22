# B3EffMen.menu: tokens Torment's menu parser does not have (eeexlua/notes/uiItem_layout.md; rejected as invalid):
# `scaleToClip` (no bam.scaletoclip: the BAM is drawn at its own size) and `scrollbar clunkyScroll` (no
# scrollbar.clunkyScroll: the list scrolls at Torment's default speed).
PATCHES = [
    # scrollbar: Torment's own list scrollbar (CGSCRL1, every options / journal list in UI.MENU) instead of BG's GUISCRC
    ('''		scrollbar "GUISCRC"''', '''		scrollbar "CGSCRL1" -- EEex-PSTEE: Torment's scrollbar'''),
    # wider (+100 px): French spell names were cut ("Duplication d'Enoll Ev...", owner test)
    ('\t\tarea 0 0 220 160\n', '\t\tarea 0 0 320 160 -- EEex-PSTEE: +100\n'),
    ('\t\t\t\tarea 0 0 147 30\n', '\t\t\t\tarea 0 0 230 30 -- EEex-PSTEE: +100 (column 70%)\n'),
    ('\t\tarea 10 10 210 140\n', '\t\tarea 10 10 310 140 -- EEex-PSTEE: +100\n'),
    # Torment's default text colour is dark (parchment screens): the effect names were unreadable on the dark
    # background; same style / white colour as B3AtkInf.menu, which reads fine in Torment (owner test)
    ('''				text lua "B3EffectMenu_Private_Menu_List_Table[rowNumber].text"
				text align left center''',
     '''				text lua "B3EffectMenu_Private_Menu_List_Table[rowNumber].text"
				text style "normal" -- EEex-PSTEE
				text color 255 255 255 255 -- EEex-PSTEE
				text align left center'''),
    ('@all:1 ' + '\t\t\t\tscaleToClip\n', ''),
    ('''		scrollbar clunkyScroll 35
''', ''),
]
