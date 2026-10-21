# EEex_AIBase.lua: Torment's CAIScript constructor has no player-script flag (it calls CAIScript::Read(res, 0), PT
# 0x176d80 -> 0x12d240); player scripts are re-read with Read(res, 1) as CGameSprite::JoinParty does (same as
# EEex.dll's PTEE::NewScript; binding CAIScript:Read in bindings/in/make_manual_types_pt.py).
PATCHES = [
    ('''			newScript:Construct1(manager:getUD("resref"), EEex_Utility_Default(bPlayerScript, false))''',
     '''			newScript:Construct1(manager:getUD("resref")) -- EEex-PTEE: no player flag in Torment
			if EEex_Utility_Default(bPlayerScript, false) then newScript:Read(manager:getUD("resref"), 1) end'''),
]
