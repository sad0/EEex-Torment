# EEex_Resource.lua: same CAIScript construction as EEex_AIBase.py (Torment constructor without the player flag).
PATCHES = [
    ('''			script:Construct1(manager:getUD("resref"), bPlayerScript or false)''',
     '''			script:Construct1(manager:getUD("resref")) -- EEex-PSTEE: no player flag in Torment
			if bPlayerScript then script:Read(manager:getUD("resref"), 1) end'''),
]
