# EEex_Mix_Patch.lua: CGameSprite::Swing (PT 0x4334e0) CImmunitiesWeapon::OnList hooks.
# Torment frame (BG -> PT, from the shared loads / Hit() arguments): weapon item [rsp+0x58] -> [rbp-0x68]
# (PT 0x433766), ability [rsp+0x68] -> [rbp-0x70] (PT 0x4337dd, the pointer tested for type 2 at PT 0x433ddc), launcher
# item [rsp+0x70] -> [rbp-0x60] (PT 0x433810), attacker rbx, target r15 (PT 0x4336a9), r13 = target + 0xC (PT 0x43383f).
# - Melee (PT 0x434296): Torment passes the weapon to Hit() straight from [rbp-0x68] (PT 0x434215, BG r12): read the
#   frame slots. Same jne polarity after the call (PT 0x43429d, immune -> PT 0x434c0f).
# - Ranged: Torment duplicates BG's block. BG decodes the missing projectile then jumps back (BG 0x3b90f0); Torment has
#   a second copy of the Hit() / OnList() / feedback code after the decode: OnList at PT 0x433eb2 (label, projectile
#   already loaded) and PT 0x433fb8 (= label + 0x106, after DecodeProjectile PT 0x433f43). Both are hooked. Weapon in
#   r12 (PT 0x433e6f / 0x433f75 mov r12, [rbp-0x68]; BG rdi). The two immune blocks end with mov rdi, [rbp-0x60] /
#   jmp PT 0x4340bc (NoCImmunitiesWeaponElseContinue label: mov r8, rdi / mov rdx, r12), so the skip boilerplate
#   is mov rdi, [rbp-0x60] (BG mov rsi, [rsp+0x70]; r13 is already target + 0xC in Torment).
PATCHES = [
    # Melee: weapon / ability from Torment's frame slots
    ('''				mov rcx, rbx                                    ; attackingSprite
				mov rdx, r15                                    ; targetSprite
				mov r8, r12                                     ; weapon
				mov r9, qword ptr ds:[rsp+#LAST_FRAME_TOP(68h)] ; weaponAbility''',
     '''				mov rcx, rbx                                    ; attackingSprite
				mov rdx, r15                                    ; targetSprite
				mov r8, qword ptr ss:[rbp-0x68]                 ; weapon        ; EEex-PTEE: PT 0x434215
				mov r9, qword ptr ss:[rbp-0x70]                 ; weaponAbility ; EEex-PTEE: PT 0x4337dd'''),
    # Ranged: both Torment OnList() sites
    ('''	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CGameSprite::Swing()-CImmunitiesWeapon::OnList()-Ranged"), {''',
     '''	-- EEex-PTEE: Torment has two copies of the ranged OnList() block (PT 0x433eb2 and 0x433fb8 = label + 0x106)
	local ptRangedOnList = EEex_Label("Hook-CGameSprite::Swing()-CImmunitiesWeapon::OnList()-Ranged")
	local ptRangedOnList2 = ptRangedOnList + 0x106
	if EEex_ReadU8(ptRangedOnList2) ~= 0xE8
		or ptRangedOnList2 + 5 + EEex_Read32(ptRangedOnList2 + 1) ~= ptRangedOnList + 5 + EEex_Read32(ptRangedOnList + 1)
	then
		EEex_Error("[EEex-PTEE] Unexpected second CGameSprite::Swing() ranged OnList() call")
	end
	for _, ptRangedOnListSite in ipairs({ptRangedOnList, ptRangedOnList2}) do
	EEex_HookAfterCallWithLabels(ptRangedOnListSite, {'''),
    ('''				mov rcx, rbx                                    ; attackingSprite
				mov rdx, r15                                    ; targetSprite
				mov r8, rdi                                     ; weapon
				mov r9, qword ptr ds:[rsp+#LAST_FRAME_TOP(68h)] ; weaponAbility''',
     '''				mov rcx, rbx                                    ; attackingSprite
				mov rdx, r15                                    ; targetSprite
				mov r8, r12                                     ; weapon        ; EEex-PTEE: PT 0x433e6f / 0x433f75
				mov r9, qword ptr ss:[rbp-0x70]                 ; weaponAbility ; EEex-PTEE: PT 0x4337dd'''),
    ('''				#MANUAL_HOOK_EXIT(0)
				; The consequence of not running the else block is that this boilerplate is not executed
				mov rsi, qword ptr ss:[rsp+0x70]
				lea r13, qword ptr ds:[r15+0xC]
				jmp #L(Hook-CGameSprite::Swing()-NoCImmunitiesWeaponElseContinue)
			]]},
		})
	)''',
     '''				#MANUAL_HOOK_EXIT(0)
				; The consequence of not running the else block is that this boilerplate is not executed
				mov rdi, qword ptr ss:[rbp-0x60] ; EEex-PTEE: PT 0x433f28 / 0x43402a (r13 is already target + 0xC)
				jmp #L(Hook-CGameSprite::Swing()-NoCImmunitiesWeaponElseContinue)
			]]},
		})
	)
	end -- EEex-PTEE: both ranged sites'''),
]
