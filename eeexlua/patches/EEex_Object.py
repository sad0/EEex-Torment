# EEex_Object.lua: Torment's CAIObjectType::GetShare has a third argument bIgnoreRangeAndLOS (PT 0x12b340, AUDIT.md
# argument check; bindings/in/make_manual_types_pt.py); 21 of Torment's 24 callers pass 0 (normal range / LOS rules).
PATCHES = [
    ('@all:2 GetShare(aiBase, checkBackList and 1 or 0))', 'GetShare(aiBase, checkBackList and 1 or 0, 0)) -- EEex-PSTEE: bIgnoreRangeAndLOS'),
]
