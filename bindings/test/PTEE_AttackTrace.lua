-- EEex-PTEE dev trace (not shipped): logs every B3AttackInfo hit-chance computation (source, slot, item) before
-- calling the engine, to find the creature / weapon behind a heap corruption seen in the reversed (Shift) view.
local origHitChance = EEex.GetWeaponHitChance
local origImmune = EEex.IsImmuneToWeapon
local function name(sprite) local ok, n = pcall(function() return sprite:getName() end) return ok and n or "?" end
local function res(item) if item == nil then return "nil" end local ok, r = pcall(function() return item.pRes.resref:get() end) return ok and r or "?" end
EEex.IsImmuneToWeapon = function(source, target, slot, item, ability)
	print(string.format("PTEE-ATK: immune %s -> %s slot %s item %s ability %s", name(source), name(target), tostring(slot), res(item), tostring(ability)))
	return origImmune(source, target, slot, item, ability)
end
EEex.GetWeaponHitChance = function(source, target, item, ability, leftHand)
	print(string.format("PTEE-ATK: hit %s -> %s item %s ability %s left %s", name(source), name(target), res(item), tostring(ability), tostring(leftHand)))
	local a, b = origHitChance(source, target, item, ability, leftHand)
	print("PTEE-ATK: ok " .. tostring(a))
	return a, b
end
