-- EEex-PSTEE dev test battery (not shipped): a full game session run by script on the dedicated save.
-- F9: start (or resume after a game load). Each step logs "PSTEE-BATTERY: PASS|FAIL|INFO <step>: <check> (detail)";
-- the run ends with a summary line. Steps run one after the other, driven by a per-frame tick (PTEEBAT.menu).
-- Needs the dev resources of bindings/test/make_battery_res.py (dev_override, deployed by eeexlua/build.py).
-- Script strings parsed at runtime lose spaces and most punctuation inside quotes: the chunks below avoid them.

PSTEE_BAT = PSTEE_BAT or { results = {}, pass = 0, fail = 0, flags = {} }
local B = PSTEE_BAT

local function log(kind, msg)
	print("PSTEE-BATTERY: " .. kind .. " " .. msg)
end

local function check(step, name, ok, detail)
	ok = ok and true or false
	if ok then B.pass = B.pass + 1 else B.fail = B.fail + 1 end
	table.insert(B.results, { step = step, name = name, ok = ok })
	log(ok and "PASS" or "FAIL", step .. ": " .. name .. (detail ~= nil and (" (" .. tostring(detail) .. ")") or ""))
end

local function info(step, msg) log("INFO", step .. ": " .. tostring(msg)) end

local function now() return Infinity_GetClockTicks() end

local function q(sprite, str) EEex_Action_QueueResponseStringOnAIBase(str, sprite) end

local function tno() return EEex_Sprite_GetInPortrait(0) end

local function party()
	local t = {}
	for i = 0, 5 do
		local s = EEex_Sprite_GetInPortrait(i)
		if s then table.insert(t, s) end
	end
	return t
end

local function isDead(sprite)
	return sprite == nil or EEex_BAnd(EEex_Sprite_GetState(sprite), 0x800) ~= 0
end

local function hp(sprite) return sprite.m_baseStats.m_hitPoints end

local function areaRes(sprite) return sprite.m_pArea and sprite.m_pArea.m_resref:get() or "" end

-- the area the test works in, and a point in it: TNO's, else the first party member in an area, else the visible one
local function workArea()
	for _, s in ipairs(party()) do
		if s.m_pArea then return s.m_pArea, s.m_pos.x, s.m_pos.y end
	end
	local area = EEex_Area_GetVisible()
	return area, 0, 0
end

-- every creature of the visible area whose CRE resref is `resref` (spawn order kept)
local function findAll(resref)
	local out = {}
	local area, x, y = workArea()
	if not area then return out end
	for _, obj in ipairs(EEex_Area_GetAllOfTypeStringInRange(area, x, y, "[ANYONE]", 0x7FFF, false, false)) do
		if EEex_GameObject_IsSprite(obj, true) and obj.m_resref:get() == resref then
			table.insert(out, obj)
		end
	end
	return out
end

local function unpause()
	if worldScreen:CheckIfPaused() then EEex_GameState_TogglePause(false, false) end
end

-------------------------------------------------------------------------------
-- Hook counters (installed once): Lua hooks EEex.dll calls, plus sprite listeners
-------------------------------------------------------------------------------

if not B.hooksInstalled then
	B.hooksInstalled = true
	B.count = {}
	local function count(key) B.count[key] = (B.count[key] or 0) + 1 end
	local function wrap(name, key)
		local orig = _G[name]
		if orig == nil then return end
		_G[name] = function(...) count(key) return orig(...) end
	end
	wrap("EEex_Opcode_Hook_OnAfterSwingCheckedOp248", "op248")
	wrap("EEex_Opcode_Hook_OnAfterSwingCheckedOp249", "op249")
	wrap("EEex_Opcode_Hook_OnOp214ApplyEffect", "op214")
	wrap("EEex_Opcode_Hook_OnOp333CopiedSelf", "op333")
	EEex_Sprite_AddAlterBaseWeaponDamageListener(function(context) count("alterDamage") end)
	EEex_Sprite_AddBlockWeaponHitListener(function(context) count("blockHit") return false end)
	EEex_Opcode_AddListsResolvedListener(function(sprite) count("listsResolved") end)
	EEex_Action_AddSpriteStartedActionListener(function(sprite, action)
		count("actionStarted")
		if B.watchActions and B.watchActions[sprite.m_id] then
			table.insert(B.watchActions[sprite.m_id], action.m_actionID)
		end
	end)
	EEex_Sprite_AddLoadedListener(function(sprite) count("spriteLoaded") end)
	EEex_Projectile_RegisterGlobalMutator("PSTEEBATGM")
	-- Lua data saved with the sprite (EEex marshal handlers): written before the save, read back on load
	EEex_Sprite_AddMarshalHandlers("PSTEE_Battery",
		function(sprite)
			local v = EEex_GetUDAux(sprite)["PSTEE_Battery_Marshal"]
			return v and { ["v"] = v } or {}
		end,
		function(sprite, read)
			if read["v"] then
				EEex_GetUDAux(sprite)["PSTEE_Battery_Marshal"] = read["v"]
				B.flags.marshalImported = read["v"]
			end
		end
	)
end

PSTEEBATGM = {
	["typeMutator"] = function(context) B.count.decode = (B.count.decode or 0) + 1 end,
	["projectileMutator"] = function(context) B.count.decoded = (B.count.decoded or 0) + 1 end,
}

-- InvokeLua (op402) targets of the dev resources
function PTEEB248(effect, sprite)
	B.flags.op248Targets = B.flags.op248Targets or {}
	B.flags.op248Targets[sprite.m_id] = true
end
function PTEEB326(effect, sprite)
	B.flags.op326 = (B.flags.op326 or 0) + 1
	B.flags.op326Target = sprite.m_id
	B.flags.op326Source = effect.m_sourceId
