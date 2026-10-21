# B3AttackInfo.lua: Torment's CGameSpriteEquipment.m_items is a CItem** to an array sized by ITMSLOTS.2DA
# (manual_fields.json, CGameSpriteEquipment::ClearMarshal PT 0x3c09a0), not BG's inline Array<CItem*,39>: there is
# no :get(); the slot is read from the array (same as bindings/test/EEex_Main.lua's in-game test).
PATCHES = [
    ('''	local sourceSpriteEquipment = sourceSprite.m_equipment
''', '''	local sourceSpriteEquipment = sourceSprite.m_equipment

	-- EEex-PTEE: m_items is a CItem** in Torment
	local getEquippedItem = function(slot)
		local item = EEex_ReadPtr(EEex_UDToPtr(sourceSpriteEquipment.m_items) + EEex_PtrSize * slot)
		return item ~= 0 and EEex_PtrToUD(item, "CItem") or nil
	end
'''),
    ('@all:2 sourceSpriteSelectedWeapon = sourceSpriteEquipment.m_items:get(nSourceSpriteSelectedWeapon)',
     'sourceSpriteSelectedWeapon = getEquippedItem(nSourceSpriteSelectedWeapon) -- EEex-PTEE'),
]
