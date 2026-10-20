-- EEex-PTEE phase 3 test: load LuaBindings.dll (Torment layouts) and read a few engine structs.
-- Output goes to EEex_PTEE.log through print().

local function log(...)
	local t = {}
	for i = 1, select("#", ...) do t[#t + 1] = tostring((select(i, ...))) end
	print("PTEE-TEST: " .. table.concat(t, " "))
end

local ok, err = pcall(function() EEex_OpenLuaBindings("LuaBindings") end)
log("EEex_OpenLuaBindings(LuaBindings)", ok, err)
if not ok then return end

local chitin, game
local ok0, err0 = pcall(function()
chitin = EngineGlobals.g_pBaldurChitin
log("g_pBaldurChitin", chitin, "ptr", string.format("0x%X", EEex_UDToPtr(chitin)))
game = chitin.m_pObjectGame
log("m_pObjectGame", game, "ptr", string.format("0x%X", EEex_UDToPtr(game)))
log("CBaldurChitin.m_pEngineWorld", chitin.m_pEngineWorld)
end)
log("startup reads", ok0, err0)
if not ok0 then return end

local function getObject(id)
	local object
	EEex_RunWithStack(EEex_PointerSize, function(mem)
		local ptr = EEex_PtrToUD(mem, "Pointer<CGameObject>")
		local rc = CGameObjectArray.GetShare(id, ptr)
		object = rc == 0 and ptr.reference or nil
	end)
	return object
end

local function dumpParty()
	local n = game.m_nCharacters
	log("party size m_nCharacters =", n)
	for i = 0, n - 1 do
		local id = game.m_characters:get(i)
		local obj = getObject(id)
		if obj then
			local sprite = EEex_CastUD(obj, "CGameSprite")
			local base = sprite.m_baseStats
			local derived = sprite.m_derivedStats
			local name = Infinity_FetchString(base.m_name)
			log(string.format("party[%d] id=%d name=%q hp=%d/%d (derived max %d) xp=%d gold=%d",
				i, id, name, base.m_hitPoints, base.m_maxHitPointsBase, derived.m_nMaxHitPoints, base.m_xp, base.m_gold))
		else
			log(string.format("party[%d] id=%d -> no object", i, id))
		end
	end
	log("party gold m_gameSave.m_nPartyGold =", game.m_gameSave.m_nPartyGold)
end

-- Run the party dump once a game is loaded: the UI pushes world menus through Infinity_PushMenu.
local done = false
local pushMenu = Infinity_PushMenu
Infinity_PushMenu = function(...)
	if not done and game.m_nCharacters > 0 then
		done = true
		local ok2, err2 = pcall(dumpParty)
		log("dumpParty", ok2, err2)
	end
	return pushMenu(...)
end
log("waiting for a loaded game (party dump on next menu push)")
