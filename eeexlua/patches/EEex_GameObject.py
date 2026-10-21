# EEex_GameObject.lua: VFTable labels checked against Torment (all equal tools/bindings/vtmap.json's independently
# derived Torment vtables: CGameChunk 0x6494d8, CGameText 0x62ccd0, CProjectile* (see EEex_Projectile.py),
# CSparkleCluster 0x62e318, CVEFVidCell 0x639650, CVisualEffect 0x639848). Torment-only projectile classes have
# vtables EEex does not name: cast them to their nearest known base class (EEex_Projectile.lua fallback).
PATCHES = [
    ('''		usertype = EEex_GameObject_Private_VFTableToUsertype[EEex_ReadPtr(EEex_UDToPtr(object))]
	end''',
     '''		local vftable = EEex_ReadPtr(EEex_UDToPtr(object))
		usertype = EEex_GameObject_Private_VFTableToUsertype[vftable]
		if usertype == nil and EEex_Projectile_Private_PTEE_GetFallbackType then
			-- EEex-PTEE: Torment-only projectile class -> nearest known base class (AddEffect vtable slot)
			local projectileType = EEex_Projectile_Private_PTEE_GetFallbackType(vftable)
			usertype = projectileType and EEex_Projectile_Private_CastUserTypes[projectileType]
		end
	end'''),
]
