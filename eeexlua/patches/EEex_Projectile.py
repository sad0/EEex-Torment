# EEex_Projectile.lua: label uses checked against Torment.
# - VFTable labels: every CProjectile*::VFTable label equals tools/bindings/vtmap.json's independent Torment vtable
#   (constructor store / content match); CProjectileInstant (absent from vtmap) checked by hand: DecodeProjectile's
#   fallback allocation stores it (PT 0x282b4a lea rax, 0x630700 <-> BG 0x22ed71).
# - Data-...-CProjectile::DecodeProjectile()-RetPtr: each Torment label is the return address of a call
#   0x27c4a0 in the mapped function, except ForceSpellPoint: PT label 0x1823f1 points 2 bytes past the return
#   address (call at PT 0x1823ea returns to 0x1823ef, xor edi, edi): LABEL FIX NEEDED (tools/manual.json), not
#   compensated here. Two labels do not exist in Torment (PATTERNS.md "unsupported"): guarded below.
# - Data-...-CProjectile::AddEffect()-RetPtr: each label is the return address of call [rax+0xC8] (AddEffect is
#   virtual in Torment) in the mapped function (see EEex_Projectile_Patch.py).
# - Torment has 80 projectile vtables (one of the three AddEffect bodies at +0xC8) for the 22 EEex names: the other
#   classes are Torment-only and would be EEex_Projectile_Type.Unknown, which isOfType() cannot handle
#   (Inheritance[Unknown] is nil). They are classified by their AddEffect slot instead (nearest known base class).
# - CProjectile::DecodeProjectile takes a third argument in Torment (nLevel, bindings manual_types_pt.txt).
PATCHES = [
    # BG CGameSprite::UpdateAOE has no Torment counterpart (PATTERNS.md): label undefined
    ('''	[ EEex_Label("Data-CGameSprite::UpdateAOE()-CProjectile::DecodeProjectile()-RetPtr")                    ] = EEex_Projectile_DecodeSource.CGameSprite_UpdateAOE,''',
     '''	[ EEex_LabelDefault("Data-CGameSprite::UpdateAOE()-CProjectile::DecodeProjectile()-RetPtr", -1)         ] = EEex_Projectile_DecodeSource.CGameSprite_UpdateAOE, -- EEex-PSTEE: absent in Torment'''),
    # Torment's DecodeProjectile has no Multi Magic Missile sub-decode (PATTERNS.md): label undefined
    ('''	[ EEex_Label("Data-CProjectile::DecodeProjectile()-CProjectile::DecodeProjectile()-RetPtr")             ] = EEex_Projectile_DecodeSource.CProjectile_DecodeProjectile_MultiMagicMissile,''',
     '''	[ EEex_LabelDefault("Data-CProjectile::DecodeProjectile()-CProjectile::DecodeProjectile()-RetPtr", -2)  ] = EEex_Projectile_DecodeSource.CProjectile_DecodeProjectile_MultiMagicMissile, -- EEex-PSTEE: absent in Torment'''),
    # Torment-only projectile classes: nearest known base class from the AddEffect vtable slot
    ('''function EEex_Projectile_GetType(projectile)
	local type = EEex_Projectile_Private_VFTableToType[EEex_ReadPtr(EEex_UDToPtr(projectile))]
	return type or EEex_Projectile_Type.Unknown
end''',
     '''-- EEex-PSTEE: Torment has Torment-only projectile classes (80 projectile vtables). AddEffect (vtable +0xC8) is
-- overridden by CProjectileArea (PT 0x279aa0) and CProjectileBAM (PT 0x279b20, inherited by every BAM-derived class),
-- so an unknown vtable's slot gives its nearest known base class.
EEex_Projectile_Private_PSTEE_AddEffectToType = {
	[ EEex_ReadPtr(EEex_Label("CProjectile::VFTable") + 0xC8)     ] = EEex_Projectile_Type.CProjectile,
	[ EEex_ReadPtr(EEex_Label("CProjectileArea::VFTable") + 0xC8) ] = EEex_Projectile_Type.CProjectileArea,
	[ EEex_ReadPtr(EEex_Label("CProjectileBAM::VFTable") + 0xC8)  ] = EEex_Projectile_Type.CProjectileBAM,
}

function EEex_Projectile_Private_PSTEE_GetFallbackType(vftable)
	return EEex_Projectile_Private_PSTEE_AddEffectToType[EEex_ReadPtr(vftable + 0xC8)]
end

function EEex_Projectile_GetType(projectile)
	local vftable = EEex_ReadPtr(EEex_UDToPtr(projectile))
	local type = EEex_Projectile_Private_VFTableToType[vftable]
		or EEex_Projectile_Private_PSTEE_GetFallbackType(vftable) -- EEex-PSTEE: Torment-only projectile classes
	return type or EEex_Projectile_Type.Unknown
end'''),
    ('''	return EEex_BAnd(EEex_Projectile_Private_Inheritance[projType], checkType) ~= 0x0''',
     '''	return EEex_BAnd(EEex_Projectile_Private_Inheritance[projType] or 0x0, checkType) ~= 0x0 -- EEex-PSTEE: Unknown has no entry'''),
    # Torment's DecodeProjectile(type, decoder, nLevel): CGameAIBase::FireSpell passes 1 (PT 0x17ddfa), Swing 1
    # (PT 0x433f37), CProjectile multi / chain sub-decodes 1 (PT 0x2829e2, 0x27cd32)
    ('''	local projectile = CProjectile.DecodeProjectile(projectileID, sourceObject)''',
     '''	local projectile = CProjectile.DecodeProjectile(projectileID, sourceObject, 1) -- EEex-PSTEE: Torment's nLevel argument'''),
    # Torment's own spell action handlers decode their projectile themselves (tools/port_extra.py, pstee.db labels):
    # same decode sources as the BG functions they replace. Torment's PST-only projectile classes (PT 0x25d..0x290)
    # and op handler 0x1e5ba0 also decode sub-projectiles: no BG source, decodeSource stays nil there.
    ('''	[ EEex_Label("Data-CGameSprite::Spell()-CProjectile::DecodeProjectile()-RetPtr")                        ] = EEex_Projectile_DecodeSource.CGameSprite_Spell,''',
     '''	[ EEex_Label("Data-CGameSprite::Spell()-CProjectile::DecodeProjectile()-RetPtr")                        ] = EEex_Projectile_DecodeSource.CGameSprite_Spell,
	[ EEex_Label("Data-PSTEE-SpellAction()-CProjectile::DecodeProjectile()-RetPtr")                          ] = EEex_Projectile_DecodeSource.CGameSprite_Spell,           -- EEex-PSTEE: Spell / SpellNoDec
	[ EEex_Label("Data-PSTEE-SpellPointAction()-CProjectile::DecodeProjectile()-RetPtr")                     ] = EEex_Projectile_DecodeSource.CGameSprite_SpellPoint,      -- EEex-PSTEE: SpellPoint / SpellPointNoDec
	[ EEex_Label("Data-PSTEE-ForceSpellAction()-CProjectile::DecodeProjectile()-RetPtr")                     ] = EEex_Projectile_DecodeSource.CGameAIBase_ForceSpell,      -- EEex-PSTEE: ForceSpell / ReallyForceSpell / NoFeedback
	[ EEex_Label("Data-PSTEE-ForceSpellPointAction()-CProjectile::DecodeProjectile()-RetPtr")                ] = EEex_Projectile_DecodeSource.CGameAIBase_ForceSpellPoint, -- EEex-PSTEE: ForceSpellPoint'''),
]
