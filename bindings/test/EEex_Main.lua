-- EEex-PTEE phase 3 test: load LuaBindings.dll (Torment layouts) and read a few engine structs.
-- Output goes to EEex_PTEE.log through print(). EEex_Main.lua runs while the main object is
-- being allocated, so engine reads are deferred to UI activity (Infinity_PushMenu wrapper).

local function log(...)
	local t = {}
	for i = 1, select("#", ...) do t[#t + 1] = tostring((select(i, ...))) end
	print("PTEE-TEST: " .. table.concat(t, " "))
end

local ok, err = pcall(function()
	EEex_DoFile("EEex_Assembly")
	EEex_DoFile("EEex_Assembly_Patch")
	EEex_DoFile("PTEE_SkipIntro")
	-- Same as EEex_Main.lua: redirect the engine's tolua event functions to the bindings' versions
	EEex_OpenLuaBindings("LuaBindings", function() EEex_DoFile("EEex_LuaBindings_Patch") end)
	-- Phase 4: EEex.dll (C++ core) for Torment
	EEex_OpenLuaBindings("EEex")
	EEex.OnTargetExecutableInitialized()
	-- Phase 4d: EEex's visibility map (FoW-clearing cap) reimplementation, installed like EEex_Fix_Patch.lua
	EEex_DoFile("PTEE_VisMapTest")
end)
log("EEex_OpenLuaBindings(LuaBindings + EEex)", ok, err)
if ok then
	local n = 0
	for _ in pairs(EEex) do n = n + 1 end
	log("EEex table entries:", n, "GetMicroseconds:", EEex.GetMicroseconds())
end
if not ok then return end

local fetchString -- set when the engine registers Infinity_FetchString

local function hex(ud)
	local p = ud and EEex_UDToPtr(ud)
	return p and string.format("0x%X", p) or "nil"
end

local function getObject(id)
	local object
	EEex_RunWithStack(EEex_PointerSize, function(mem)
		local ptr = EEex_PtrToUD(mem, "Pointer<CGameObject>")
		local rc = CGameObjectArray.GetShare(id, ptr)
		object = rc == 0 and ptr.reference or nil
	end)
	return object
end

local lastState
local function dumpEngine()
	local chitin = EngineGlobals.g_pBaldurChitin
	local game = chitin and chitin.m_pObjectGame
	local state = string.format("g_pBaldurChitin=%s m_pObjectGame=%s m_pEngineWorld=%s", hex(chitin), hex(game), hex(chitin and chitin.m_pEngineWorld))
	if state ~= lastState then
		lastState = state
		log(state)
	end
	return game
end

local function dumpParty(game)
	local n = game.m_nCharacters
	log("party size m_nCharacters =", n)
	for i = 0, n - 1 do
		local id = game.m_characters:get(i)
		local obj = getObject(id)
		if obj then
			local sprite = EEex_CastUD(obj, "CGameSprite")
			local base = sprite.m_baseStats
			local derived = sprite.m_derivedStats
			log(string.format("party[%d] id=%d name=%q hp=%d/%d (derived max %d) xp=%d gold=%d",
				i, id, fetchString(base.m_name), base.m_hitPoints, base.m_maxHitPointsBase,
				derived.m_nMaxHitPoints, base.m_xp, base.m_gold))
		else
			log(string.format("party[%d] id=%d -> no object", i, id))
		end
	end
	log("party gold m_gameSave.m_nPartyGold =", game.m_gameSave.m_nPartyGold)
	-- EEex.dll functions working on engine structs
	local obj = getObject(game.m_characters:get(0))
	local sprite = EEex_CastUD(obj, "CGameSprite")
	log("EEex.FormatPointerAsEngine:", EEex.FormatPointerAsEngine(EEex_UDToPtr(sprite)))
	log("EEex.CanAttackWithLeftHand(party[0]):", EEex.CanAttackWithLeftHand(sprite))
	-- PTEE CGameSpriteEquipment: items pointer + selected slot (ITMSLOTS: 10 = FIST, 35-38 = WEAPONS)
	local eq = sprite.m_equipment
	log("m_equipment.m_selectedWeapon:", eq.m_selectedWeapon, "ability:", eq.m_selectedWeaponAbility,
		"m_pSprite==sprite:", EEex_UDToPtr(eq.m_pSprite) == EEex_UDToPtr(sprite))
	log("m_equipment.m_items:", pcall(function() return tostring(eq.m_items) end))

	-- Phase 4b: every EEex.dll export that works without the phase-5 Lua patches
	local target = EEex_CastUD(getObject(game.m_characters:get(1)), "CGameSprite")
	local function t(name, f)
		local res = {pcall(f)}
		local out = {}
		for i = 2, #res do out[#out + 1] = tostring(res[i]) end
		log(string.format("EXPORT %-28s %s %s", name, res[1] and "ok" or "ERROR", table.concat(out, " | ")))
	end
	local weaponPtr = EEex_ReadPtr(EEex_UDToPtr(eq.m_items) + 8 * eq.m_selectedWeapon)
	local weapon = weaponPtr ~= 0 and EEex_PtrToUD(weaponPtr, "CItem") or nil
	log("selected weapon item:", weaponPtr ~= 0 and weapon.cResRef:get() or "none")
	t("GetWeaponHitChance", function() return EEex.GetWeaponHitChance(sprite, target, weapon, eq.m_selectedWeaponAbility, 0) end)
	t("FakeAttackRoll", function() return EEex.FakeAttackRoll(sprite, target, weapon, eq.m_selectedWeaponAbility, 0) end)
	t("IsImmuneToWeapon", function() return EEex.IsImmuneToWeapon(target, sprite, eq.m_selectedWeapon, weapon, eq.m_selectedWeaponAbility) end)
	t("GetExtendedStatValue", function() return EEex.GetExtendedStatValue(sprite, 203) end)
	t("GetHighestRefreshRate", function() return EEex.GetHighestRefreshRate() end)
	t("GetMicroseconds", function() return EEex.GetMicroseconds() end)
	t("SetINIString", function() return EEex.SetINIString("./EEex_PTEE_test.ini", "Test", "Key", "Value42") end)
	t("GetINIString", function() return EEex.GetINIString("./EEex_PTEE_test.ini", "Test", "Key", "default") end)
	t("GetTextWidthHeight", function() return EEex.GetTextWidthHeight("Hello Sigil", "BOOKMANI", 14, false) end)
	t("IsDefaultAttackCursor", function() return EEex.IsDefaultAttackCursor() end)
	t("IsMarshallingCopy", function() return EEex.IsMarshallingCopy() end)
	t("IsPlayerScript", function() return EEex.IsPlayerScript(sprite.m_overrideScript) end)
	t("ShouldEffectBypassOp120", function() return EEex.ShouldEffectBypassOp120(nil) end)
	t("MatchObject", function() return EEex.MatchObject(sprite, "return true", 0, 300, 0) end)
	t("MatchObject Party", function() return EEex.MatchObject(sprite, "return EEex_MatchObject.m_id ~= nil", 0, 300, 0) end)
	t("FormatPointerAsEngine", function() return EEex.FormatPointerAsEngine(EEex_UDToPtr(target)) end)
	t("DeepCopy", function() local c = EEex.DeepCopy({a = {b = 1}}); return c and c.a.b end)
	-- Phase 4b: virtual calls in Torment slot order (tools/bindings/vtsolve.py)
	t("virtual_GetObjectType", function() return sprite:virtual_GetObjectType() end)
	t("virtual_GetVisualRange", function() return sprite:virtual_GetVisualRange() end)
	t("virtual_GetAttackRange", function() return sprite:virtual_GetAttackRange() end)
	t("virtual_GetHelpRange", function() return sprite:virtual_GetHelpRange() end)
	t("virtual_GetCanSeeInvisible", function() return sprite:virtual_GetCanSeeInvisible() end)
	t("virtual_GetAIType", function() return EEex_UDToPtr(sprite:virtual_GetAIType()) - EEex_UDToPtr(sprite) end)
	t("virtual_GetVertListType", function() return sprite:virtual_GetVertListType() end)
	t("m_activeImprisonment", function() return sprite.m_activeImprisonment end)
	-- Phase 4d visibility map: party members are FoW-clearing characters, tiles around them are visible
	t("vismap visible/explored tiles", function()
		local vis = sprite.m_pArea.m_visibility
		local w, h = vis.m_nWidth, vis.m_nHeight
		local base = EEex_UDToPtr(vis.m_pMap)
		local seen, explored = 0, 0
		for i = 0, w * h - 1 do
			local v = EEex_ReadU16(base + 2 * i)
			if bit32.band(v, 0x7FFF) ~= 0 then seen = seen + 1 end
			if bit32.band(v, 0x8000) ~= 0 then explored = explored + 1 end
		end
		local cx, cy = math.floor(sprite.m_pos.x / 32), math.floor(sprite.m_pos.y / 32)
		return w, h, seen, explored, EEex_ReadU16(base + 2 * (cy * w + cx))
	end)
	t("party canBeSeen", function() return sprite.m_canBeSeen, target.m_canBeSeen end)
	-- MatchObject diagnosis: every condition EEex_CheckMatch tests on the target (party[1])
	t("target flags", function() return target.m_active, target.m_activeAI, target.m_activeImprisonment end)
	t("target pos/caller pos", function() return target.m_pos.x, target.m_pos.y, sprite.m_pos.x, sprite.m_pos.y end)
	t("target AboveGround", function() return target.m_animation.m_animation:virtual_GetAboveGround() end)
	t("target generalState", function() return target.m_derivedStats.m_generalState, target.m_derivedStats.m_bSanctuary end)
	t("caller vert list", function() return sprite:virtual_GetVertListPos() ~= nil, sprite:virtual_GetVertListType() end)
	t("area vert sort count", function() return sprite.m_pArea.m_lVertSort.m_nCount end)
	t("MatchObject counter", function() PTEE_MC = 0; local r = EEex.MatchObject(sprite, "PTEE_MC = PTEE_MC + 1 return true", 0, -1, 1); return r, PTEE_MC end)
	t("MatchObject non-sprites", function() PTEE_MC = 0; local r = EEex.MatchObject(sprite, "PTEE_MC = PTEE_MC + 1 return true", 0, -1, 2 + 8 + 16 + 32); return r, PTEE_MC end)
end

local engineDone, partyDone, ticks = false, false, 0

local samples = 0
local function sampleVisibility()
	-- m_canBeSeen of every sprite in the area over time (visibility map test)
	samples = samples + 1
	if samples > 40 then return end
	local game = EngineGlobals.g_pBaldurChitin.m_pObjectGame
	local o = getObject(game.m_characters:get(0))
	local area = o.m_pArea
	local out = {}
	local node = area.m_lVertSort.m_pNodeHead
	while node do
		local obj = getObject(node.data)
		if obj and obj.m_objectType == 0x31 then
			local s = EEex_CastUD(obj, "CGameSprite")
			out[#out + 1] = string.format("%d:%d", s.m_id % 1000, s.m_canBeSeen)
		end
		node = node.pNext
	end
	log("canBeSeen", samples, table.concat(out, " "))
end

local function onUI()
	if partyDone then
		ticks = ticks + 1
		if ticks % 7 == 0 then pcall(sampleVisibility) end
		return
	end
	ticks = ticks + 1
	if ticks % 200 ~= 1 then return end
	local okE, game = pcall(dumpEngine)
	if not engineDone then
		engineDone = true
		log("engine reads", okE, okE and "" or game)
	end
	-- wait until party[0] is placed in its area (vertical sort list), not just loaded
	local function placed()
		local o = getObject(game.m_characters:get(0))
		return o and o.m_pArea and EEex_CastUD(o, "CGameSprite"):virtual_GetVertListPos() ~= nil
	end
	if okE and game and game.m_nCharacters > 0 and select(2, pcall(placed)) == true then
		partyDone = true
		local okP, errP = pcall(dumpParty, game)
		log("dumpParty", okP, errP)
	end
end

-- The engine registers Infinity_* after EEex_Main.lua: catch their creation and wrap them
local wanted = {Infinity_FetchString = true, Infinity_PushMenu = true, Infinity_GetScreenSize = true, Infinity_PopMenu = true}
local pending = 4
setmetatable(_G, {__newindex = function(t, k, v)
	if wanted[k] and type(v) == "function" then
		if k == "Infinity_FetchString" then fetchString = v end
		rawset(t, k, function(...) onUI(); return v(...) end)
		pending = pending - 1
		log("hooked", k)
		if pending == 0 then setmetatable(_G, nil) end
	else
		rawset(t, k, v)
	end
end})
log("waiting for UI activity / a loaded game")
