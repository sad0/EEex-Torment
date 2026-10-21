# EEex_Action.lua: Torment's CGameAIBase::GetTargetShare / GetTargetShareType(byte) forward a third CAIObjectType::
# GetShare argument bIgnoreRangeAndLOS (PT 0x1731c0 / 0x173440, AUDIT.md argument check); 0 = engine default.
PATCHES = [
    ('aiBase:GetTargetShareType2(CGameObjectType.AIBASE)', 'aiBase:GetTargetShareType2(CGameObjectType.AIBASE, 0) -- EEex-PTEE'),
    ('aiBase:GetTargetShareType_Overload_ObjectType(1)', 'aiBase:GetTargetShareType_Overload_ObjectType(1, 0) -- EEex-PTEE'),
    ('aiBase:GetTargetShare()', 'aiBase:GetTargetShare(0) -- EEex-PTEE'),
]