end
-- op403 spy: logs every op326 effect as it is added to a creature (fields as the engine sees them)
function PTEEBSPY(op403, effect, sprite)
	if effect.m_effectId == 326 then
		print(string.format("PSTEE-BATTERY: INFO op326: added to %d: special %d param1 %d param2 %d source %d", sprite.m_id,
			effect.m_special, effect.m_effectAmount, effect.m_dWFlags, effect.m_sourceId))
	end
	return false
end
function PTEEB333(effect, sprite) B.flags.op333Spell = (B.flags.op333Spell or 0) + 1 end
function PTEEB214(effect, sprite)
	B.flags.op214Func = (B.flags.op214Func or 0) + 1
	return EEex_Actionbar_GetSpellButtonDataIterator(EEex_Resource_GetValidSpellsIterator(EEex_Utility_ValuesIterator("SPWI101")))
end

-------------------------------------------------------------------------------
-- Steps
-------------------------------------------------------------------------------

local COMPANIONS = { "ANNAH", "DAKKON", "NORDOM", "IGNUS" }
-- areas and an entrance point of each (ARE entrance list), then back to the start and on to the first one to rest.
-- The Mortuary's floors: the base save (eeex-battery) is before the escape, and reaching the Hive starts that plot
-- (cutscene + dialog that cancel the travel orders); AR0500 also starts Morte's kidnapping. AR0201's Dustman guard
-- (0201GD1, DDUSTGU) talks to the party on arrival: with a member still in transit (no area yet), vanilla
-- CScreenWorld::StartDialog writes through its null m_pArea (PT 0x3658a1) and the game crashes. Not used.
local AREAS = {
	{ "AR0203", 676, 1606 }, { "AR0202", 1316, 2247 }, { "AR0203", 2938, 1511 }, { "AR0202", 1184, 2296 },
}
-- projectile spells cast for real (decode path), Torment mage / priest / innate
local CAST_SPELLS = {
	"SPWI101", "SPWI102", "SPWI103", "SPWI104", "SPWI105", "SPWI107", "SPWI111", "SPWI113", "SPWI115", "SPWI117",
	"SPWI118", "SPWI201", "SPWI203", "SPWI205", "SPWI212", "SPWI301", "SPWI305", "SPWI310", "SPWI401", "SPWI405",
	"SPPR101", "SPPR103", "SPPR201", "SPPR301", "SPIN101", "SPIN103",
}

local STEPS = {}
local function step(t) table.insert(STEPS, t) end

-- 1. API sweep: every public getter of EEex's Lua API on every party member, with pcall
step({ name = "api", run = function(S)
	local t = tno()
	local errs, calls = 0, 0
	local function try(label, f, ...)
		calls = calls + 1
		local ok, err = pcall(f, ...)
		if not ok then errs = errs + 1 info("api", "error in " .. label .. ": " .. tostring(err)) end
		return ok
	end
	for _, s in ipairs(party()) do
		local n = EEex_Sprite_GetName(s)
		for _, fname in ipairs({ "EEex_Sprite_GetName", "EEex_Sprite_GetNameRef", "EEex_Sprite_GetState",
			"EEex_Sprite_GetActiveStats", "EEex_Sprite_GetModalState", "EEex_Sprite_GetModalTimer",
			"EEex_Sprite_GetContingencyTimer", "EEex_Sprite_GetCastTimer", "EEex_Sprite_GetModalTimerPercentage",
			"EEex_Sprite_GetContingencyTimerPercentage", "EEex_Sprite_GetCastTimerPercentage",
			"EEex_Sprite_GetPersonalSpace", "EEex_Sprite_GetPortraitIndex", "EEex_Sprite_GetCharacterIndex",
			"EEex_Sprite_GetUUID" }) do
			try(fname .. " " .. n, _G[fname], s)
		end
		for id = 0, 255 do try("GetStat " .. id .. " " .. n, EEex_Sprite_GetStat, s, id) end
		try("GetExtendedStat 1000 " .. n, EEex_Sprite_GetExtendedStat, s, 1000)
		for state = 0, 255 do try("GetSpellState " .. state .. " " .. n, EEex_Sprite_GetSpellState, s, state) end
		try("GetLocalInt " .. n, EEex_Sprite_GetLocalInt, s, "PTEEBAT")
		try("SetLocalInt " .. n, EEex_Sprite_SetLocalInt, s, "PTEEBAT", 7)
		try("SetLocalString " .. n, EEex_Sprite_SetLocalString, s, "PTEEBATS", "abc")
		check("api", "local int/string round trip " .. n, EEex_Sprite_GetLocalInt(s, "PTEEBAT") == 7
			and EEex_Sprite_GetLocalString(s, "PTEEBATS") == "abc")
		local iterCount = 0
		for _, itf in ipairs({ "GetKnownMageSpellsIterator", "GetKnownPriestSpellsIterator", "GetKnownInnateSpellsIterator",
			"GetValidKnownMageSpellsIterator", "GetValidKnownPriestSpellsIterator", "GetValidKnownInnateSpellsIterator",
			"GetKnownMageSpellsWithAbilityIterator", "GetKnownPriestSpellsWithAbilityIterator",
			"GetKnownInnateSpellsWithAbilityIterator" }) do
			try(itf .. " " .. n, function()
				local maxLevel = itf:find("Priest") and 7 or 9 -- priest spell levels are 1..7
				local it = itf:find("Innate") and _G["EEex_Sprite_" .. itf](s) or _G["EEex_Sprite_" .. itf](s, 1, maxLevel)
				for _ in it do iterCount = iterCount + 1 end
			end)
		end
		info("api", n .. ": " .. iterCount .. " spell iterator entries")
		try("GetCasterLevelForSpell " .. n, EEex_Sprite_GetCasterLevelForSpell, s, "SPWI101", true)
		try("CountAllOfTypeStringInRange " .. n, EEex_Sprite_CountAllOfTypeStringInRange, s, "[ANYONE]", 400, false)
	end
	try("EEex_Test_IDSFunctions", EEex_Test_IDSFunctions)
	try("GetVisible", EEex_Area_GetVisible)
	try("Area variable", function()
		EEex_Area_SetVariableInt(t.m_pArea, "PTEEBAT", 3)
		check("api", "area variable round trip", EEex_Area_GetVariableInt(t.m_pArea, "PTEEBAT") == 3)
	end)
	try("Global variable", function()
		EEex_GameState_SetGlobalInt("PTEEBAT", 5)
		EEex_GameState_SetGlobalString("PTEEBATS", "xyz")
		check("api", "global variable round trip", EEex_GameState_GetGlobalInt("PTEEBAT") == 5
			and EEex_GameState_GetGlobalString("PTEEBATS") == "xyz")
	end)
	try("Nearest open position", EEex_Area_GetNearestOpenPosition, t.m_pArea, t.m_pos.x, t.m_pos.y, 3)
	try("Actionbar", function() EEex_Actionbar_GetState() EEex_Actionbar_GetArray() end)
	try("Keys", function() check("api", "key name round trip", EEex_Key_GetName(EEex_Key_GetFromName("A")) == "A") end)
	try("Resource", function()
		local spl = EEex_Resource_Demand("SPWI101", "SPL")
		check("api", "SPL demand + ability", spl ~= nil and EEex_Resource_GetSpellAbility(spl, 0) ~= nil)
		local itm = EEex_Resource_Demand("DAGGER", "ITM") or EEex_Resource_Demand("DAGG01", "ITM")
		info("api", "ITM demand " .. tostring(itm ~= nil))
	end)
	try("Script", function()
		local script = EEex_Resource_LoadScript("NONE", false)
		check("api", "script load", script ~= nil)
		if script then EEex_Resource_FreeScript(script) end
	end)
	try("Object parse", function()
		local found = EEex_Object_EvalStringAsAIBase("Player2", t)
		check("api", "object Player2", found ~= nil and found.m_id == EEex_Sprite_GetInPortrait(1).m_id)
	end)
	try("Trigger", function()
		check("api", "trigger InParty(Myself)", EEex_Trigger_EvalConditionalStringAsAIBase("InParty(Myself)", t) == true)
	end)
	-- EEex_Action_ExecuteResponseStringOnAIBaseInstantly: copies / restores m_curAction through EEex_MemoryManager
	-- (CAIAction copy + destructor; Torment inlines ~CAIAction, replaced in EEex_Alias.lua)
	try("instant actions", function()
		for i = 1, 5 do
			EEex_Action_ExecuteResponseStringOnAIBaseInstantly('SetGlobal("PTEEBATI","GLOBAL",' .. i .. ')', t)
		end
		check("api", "instant action x5 (CAIAction copy + destruct)", EEex_GameState_GetGlobalInt("PTEEBATI") == 5,
			EEex_GameState_GetGlobalInt("PTEEBATI"))
	end)
	check("api", "no Lua error in " .. calls .. " calls", errs == 0, errs .. " errors")
end })

