-- EEex-PSTEE dev helper (not shipped): F11 applies 6 timed spells (SPWI103/115/120/205/504, SPPR201) to every party member and
-- applies op146 (param2 0, special 2: EEex SpellNoDec bit in Torment) casting SPWI216 to the protagonist, so B3EffMen (effect list) and B3Timer (cast / effect bars) have something
-- to show. Test save only.
-- F11 (registered first, runs first): dump the protagonist's timed effects with the fields B3EffMen filters on
PSTEE_SpellTest_Dump = function()
	local sprite = EEex_Sprite_GetInPortrait(0)
	if not sprite then return end
	local n = 0
	EEex_Utility_IterateCPtrList(sprite.m_timedEffectList, function(effect)
		n = n + 1
		local ok, err = pcall(function()
			local res = effect.m_sourceRes:get()
			local line = string.format("PSTEE-EFFECTS: #%d op %d sourceType %d sourceRes '%s' durationType %d duration %d casterLevel %d",
				n, effect.m_effectId, effect.m_sourceType, res, effect.m_durationType, effect.m_duration, effect.m_casterLevel)
			if res ~= "" then
				local header = EEex_Resource_Demand(res, "SPL")
				if header then
					local ability = header:getAbilityForLevel(math.max(effect.m_casterLevel, 1)) or header:getAbility(0)
					line = line .. string.format(" name %d icon '%s'", header.genericName, ability and ability.quickSlotIcon:get() or "?")
				else
					line = line .. " (no SPL)"
				end
			end
			print(line)
		end)
		if not ok then print("PSTEE-EFFECTS: #" .. n .. " error " .. tostring(err)) end
	end)
	print("PSTEE-EFFECTS: " .. n .. " timed effects on " .. sprite:getName())
end


EEex_Key_AddPressedListener(function(key)
	if key ~= EEex_Key_GetFromName("F11") then return end
	PSTEE_SpellTest_Dump()
	for i = 0, 5 do
		local sprite = EEex_Sprite_GetInPortrait(i)
		if sprite then
			for _, res in ipairs({"SPWI103", "SPWI115", "SPWI120", "SPWI205", "SPWI504", "SPPR201"}) do
				EEex_Action_QueueResponseStringOnAIBase('ApplySpellRES("' .. res .. '",Myself)', sprite)
			end
			print("PSTEE-SPELLTEST: applied 6 timed spells to " .. sprite:getName())
		end
	end
	local leader = EEex_Sprite_GetInPortrait(0)
	if leader then
		-- op146 test: param2 0 + special 2 (EEex-PSTEE bit) must queue SpellNoDec (191) instead of ForceSpell;
		-- current / queued action ids are printed by the next F11
		print("PSTEE-SPELLTEST: current action " .. leader.m_curAction.m_actionID)
		EEex_Utility_IterateCPtrList(leader.m_queuedActions, function(action)
			print("PSTEE-SPELLTEST: queued action " .. action.m_actionID)
		end)
		EEex_GameObject_ApplyEffect(leader, {
			["effectID"] = 146, ["res"] = "SPWI216", ["dwFlags"] = 0, ["special"] = 2, ["sourceID"] = leader.m_id,
		})
		print("PSTEE-SPELLTEST: op146 special 2 (SPWI216) applied to " .. leader:getName())
	end
end)

-- every action a party member starts (action id; 191 = SpellNoDec from the op146 special 2 test)
EEex_Action_AddSpriteStartedActionListener(function(sprite, action)
	if sprite.m_typeAI.m_EnemyAlly == 2 then
		print(string.format("PSTEE-SPELLTEST: %s starts action %d", sprite:getName(), action.m_actionID))
	end
end)
