-- EEex-PTEE dev test battery (not shipped): EEex features for modders, run on the protagonist in the test save.
-- F10 once: run the tests (immediate checks print PASS / FAIL, deferred ones are started);
-- F10 again (game unpaused in between): check the deferred results.
-- Needs the dev overrides deployed by eeexlua/build.py: STATS.IDS 1000 PTEE_TEST_STAT, X-STATS.2DA default 7.
-- Script strings parsed at runtime (ParseConditionalString / ParseResponseString) lose spaces and most punctuation,
-- in BG2EE too (identical parser code): the chunks below avoid them; compiled BCS keep their strings intact.

local results = { pass = 0, fail = 0 }
local function check(name, ok, detail)
	if ok then results.pass = results.pass + 1 else results.fail = results.fail + 1 end
	print(string.format("PTEE-FEATURE: %s %s%s", ok and "PASS" or "FAIL", name, detail and (" (" .. tostring(detail) .. ")") or ""))
end
local function try(name, func)
	local ok, err = pcall(func)
	if not ok then check(name, false, "error: " .. tostring(err)) end
end

PTEE_FT_State = PTEE_FT_State or { stage = 0 }

-- EEex_LuaAction / EEex_MatchObject chunks (no spaces / operators in runtime-parsed strings)
function PTEEFTA() PTEE_FT_State.luaAction = EEex_LuaAction_Object.m_id end
function PTEEFTM() return true end

-- op403 screen: block op12 (damage), record calls
function PTEESCR(op403, effect, sprite)
	PTEE_FT_State.op403calls = (PTEE_FT_State.op403calls or 0) + 1
	return effect.m_effectId == 12
end
-- op408 projectile mutator table
PTEEPM = { ["typeMutator"] = function(context) PTEE_FT_State.op408 = tostring(context.decodeSource) end }
-- op409 enabled action listener
EEex_Action_AddEnabledSpriteStartedActionListener("PTEEFTL", function(sprite, action, op409)
	PTEE_FT_State.op409 = action.m_actionID
end)

-- op402 target (InvokeLua: global function, name of 8 uppercase characters or less)
function PTEEFT(effect, sprite)
	PTEE_FT_State.op402 = sprite.m_id
end