-- 2. Companions join (party of 6), timers get one instance set per portrait
step({ name = "companions", timeout = 30000, run = function(S)
	-- fill the free party slots only, with companions not already in the party (nobody when the party is full)
	S.before = EEex_Sprite_GetNumCharacters()
	local inParty = {}
	for _, s in ipairs(party()) do inParty[s.m_resref:get()] = true end
	S.toJoin = {}
	for _, c in ipairs(COMPANIONS) do
		if #S.toJoin < 6 - S.before and not inParty[c] then table.insert(S.toJoin, c) end
	end
	for _, c in ipairs(S.toJoin) do
		if #findAll(c) == 0 then q(tno(), 'CreateCreatureObject("' .. c .. '",Myself,0,0,0)') end
	end
	info("companions", "party of " .. S.before .. ", joining: " .. (#S.toJoin > 0 and table.concat(S.toJoin, ", ") or "nobody"))
end, wait = function(S)
	if not S.joined then
		for _, c in ipairs(S.toJoin) do if #findAll(c) == 0 then return false end end
		for _, c in ipairs(S.toJoin) do
			local s = findAll(c)[1]
			if EEex_Sprite_GetPortraitIndex(s) == -1 then q(s, "JoinParty()") end
		end
		S.joined = true
		return false
	end
	return EEex_Sprite_GetNumCharacters() >= 6
end, done = function(S)
	check("companions", "party of 6", EEex_Sprite_GetNumCharacters() == 6, S.before .. " -> " .. EEex_Sprite_GetNumCharacters())
	B.flags.partyBefore, B.flags.joined = S.before, S.toJoin
	for i = 0, 5 do
		local s = EEex_Sprite_GetInPortrait(i)
		info("companions", "portrait " .. i .. ": " .. (s and EEex_Sprite_GetName(s) or "none"))
	end
	local n = 0
	for _ in pairs(B3Timer_Private_TemplateInstancesByPortrait or {}) do n = n + 1 end
	if B3Timer_Private_TemplateInstancesByPortrait then
		check("companions", "timer instances for every portrait slot", n >= 6, n)
	else
		info("companions", "timer module disabled: no timer check")
	end
end })

-- 3. Experience and level up
step({ name = "levelup", timeout = 15000, run = function(S)
	S.xp, S.level = {}, {}
	for _, s in ipairs(party()) do S.xp[s.m_id] = s.m_baseStats.m_xp S.level[s.m_id] = s.m_baseStats.m_level1 end
	q(tno(), "AddexperienceParty(400000)")
	S.t0 = now()
end, wait = function(S) return now() - S.t0 > 5000 end, done = function(S)
	for _, s in ipairs(party()) do
		local n = EEex_Sprite_GetName(s)
		check("levelup", "XP gained " .. n, s.m_baseStats.m_xp > S.xp[s.m_id], S.xp[s.m_id] .. " -> " .. s.m_baseStats.m_xp)
		info("levelup", n .. " level " .. S.level[s.m_id] .. " -> " .. s.m_baseStats.m_level1
			.. " (active level stat " .. EEex_Sprite_GetStat(s, 34) .. ")")
	end
end })

-- 4. Opcode extensions that need no combat
step({ name = "opcodes", timeout = 30000, run = function(S)
	local t, morte = tno(), EEex_Sprite_GetInPortrait(1)
	-- op101 + saving throw bit 23: bypasses the immunity
	EEex_GameObject_ApplyEffect(morte, { ["effectID"] = 101, ["dwFlags"] = 12, ["durationType"] = 0, ["duration"] = 30, ["sourceID"] = morte.m_id })
	local h0 = hp(morte)
	EEex_GameObject_ApplyEffect(morte, { ["effectID"] = 12, ["effectAmount"] = 1, ["sourceID"] = morte.m_id })
	local h1 = hp(morte)
	EEex_GameObject_ApplyEffect(morte, { ["effectID"] = 12, ["effectAmount"] = 1, ["savingThrow"] = 0x800000, ["sourceID"] = morte.m_id })
	local h2 = hp(morte)
	check("opcodes", "op101 blocks op12", h1 == h0, h0 .. " -> " .. h1)
	check("opcodes", "op101 bypassed by saving throw bit 23", h2 == h1 - 1, h1 .. " -> " .. h2)
	-- op146 special bit 1 (value 2) -> SpellNoDec (191); op148 special bit 0 -> SpellPointNoDec (192)
	B.watchActions = { [t.m_id] = {} }
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 146, ["res"] = "SPWI101", ["special"] = 2, ["sourceID"] = t.m_id, ["sourceTarget"] = morte.m_id })
	-- op214 param2 3: the spell list comes from a Lua function
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 214, ["dwFlags"] = 3, ["res"] = "PTEEB214", ["sourceID"] = t.m_id })
	-- op219 (via op177 + EFF: param3 5 overrides the bonus of 2), op280, op333 (via op177 + EFF: param3 bit 0)
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 177, ["effectAmount"] = 0, ["dwFlags"] = 2, ["res"] = "PTEEB219", ["sourceID"] = t.m_id })
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 280, ["effectAmount"] = 5, ["special"] = 1, ["durationType"] = 0, ["duration"] = 10, ["sourceID"] = t.m_id })
	S.t0 = now()
