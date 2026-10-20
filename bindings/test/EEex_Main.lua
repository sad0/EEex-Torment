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
end

local engineDone, partyDone, ticks = false, false, 0

local function onUI()
	if partyDone then return end
	ticks = ticks + 1
	if ticks % 200 ~= 1 then return end
	local okE, game = pcall(dumpEngine)
	if not engineDone then
		engineDone = true
		log("engine reads", okE, okE and "" or game)
	end
	if okE and game and game.m_nCharacters > 0 then
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
