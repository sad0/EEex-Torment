# EEex_Sprite_Patch.lua: Torment register allocation / code layout at the hook sites (tools/hookreview.py).
# Reviewed hooks without a change: Destruct (rbx), CheckQuickLists (5 relocatable push bytes), Marshal (r13),
# Unmarshal (rbx), Marshal OverrideSize / WriteExtra (rbx / rax), Unmarshal JIT (EEex.dll), CHECK_MODE (rcx),
# ConcentrationFailed (same prologue), GetMax/MinDamage (r13 = item), GetProfBonuses (same stack arguments),
# MeleeingWithRangedPenalty (same 7-byte movsx, Torment's constant is -8 too), UUID Copy/Marshal hooks (rax/rcx
# scratch only), FormatRollCall (r8 = roll), Swing Damage-1/2 (call CGameSprite::Damage, same arguments).
PATCHES = [
    # CGameSprite::SetCursor: Torment's SetCharacterToolTip(this, CString* out) returns the text that the next call
    # shows (PT 0x3e69b2 -> 0x3e69d1). Skipping only the call would show an uninitialized string: suppress through
    # Torment's own no-tooltip path instead (empty string, id 0, PT 0x3e69bb = site + 9).
    ('''	EEex_HookBeforeCallWithLabels(EEex_Label("Hook-CGameSprite::SetCursor()-SetCharacterToolTip()"), {
		{"hook_integrity_watchdog_ignore_registers", {''',
     '''	EEex_HookBeforeCallWithLabels(EEex_Label("Hook-CGameSprite::SetCursor()-SetCharacterToolTip()"), {
		{"ptee_no_tooltip", EEex_Label("Hook-CGameSprite::SetCursor()-SetCharacterToolTip()") + 9},
		{"hook_integrity_watchdog_ignore_registers", {'''),
    ('''				#DESTROY_SHADOW_SPACE
				test rax, rax
				jnz #L(return_skip)''',
     '''				#DESTROY_SHADOW_SPACE
				test rax, rax
				jnz #L(ptee_no_tooltip) ; EEex-PTEE: Torment's no-tooltip path'''),
    # CGameSprite constructors: the sprite is in rbx (Construct1, PT 0x3b2ae8) / rdi (Construct2, PT 0x3b09f6)
    ('''	for _, labelName in ipairs({
		"Hook-CGameSprite::Construct1()-FirstCall",
		"Hook-CGameSprite::Construct2()-FirstCall"
	}) do
		EEex_HookAfterCallWithLabels(EEex_Label(labelName), {
			{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
			{[[
				mov rcx, rsi ; pSprite
				call #L(EEex::Sprite_Hook_OnConstruct)
			]]}
		)
	end''',
     '''	for _, labelEntry in ipairs({
		{"Hook-CGameSprite::Construct1()-FirstCall", "rbx"}, -- EEex-PTEE: Torment keeps the sprite in rbx
		{"Hook-CGameSprite::Construct2()-FirstCall", "rdi"}, -- EEex-PTEE: Torment keeps the sprite in rdi
	}) do
		EEex_HookAfterCallWithLabels(EEex_Label(labelEntry[1]), {
			{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
			{[[
				mov rcx, ]], labelEntry[2], [[ ; pSprite
				call #L(EEex::Sprite_Hook_OnConstruct)
			]]}
		)
	end'''),
    # CGameSprite::Rest: the sprite is in rdi (PT 0x429971 mov [rdi+0x4b4c], eax)
    ('''			EEex_GenLuaCall("EEex_Sprite_Hook_OnResetQuickListCounts", {
				["args"] = {
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r15 #ENDL", {rspOffset}}, "CGameSprite" end,''',
     '''			EEex_GenLuaCall("EEex_Sprite_Hook_OnResetQuickListCounts", {
				["args"] = {
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], rdi #ENDL", {rspOffset}}, "CGameSprite" end, -- EEex-PTEE: rdi'''),
    # CGameEffectDamage::ApplyEffect (PT 0x1c7e50): effect in r15 (BG r14), source sprite at [rbp-0x70] (BG
    # [rbp-0x41]), target in rbx; none of them changes before the common exit (OnDone, PT 0x1c9c41)
    ('@all:2 ' + '''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r14 #ENDL", {rspOffset}}, "CGameEffect" end,
					function(rspOffset) return {[[
						mov rax, qword ptr ss:[rbp-0x41]''',
     '''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r15 #ENDL", {rspOffset}}, "CGameEffect" end, -- EEex-PTEE: r15
					function(rspOffset) return {[[
						mov rax, qword ptr ss:[rbp-0x70] ; EEex-PTEE: source sprite slot'''),
    # CGameSprite::SetCurrAction: the sprite is in rbx (PT 0x42b7ff lea rcx, [rbx+0x3f0])
    ('''			EEex_GenLuaCall("EEex_Sprite_Hook_OnSetCurrAction", {
				["args"] = {
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], rdi #ENDL", {rspOffset}}, "CGameSprite" end,''',
     '''			EEex_GenLuaCall("EEex_Sprite_Hook_OnSetCurrAction", {
				["args"] = {
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], rbx #ENDL", {rspOffset}}, "CGameSprite" end, -- EEex-PTEE: rbx'''),
    # GetProfBonuses callers: the item is the argument of the preceding CItem call (mov rcx, <item>)
    ('''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::CheckCombatStats()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], rbx ]]''',
     '''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::CheckCombatStats()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], r15 ]]'''),  # PT 0x3bcd0e mov rcx, r15
    ('''	EEex_HookBeforeCall(EEex_Label("Hook-CGameSprite::GetStatBreakdown()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], r14 ]]''',
     '''	EEex_HookBeforeCall(EEex_Label("Hook-CGameSprite::GetStatBreakdown()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], rsi ]]'''),  # PT 0x3ce922 mov rcx, rsi
    ('''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::GetActiveWeaponStyleAndLevel()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], rdi ]]''',
     '''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::GetActiveWeaponStyleAndLevel()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], r15 ]]'''),  # PT 0x412fd9 mov rcx, r15
    ('''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::EquipMostDamagingMelee()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], rdi ]]''',
     '''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::EquipMostDamagingMelee()-GetProfBonuses-SaveItem"), {[[
		mov qword ptr ds:[#$(1)], rsi ]]'''),  # PT 0x408e6f mov rcx, rsi
    # CGameSprite::Hit (PT 0x4147f7): the item argument (r8) is kept at [rbp-0x39], the ability number (r9d) in r13
    ('''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::Hit()-FirstCall"), {[[
		mov qword ptr ds:[#$(1)], r15 ]], {CGameSprite_Hit_SavedItem}, [[ #ENDL
		mov qword ptr ds:[#$(1)], rsi ]], {CGameSprite_Hit_SavedItemAbilityNum}''',
     '''	EEex_HookAfterCall(EEex_Label("Hook-CGameSprite::Hit()-FirstCall"), {[[
		mov rax, qword ptr ss:[rbp-0x39] ; EEex-PTEE: item slot
		mov qword ptr ds:[#$(1)], rax ]], {CGameSprite_Hit_SavedItem}, [[ #ENDL
		mov qword ptr ds:[#$(1)], r13 ]], {CGameSprite_Hit_SavedItemAbilityNum}'''),
]