end, wait = function(S)
	if not S.op148 and now() - S.t0 > 3000 then
		local t = tno()
		EEex_GameObject_ApplyEffect(t, { ["effectID"] = 148, ["res"] = "SPWI101", ["special"] = 1, ["sourceID"] = t.m_id,
			["targetX"] = t.m_pos.x + 40, ["targetY"] = t.m_pos.y })
		S.op148 = true
	end
	return now() - S.t0 > 9000
end, done = function(S)
	local acts = B.watchActions[tno().m_id] or {}
	local seen = {}
	for _, a in ipairs(acts) do seen[a] = true end
	check("opcodes", "op146 special 2 -> SpellNoDec (191)", seen[191], table.concat(acts, ","))
	check("opcodes", "op148 special 1 -> SpellPointNoDec (192)", seen[192], table.concat(acts, ","))
	check("opcodes", "op214 param2 3 calls the Lua hook", (B.count.op214 or 0) > 0, B.count.op214)
	check("opcodes", "op214 param2 3 calls the resource function", (B.flags.op214Func or 0) > 0, B.flags.op214Func)
	info("opcodes", "op219 / op280 applied (EEex.dll only, no Lua-visible result)")
	B.watchActions = nil
	EEex_Actionbar_RestoreLastState()
end })

-- 5. Combat: rats + skeletons, op248 special 1 through op120, op342 combat round override, op326 flip, op333
step({ name = "combat-spawn", timeout = 20000, run = function(S)
	for _ = 1, 3 do q(tno(), 'CreateCreatureObject("RAT",Myself,0,0,0)') end
	for _ = 1, 2 do q(tno(), 'CreateCreatureObject("SKELW",Myself,0,0,0)') end
end, wait = function(S)
	return #findAll("RAT") >= 3 and #findAll("SKELW") >= 2
end, done = function(S)
	local rats, skels = findAll("RAT"), findAll("SKELW")
	check("combat-spawn", "3 rats + 2 skeletons", #rats >= 3 and #skels >= 2, #rats .. " / " .. #skels)
	if #rats < 3 or #skels < 2 then error("no enemies to test with") end
	B.enemies = {}
	for _, s in ipairs(rats) do table.insert(B.enemies, s.m_id) end
	for _, s in ipairs(skels) do table.insert(B.enemies, s.m_id) end
	for _, id in ipairs(B.enemies) do q(EEex_GameObject_Get(id), "ChangeEnemyAlly(Myself,255)") end
	local t = tno()
	-- attack info before op219-like changes: hit chance of every party member against the first skeleton
	for _, s in ipairs(party()) do
		local ok, chance = pcall(B3AttackInfo_Private_GetWeaponHitChance, s, skels[1], false)
		check("combat-spawn", "attack info hit chance " .. EEex_Sprite_GetName(s), ok and type(chance) == "number", tostring(chance))
	end
	local ok, back = pcall(B3AttackInfo_Private_GetWeaponHitChance, skels[1], t, false)
	B.flags.skelHitBefore = ok and back or nil
	info("combat-spawn", "skeleton hit chance on TNO with op219 (+5 vs ENEMY): " .. tostring(back))
	-- op248 special 1 on TNO: its .EFF reaches the first rat although the rat is immune to weapons (op120)
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 248, ["res"] = "PTEEB248", ["special"] = 1, ["durationType"] = 0, ["duration"] = 120, ["sourceID"] = t.m_id })
	EEex_GameObject_ApplyEffect(rats[1], { ["effectID"] = 120, ["dwFlags"] = 0, ["durationType"] = 0, ["duration"] = 120, ["sourceID"] = rats[1].m_id })
	EEex_GameObject_ApplyEffect(rats[1], { ["effectID"] = 18, ["effectAmount"] = 2000, ["dwFlags"] = 0, ["durationType"] = 0, ["duration"] = 120, ["sourceID"] = rats[1].m_id })
	B.flags.op248Rat = rats[1].m_id
	-- op342 param2 5 on the skeletons: combat round 1 drawn from RNDBASE2
	for _, s in ipairs(skels) do
		EEex_GameObject_ApplyEffect(s, { ["effectID"] = 342, ["effectAmount"] = 1, ["dwFlags"] = 5, ["res"] = "RNDBASE2", ["durationType"] = 0, ["duration"] = 120, ["sourceID"] = s.m_id })
	end
	-- op333 static charge on TNO (via op177 + EFF, param3 bit 0)
	EEex_GameObject_ApplyEffect(t, { ["effectID"] = 177, ["effectAmount"] = 0, ["dwFlags"] = 2, ["res"] = "PTEEB333", ["sourceID"] = t.m_id })
end })

