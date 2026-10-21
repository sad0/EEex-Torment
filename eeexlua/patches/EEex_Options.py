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
