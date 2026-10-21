# B3EffMen.menu: tokens Torment's menu parser does not have (eeexlua/notes/uiItem_layout.md; rejected as invalid):
# `scaleToClip` (no bam.scaletoclip: the BAM is drawn at its own size) and `scrollbar clunkyScroll` (no
# scrollbar.clunkyScroll: the list scrolls at Torment's default speed).
PATCHES = [
    ('@all:1 ' + '\t\t\t\tscaleToClip\n', ''),
    ('''		scrollbar clunkyScroll 35
''', ''),
]