-- op326 on a rat from TNO, SPLPROT rows 128 ENOUGHINT / 129 NOTENOINT (INT >= / < param1), param1 = TNO's INT:
-- true for TNO, false for a rat. (The EA rows compare through an EA-category helper, not the raw EA: not used.)
-- EEex.dll flips source and target on special bit 1 (value 2; upstream's doc says bit 0, its code tests & 2).
local OP326_CASES = {
	{ 129, 0, 1, "NOTENOINT, no flip: rat INT < TNO INT, applied (control)" },
	{ 128, 0, 0, "ENOUGHINT, no flip: rat INT < TNO INT, not applied" },
	{ 128, 2, 1, "ENOUGHINT, flip: checks TNO, applied" },
	{ 129, 2, 0, "NOTENOINT, flip: checks TNO, not applied" },
	{ 128, 0, 1, "ENOUGHINT, no flip, on TNO itself: applied (rule control)", "tno" },
}
-- each case on its own fresh rat (op326 stays on the creature and fires again on later list evaluations)
step({ name = "op326", timeout = 30000, run = function(S)
	unpause()
	S.before = {}
	for _, r in ipairs(findAll("RAT")) do S.before[r.m_id] = true end
	for _ = 1, #OP326_CASES do q(tno(), 'CreateCreatureObject("RAT",Myself,0,0,0)') end
	S.i, S.next = 0, now()
end, wait = function(S)
	if S.rats == nil then
		local fresh = {}
		for _, r in ipairs(findAll("RAT")) do if not S.before[r.m_id] then table.insert(fresh, r) end end
		if #fresh < #OP326_CASES then return false end
		S.rats = fresh
		for _, r in ipairs(fresh) do
			q(r, "ChangeEnemyAlly(Myself,255)")
			EEex_GameObject_ApplyEffect(r, { ["effectID"] = 403, ["res"] = "PTEEBSPY", ["durationType"] = 0, ["duration"] = 60, ["sourceID"] = r.m_id })
		end
		S.next = now() + 1000
		return false
	end
	if now() < S.next then return false end
	if S.i > 0 then
		local c = OP326_CASES[S.i]
		local got = B.flags.op326 or 0
		check("op326", c[4], (c[3] == 1 and got >= 1) or (c[3] == 0 and got == 0), got .. " calls, spell source " .. tostring(B.flags.op326Source)
			.. ", TNO " .. tno().m_id .. ", rat " .. S.rats[S.i].m_id)
		B.flags.op326Source = nil
	end
	S.i = S.i + 1
	local c = OP326_CASES[S.i]
	if c == nil then
		-- diagnostic: a permanent op326 (special 2) stays in the list, its fields are read back
		local r = S.rats[1]
		EEex_GameObject_ApplyEffect(r, { ["effectID"] = 326, ["effectAmount"] = 2, ["dwFlags"] = 102, ["res"] = "PTEEB326",
			["special"] = 2, ["durationType"] = 1, ["sourceID"] = tno().m_id })
		for _, listName in ipairs({ "m_timedEffectList", "m_equipedEffectList" }) do
			EEex_Utility_IterateCPtrList(r[listName], function(effect)
				if effect.m_effectId == 326 then
					info("op326", string.format("%s: special %d param1 %d param2 %d source %d timing %d", listName,
						effect.m_special, effect.m_effectAmount, effect.m_dWFlags, effect.m_sourceId, effect.m_durationType))
				end
			end)
		end
		for _, r2 in ipairs(S.rats) do q(r2, "DestroySelf()") end
		return true
	end
	B.flags.op326 = 0
	-- param1: TNO's INT (read, not assumed)
	local ea = EEex_Sprite_GetStat(tno(), 38)
	if S.i == 1 then info("op326", "TNO INT " .. ea .. ", rat INT " .. EEex_Sprite_GetStat(S.rats[1], 38)) end
	local target = c[5] == "tno" and tno() or S.rats[S.i]
	EEex_GameObject_ApplyEffect(target, { ["effectID"] = 326, ["effectAmount"] = ea, ["dwFlags"] = c[1], ["res"] = "PTEEB326",
		["special"] = c[2], ["sourceID"] = tno().m_id })
	S.next = now() + 1500
	return false
end })

step({ name = "combat", timeout = 120000, run = function(S)
	unpause()
	S.xp = tno().m_baseStats.m_xp
	S.count0 = { alterDamage = B.count.alterDamage or 0, blockHit = B.count.blockHit or 0 }
	-- TNO (op248 special 1) attacks the op120 rat, the others the nearest enemy
	local function orders()
		local rat = EEex_GameObject_Get(B.flags.op248Rat)
		local ratDone = isDead(rat) or (B.flags.op248Targets or {})[B.flags.op248Rat]
		for i, s in ipairs(party()) do
			if i == 1 and not ratDone then
				EEex_LuaObject = rat
				q(s, "Attack(EEex_LuaObject)")
			else
				q(s, "Attack(NearestEnemyOf(Myself))")
			end
		end
	end
	S.orders = orders
	orders()
	S.nextOrder = now() + 6000
end, wait = function(S)
	local alive = 0
	for _, id in ipairs(B.enemies) do if not isDead(EEex_GameObject_Get(id)) then alive = alive + 1 end end
	if alive > 0 and now() > S.nextOrder then
		S.nextOrder = now() + 6000
		S.orders()
		-- the op120 rat cannot be hurt by weapons: kill it once its .EFF was seen (or after 40 s)
		if (B.flags.op248Targets or {})[B.flags.op248Rat] or now() - S.t0 > 40000 then
			local r = EEex_GameObject_Get(B.flags.op248Rat)
			if r and not isDead(r) then q(r, "Kill(Myself)") end
		end
	end
	return alive == 0
end, done = function(S)
	local alive = 0
	for _, id in ipairs(B.enemies) do if not isDead(EEex_GameObject_Get(id)) then alive = alive + 1 end end
	check("combat", "every enemy dead", alive == 0, alive .. " alive" .. (S.timedOut and ", timed out" or ""))
	check("combat", "weapon damage listener called", (B.count.alterDamage or 0) > S.count0.alterDamage, B.count.alterDamage)
	check("combat", "block weapon hit listener called", (B.count.blockHit or 0) > S.count0.blockHit, B.count.blockHit)
	check("combat", "op248 Lua hook called", (B.count.op248 or 0) > 0, B.count.op248)
	check("combat", "op248 special 1: .EFF reaches the op120 rat", (B.flags.op248Targets or {})[B.flags.op248Rat] == true)
	check("combat", "XP from kills", tno().m_baseStats.m_xp > S.xp, S.xp .. " -> " .. tno().m_baseStats.m_xp)
	check("combat", "op333 copy hook called", (B.count.op333 or 0) > 0, B.count.op333)
	info("combat", "op333 spell casts: " .. tostring(B.flags.op333Spell) .. ", lists resolved: " .. tostring(B.count.listsResolved))
end })

-- 6. Spells: real casts (projectile decode path) on a skeleton, then every Torment spell applied on dummies
step({ name = "spells-cast", timeout = 400000, run = function(S)
	for _ = 1, 2 do q(tno(), 'CreateCreatureObject("SKELW",Myself,0,0,0)') end
	S.i, S.decode0, S.phase = 0, B.count.decode or 0, "spawn"
	unpause()
end, wait = function(S)
	if S.phase == "spawn" then
		local skels = {}
		for _, s in ipairs(findAll("SKELW")) do if not isDead(s) then table.insert(skels, s) end end
		if #skels < 2 then return false end
		S.target = skels[1]
		for _, s in ipairs(skels) do
			q(s, "ChangeEnemyAlly(Myself,255)")
			-- held and hardened so the casts never end the test early
			EEex_GameObject_ApplyEffect(s, { ["effectID"] = 175, ["durationType"] = 0, ["duration"] = 600, ["sourceID"] = s.m_id })
			EEex_GameObject_ApplyEffect(s, { ["effectID"] = 18, ["effectAmount"] = 2000, ["dwFlags"] = 0, ["durationType"] = 0, ["duration"] = 600, ["sourceID"] = s.m_id })
		end
		S.phase, S.next = "cast", now()
		return false
	end
	if now() < S.next then return false end
	S.i = S.i + 1
	if S.i > #CAST_SPELLS then return true end
	local t = tno()
	if isDead(S.target) then S.target = findAll("SKELW")[2] end
	q(t, "ClearAllActions()")
	q(t, 'ReallyForceSpellRES("' .. CAST_SPELLS[S.i] .. '",NearestEnemyOf(Myself))')
	S.next = now() + 9000
	return false
end, done = function(S)
	check("spells-cast", "casts reached the decode hook", (B.count.decode or 0) > S.decode0, (S.decode0 .. " -> " .. tostring(B.count.decode)))
	check("spells-cast", "every cast issued", S.i > #CAST_SPELLS, S.i - 1 .. " / " .. #CAST_SPELLS)
end })

step({ name = "spells-apply", timeout = 300000, run = function(S)
	S.list = {}
	for _, n in ipairs(PSTEE_BAT_ALL_SPELLS or {}) do table.insert(S.list, n) end
	S.i, S.next, S.errs = 0, now(), 0
end, wait = function(S)
	if now() < S.next then return false end
	local target = nil
	for _, s in ipairs(findAll("SKELW")) do if not isDead(s) then target = s break end end
	if not target then
		q(tno(), 'CreateCreatureObject("SKELW",Myself,0,0,0)')
		S.next = now() + 1500
		return false
	end
	for _ = 1, 4 do
		S.i = S.i + 1
		local n = S.list[S.i]
		if n == nil then return true end
		local ok, err = pcall(q, target, 'ApplySpellRES("' .. n .. '",Myself)')
		if not ok then S.errs = S.errs + 1 info("spells-apply", n .. ": " .. tostring(err)) end
	end
	S.next = now() + 1200
	return false
end, done = function(S)
	check("spells-apply", "every Torment player spell applied without error", S.errs == 0 and S.i > #S.list, (S.i - 1) .. " / " .. #S.list .. ", " .. S.errs .. " errors")
	for _, s in ipairs(party()) do if isDead(s) then q(s, "Resurrect()") end end
end })

-- 7a. The companions the battery added leave (before travelling: in the Mortuary, before the escape, their own
-- scripts keep them from travelling or leaving once apart)
step({ name = "companions-leave", timeout = 20000, run = function(S)
	S.target = B.flags.partyBefore or 2
	local added = {}
	for _, c in ipairs(B.flags.joined or {}) do added[c] = true end
	for _, s in ipairs(party()) do
		if added[s.m_resref:get()] then q(s, "LeaveParty()") end
	end
	unpause()
end, wait = function(S) return EEex_Sprite_GetNumCharacters() <= S.target end, done = function(S)
	check("companions-leave", "party back to its size before the run", EEex_Sprite_GetNumCharacters() == S.target,
		EEex_Sprite_GetNumCharacters() .. " / " .. S.target)
end })

-- 7. Areas: the party travels through Sigil and back, EEex APIs on every new area
step({ name = "areas", timeout = 600000, run = function(S)
	S.start = areaRes(tno())
	S.i, S.waiting = 0, false
	S.marshal = "bat" .. now()
	EEex_GetUDAux(tno())["PSTEE_Battery_Marshal"] = S.marshal
	B.flags.marshalValue = S.marshal
	unpause()
end, wait = function(S)
	local t = tno()
	if S.waiting then
		local target = S.i <= #AREAS and AREAS[S.i][1] or (S.i == #AREAS + 1 and S.start) or AREAS[1][1]
		if areaRes(t) ~= target and now() > S.settle + 20000 then
			-- not there yet: an area event or cutscene (e.g. leaving the Mortuary the first time) cancels the orders
			for _, s in ipairs(party()) do
				q(s, 'LeaveAreaLUA("' .. target .. '","",[' .. S.dest[2] .. '.' .. S.dest[3] .. '],0)')
			end
			S.settle = now()
			return false
		end
		if areaRes(t) ~= target or now() < S.settle then return false end
		local count = EEex_Area_CountAllOfTypeStringInRange(t.m_pArea, t.m_pos.x, t.m_pos.y, "[ANYONE]", 0x7FFF, false)
		check("areas", "arrived in " .. target, true, count .. " objects")
		local together = 0
		for _, s in ipairs(party()) do if areaRes(s) == target then together = together + 1 end end
		check("areas", "party together in " .. target, together == #party(), together .. " / " .. #party())
		S.waiting = false
		if S.i == #AREAS + 1 then check("areas", "back in the start area " .. S.start, areaRes(t) == S.start) end
		if S.i > #AREAS + 1 then return true end
		return false
	end
	S.i = S.i + 1
	local dest = AREAS[S.i] or (S.i == #AREAS + 1 and { S.startArea or S.start, S.startX, S.startY }) or AREAS[1]
	if S.i == 1 then S.startArea, S.startX, S.startY = S.start, t.m_pos.x, t.m_pos.y end
	for _, s in ipairs(party()) do
		q(s, 'LeaveAreaLUA("' .. dest[1] .. '","",[' .. dest[2] .. '.' .. dest[3] .. '],0)')
	end
	S.dest = dest
	S.waiting, S.settle = true, now() + 4000
	return false
end, done = function(S)
	check("areas", "Lua data kept on TNO across areas", EEex_GetUDAux(tno())["PSTEE_Battery_Marshal"] == S.marshal)
end })

-- 8. Rest, then save (the marshal value must come back after the reload: F9 after loading the save)
step({ name = "rest", timeout = 60000, run = function(S)
	for _, s in ipairs(party()) do
		EEex_GameObject_ApplyEffect(s, { ["effectID"] = 12, ["effectAmount"] = 3, ["sourceID"] = s.m_id })
	end
	S.hp = {}
	for _, s in ipairs(party()) do S.hp[s.m_id] = hp(s) end
	for _, s in ipairs(party()) do
		local function n(it) local c = 0 for _ in it do c = c + 1 end return c end
		info("rest", string.format("%s: hp %d / %d, known priest %d mage %d innate %d", EEex_Sprite_GetName(s), hp(s),
			EEex_Sprite_GetActiveStats(s).m_nMaxHitPoints, n(EEex_Sprite_GetKnownPriestSpellsIterator(s, 1, 7)),
			n(EEex_Sprite_GetKnownMageSpellsIterator(s, 1, 9)), n(EEex_Sprite_GetKnownInnateSpellsIterator(s))))
	end
	-- F7 run: stop before resting (save here, then rest by hand with and without EEex)
	if B.noRest then S.t0 = now() - 15000 return end
	-- not RestParty(): forced where resting is not allowed (the Mortuary), Torment's PartyHeal never returns,
	-- with or without EEex (reproduced in the vanilla game from the same save). Each creature rests on its own.
	-- the scripted Rest() heals nobody (vanilla behaviour, same without EEex): the player rests by hand instead
	S.t0 = now()
	unpause()
end, wait = function(S) return now() - S.t0 > 15000 end, done = function(S)
	for _, s in ipairs(party()) do
		info("rest", "hp " .. EEex_Sprite_GetName(s) .. " " .. hp(s))
	end
	B.awaitingLoad = true
	B.flags.partyAtSave = EEex_Sprite_GetNumCharacters()
	-- quick save (the reload step checks what came back); tools/battery.py then loads it (F6) and resumes (F9)
	worldScreen:OnQuickSaveButtonClick(false)
	info("rest", "rest by hand (party hurt), save, load the save, then press F9 (marshal value " .. tostring(B.flags.marshalValue) .. ")")
end, stopAfter = true })

-- 9. After the reload
step({ name = "reload", run = function(S)
	check("reload", "sprites loaded listener after load", (B.count.spriteLoaded or 0) > 0, B.count.spriteLoaded)
	check("reload", "marshal importer ran on load", B.flags.marshalImported == B.flags.marshalValue, tostring(B.flags.marshalImported))
	check("reload", "marshal handler: Lua data saved with TNO came back", EEex_GetUDAux(tno())["PSTEE_Battery_Marshal"] == B.flags.marshalValue,
		tostring(EEex_GetUDAux(tno())["PSTEE_Battery_Marshal"]) .. " / " .. tostring(B.flags.marshalValue))
	check("reload", "same party size after load", EEex_Sprite_GetNumCharacters() == B.flags.partyAtSave,
		EEex_Sprite_GetNumCharacters() .. " / " .. tostring(B.flags.partyAtSave))
end })

-------------------------------------------------------------------------------
-- Runner
-------------------------------------------------------------------------------

local function startStep()
	-- reduced run (F8): skip the steps not listed in B.only
	while B.only and STEPS[B.stepIndex] and not B.only[STEPS[B.stepIndex].name] do B.stepIndex = B.stepIndex + 1 end
	local st = STEPS[B.stepIndex]
	if st == nil then
		local failed = {}
		for _, r in ipairs(B.results) do if not r.ok then table.insert(failed, r.step .. ": " .. r.name) end end
		log("DONE", string.format("%d pass / %d fail", B.pass, B.fail) .. (#failed > 0 and (" -- failed: " .. table.concat(failed, "; ")) or ""))
		B.running = false
		Infinity_PopMenu("PSTEE_Battery_Menu")
		return
	end
	info(st.name, "start")
	unpause() -- actions and effects need game time (a loaded save may come back paused)
	B.S = { t0 = now() }
	local ok, err = pcall(st.run, B.S)
	if not ok then check(st.name, "run", false, err) B.S.failed = true end
end

local function finishStep()
	local st = STEPS[B.stepIndex]
	if st.done and not B.S.failed then
		local ok, err = pcall(st.done, B.S)
		if not ok then check(st.name, "checks", false, err) end
	end
	B.stepIndex = B.stepIndex + 1
	if st.stopAfter then
		B.running = false
		Infinity_PopMenu("PSTEE_Battery_Menu")
		log("PAUSE", string.format("%d pass / %d fail so far; next step: %s", B.pass, B.fail, STEPS[B.stepIndex] and STEPS[B.stepIndex].name or "none"))
		return
	end
	startStep()
end

function PSTEE_Battery_Tick()
	if not B.running then return false end
	local st = STEPS[B.stepIndex]
	if st == nil then return false end
	if B.S.failed or st.wait == nil then finishStep() return false end
	local ok, res = pcall(st.wait, B.S)
	if not ok then
		check(st.name, "wait", false, res)
		B.S.failed = true
		finishStep()
	elseif res then
		finishStep()
	elseif now() - B.S.t0 > (st.timeout or 60000) then
		B.S.timedOut = true
		finishStep()
	end
	return false
end

EEex_Menu_AddMainFileLoadedListener(function() EEex_Menu_LoadFile("PTEEBAT") end)

-- the engine refuses to save with enemies around: the test removes the hostile creatures (EA >= 200) of the area
function PSTEE_BAT_ClearHostiles()
	local area, x, y = workArea()
	local n = 0
	if not area then return 0 end
	for _, obj in ipairs(EEex_Area_GetAllOfTypeStringInRange(area, x, y, "[ANYONE]", 0x7FFF, false, false)) do
		if EEex_GameObject_IsSprite(obj, false) and obj.m_typeAI.m_EnemyAlly >= 200 and EEex_Sprite_GetPortraitIndex(obj) == -1 then
			q(obj, "DestroySelf()")
			n = n + 1
		end
	end
	return n
end

-- F3: prepare a base save: the companions the battery adds (COMPANIONS) leave the party and the area, hostiles go
EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F3") or B.running then return end
	unpause()
	local names = {}
	for _, c in ipairs(COMPANIONS) do names[c] = true end
	local n = 0
	for _, c in ipairs(COMPANIONS) do
		for _, s in ipairs(findAll(c)) do
			if EEex_Sprite_GetPortraitIndex(s) ~= -1 then q(s, "LeaveParty()") end
			q(s, "DestroySelf()")
			n = n + 1
		end
	end
	log("BASE", n .. " companions removed, " .. PSTEE_BAT_ClearHostiles() .. " hostiles removed")
end)

-- F4: quick save again (the engine refuses it while enemies are around; tools/battery.py retries until one is written)
EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F4") or B.running then return end
	unpause()
	log("SAVE", "quick save (" .. PSTEE_BAT_ClearHostiles() .. " hostiles removed)")
	worldScreen:OnQuickSaveButtonClick(false)
end)

-- F5: scripted RestParty() (vanilla Torment hang, fixed in EEex_Fix_Patch.lua): logs HP before, then after 20 s
EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F5") or B.running then return end
	local hps = {}
	for _, s in ipairs(party()) do table.insert(hps, EEex_Sprite_GetName(s) .. " " .. hp(s)) end
	log("RESTPARTY", "before: " .. table.concat(hps, ", "))
	unpause()
	q(tno(), "RestParty()")
end)

-- F6: load the save named in EEex_scripts/PSTEE_BatteryLoad.lua (written by tools/battery.py)
EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F6") or B.running then return end
	PSTEE_BAT_LOAD = nil
	EEex_DoFile("PSTEE_BatteryLoad")
	if PSTEE_BAT_LOAD then
		log("LOAD", PSTEE_BAT_LOAD)
		-- from the main menu, the load screen has to be the active engine first
		if e:GetActiveEngine() == startEngine then startEngine:OnLoadGameButtonClick() end
		loadScreen:LoadGame(PSTEE_BAT_LOAD)
	end
end)

-- F9: full run (or resume), F8: reduced run (combat-spawn + op326), F7: companions + damage, no rest (rest by hand)
EEex_Key_AddPressedListener(function(key)
	local full, reduced, prep = key == EEex_Key_GetFromName("F9"), key == EEex_Key_GetFromName("F8"), key == EEex_Key_GetFromName("F7")
	reduced = reduced or prep
	if not (full or reduced) or B.running then return end
	B.noRest = prep
	if worldScreen ~= e:GetActiveEngine() then return end
	if reduced or B.stepIndex == nil or B.stepIndex > #STEPS then
		B.results, B.pass, B.fail, B.flags = {}, 0, 0, {}
		B.stepIndex = 1
		B.only = reduced and (prep and { ["companions"] = true, ["rest"] = true } or { ["combat-spawn"] = true, ["op326"] = true }) or nil
		log("START", reduced and ("reduced run: " .. (prep and "companions + rest prep" or "combat-spawn + op326")) or (#STEPS .. " steps"))
	else
		log("RESUME", "step " .. B.stepIndex .. " " .. STEPS[B.stepIndex].name)
	end
	B.running = true
	Infinity_PushMenu("PSTEE_Battery_Menu")
	startStep()
end)
