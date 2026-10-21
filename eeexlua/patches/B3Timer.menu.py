# B3Timer.menu: Torment's menu parser has no `scaleToClip` keyword (eeexlua/notes/uiItem_layout.md: bam.scaletoclip is
# absent from Torment's uiItem; the token is rejected as invalid): drop it, the BAM is drawn at its own size.
PATCHES = [
    ('@all:4 ' + '\t\t\tscaleToClip\n', ''),
]