local function stage1()
	local tno = EEex_Sprite_GetInPortrait(0)
	local morte = EEex_Sprite_GetInPortrait(1)
	if not tno then print("PTEE-FEATURE: no protagonist") return end

	-- Triggers (EEex ids 0x4112..0x4115 in Torment)
	try("trigger EEex_LuaTrigger true", function()
		check("trigger EEex_LuaTrigger true", EEex_Trigger_EvalConditionalStringAsAIBase('EEex_LuaTrigger("return(true)")', tno) == true)
	end)
	try("trigger EEex_LuaTrigger false", function()
		check("trigger EEex_LuaTrigger false", EEex_Trigger_EvalConditionalStringAsAIBase('EEex_LuaTrigger("return(false)")', tno) == false)
	end)
	try("trigger EEex_IsImmuneToOpcode", function()
		check("trigger EEex_IsImmuneToOpcode(Myself,12) false", EEex_Trigger_EvalConditionalStringAsAIBase('EEex_IsImmuneToOpcode(Myself,12)', tno) == false)
	end)
	try("trigger EEex_HasDispellableEffect", function()
		local r = EEex_Trigger_EvalConditionalStringAsAIBase('EEex_HasDispellableEffect(Myself)', tno)
		check("trigger EEex_HasDispellableEffect (no crash)", r == true or r == false, r)
	end)
	try("trigger EEex_MatchObject", function()
		local r = EEex_Trigger_EvalConditionalStringAsAIBase('EEex_MatchObject("return(PTEEFTM())")', tno)
		check("trigger EEex_MatchObject (match)", r == true, r)
	end)
	-- Vanilla trigger next to EEex's: Torment's own LastPersonTalkedTo (0x4110) must still be a vanilla trigger
	try("trigger vanilla True()", function()
		check("trigger vanilla True()", EEex_Trigger_EvalConditionalStringAsAIBase('True()', tno) == true)
	end)

	-- Objects (115 EEex_LuaObject)
	try("object EEex_LuaObject", function()
		EEex_LuaObject = morte or tno
		local found = EEex_Object_EvalStringAsAIBase("EEex_LuaObject", tno)
		check("object EEex_LuaObject", found ~= nil and found.m_id == EEex_LuaObject.m_id, found and found:getName())
	end)
	try("object Myself (GetShare 3 args)", function()
		local found = EEex_Object_EvalStringAsAIBase("Myself", tno)
		check("object Myself (GetShare 3 args)", found ~= nil and found.m_id == tno.m_id)
	end)

	-- Extended stats (dev X-STATS: PTEE_TEST_STAT 1000, default 7)
	try("extended stat default", function()
		check("extended stat 1000 default 7", EEex.GetExtendedStatValue(tno, 1000) == 7, EEex.GetExtendedStatValue(tno, 1000))
	end)
	-- op401 SetExtendedStat: set 42 for 60 s
	try("op401 apply", function()
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 401, ["effectAmount"] = 42, ["dwFlags"] = 1, ["special"] = 1000,
			["durationType"] = 0, ["duration"] = 60, ["sourceID"] = tno.m_id })
	end)
	-- op402 InvokeLua (immediate resolve)
	try("op402", function()
		PTEE_FT_State.op402 = nil
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 402, ["res"] = "PTEEFT", ["sourceID"] = tno.m_id })
		check("op402 InvokeLua", PTEE_FT_State.op402 == tno.m_id)
	end)

	-- op403 ScreenEffects: damage blocked
	try("op403", function()
		PTEE_FT_State.op403calls = 0
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 403, ["res"] = "PTEESCR", ["durationType"] = 0, ["duration"] = 60, ["sourceID"] = tno.m_id })
		local hp = tno.m_baseStats.m_hitPoints
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 12, ["effectAmount"] = 1, ["sourceID"] = tno.m_id })
		check("op403 ScreenEffects blocks damage", tno.m_baseStats.m_hitPoints == hp and PTEE_FT_State.op403calls > 0,
			string.format("hp %d -> %d, calls %d", hp, tno.m_baseStats.m_hitPoints, PTEE_FT_State.op403calls))
	end)
	-- op400 SetTemporaryAIScript: override script (param2 0) = 0000DEF for 1 s (a running override script would
	-- interrupt the deferred cast below)
	PTEE_FT_SKIP_OP400 = false -- was skipped while bisecting the CGameEffect size bug
	if not PTEE_FT_SKIP_OP400 then try("op400", function()
		local before = tno.m_overrideScript and tno.m_overrideScript.cResRef:get() or "(none)"
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 400, ["dwFlags"] = 0, ["res"] = "0000DEF", ["durationType"] = 0, ["duration"] = 1, ["sourceID"] = tno.m_id })
		local after = tno.m_overrideScript and tno.m_overrideScript.cResRef:get() or "(none)"
		check("op400 SetTemporaryAIScript", after == "0000DEF", before .. " -> " .. after)
	end) end
	-- op408 ProjectileMutator and op409 EnableActionListener (deferred: the next cast / action)
	try("op408/409 apply", function()
		PTEE_FT_State.op408, PTEE_FT_State.op409 = nil, nil
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 408, ["res"] = "PTEEPM", ["durationType"] = 0, ["duration"] = 60, ["sourceID"] = tno.m_id })
		EEex_GameObject_ApplyEffect(tno, { ["effectID"] = 409, ["effectAmount"] = 1, ["res"] = "PTEEFTL", ["durationType"] = 0, ["duration"] = 60, ["sourceID"] = tno.m_id })
		EEex_Action_QueueResponseStringOnAIBase('ForceSpellRES("SPWI118",Player2)', tno) -- projectile spell
	end)

	-- DecodeProjectile direct call: must reach EEex's decode hooks (global mutator PTEEGM logs it)
	try("DecodeProjectile direct", function()
		PTEE_FT_State.gmDecode = nil
		local projectile = CProjectile.DecodeProjectile(2, tno, 1)
		check("DecodeProjectile direct reaches the decode hook", PTEE_FT_State.gmDecode ~= nil and projectile ~= nil,
			tostring(PTEE_FT_State.gmDecode) .. " " .. tostring(projectile))
	end)

	-- Actions (472 EEex_LuaAction, deferred)
	try("action EEex_LuaAction queue", function()
		PTEE_FT_State.luaAction = nil
		EEex_Action_QueueResponseStringOnAIBase('EEex_LuaAction("PTEEFTA()")', tno)
	end)
	-- Script helpers with the Torment constructor (CAIScript, player-script flag)
	try("EEex_Resource_LoadScript", function()
		local script = EEex_Resource_LoadScript("NONE", true)
		check("EEex_Resource_LoadScript (player flag)", script ~= nil)
	end)

	PTEE_FT_State.stage = 1
	print(string.format("PTEE-FEATURE: stage 1 done, %d pass / %d fail; unpause, then F10 again", results.pass, results.fail))
end

local function stage2()
	local tno = EEex_Sprite_GetInPortrait(0)
	try("action EEex_LuaAction ran", function()
		check("action EEex_LuaAction ran", PTEE_FT_State.luaAction == tno.m_id, PTEE_FT_State.luaAction)
	end)
	try("op401 result", function()
		check("op401 SetExtendedStat 42", EEex.GetExtendedStatValue(tno, 1000) == 42, EEex.GetExtendedStatValue(tno, 1000))
	end)
	try("op408 result", function()
		check("op408 ProjectileMutator typeMutator called", PTEE_FT_State.op408 ~= nil, PTEE_FT_State.op408)
	end)
	try("op409 result", function()
		check("op409 EnableActionListener called", PTEE_FT_State.op409 ~= nil, PTEE_FT_State.op409)
	end)
	PTEE_FT_State.stage = 0
	print(string.format("PTEE-FEATURE: stage 2 done, %d pass / %d fail", results.pass, results.fail))
end

EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F10") then return end
	results.pass, results.fail = 0, 0
	if PTEE_FT_State.stage == 0 then stage1() else stage2() end
end)

-- op408 diagnosis: a global mutator logs every projectile decode (source, type) and every AddEffect
PTEEGM = {
	["typeMutator"] = function(context)
		PTEE_FT_State.gmDecode = context.projectileType
		print(string.format("PTEE-FEATURE: decode source %s type %s sprite %s", tostring(context.decodeSource),
			tostring(context.projectileType), context.originatingSprite and context.originatingSprite:getName() or "nil"))
	end,
	["projectileMutator"] = function(context)
		print("PTEE-FEATURE: decoded projectile " .. tostring(context.projectile))
	end,
}
EEex_Projectile_RegisterGlobalMutator("PTEEGM")
