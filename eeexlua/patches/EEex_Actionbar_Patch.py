# EEex_Actionbar_Patch.lua: CInfButtonArray::SetState (PT 0x2c8a20), UpdateButtons, OnLButtonPressed.
# Reviewed without a change: UpdateButtons()-LastCall (PT 0x2cd8cf, __security_check_cookie at the epilogue; no PT
# caller of UpdateButtons reads its return value, so clobbering rax is harmless as in BG), IsPartyLeader()-Override
# (PT 0x12853a, identical code: rbx = movsxd of the leader id, rax = CObList::Find result), OnKeyDown()-
# ThievingHotkeyPressSpecialAbilitiesCall (PT 0x35d090, rcx = rbx = &m_cButtonArray, rdx = button index, same as BG;
# after the call PT reloads edx / rcx).
PATCHES = [
    # SetState: Torment keeps the state argument in edi (PT 0x2c8a40 mov edi, edx; edi is untouched up to the
    # SaveArg call at PT 0x2c8a5c). [rsp+0x70] is the rcx home slot of Torment's frame too (4 pushes + sub 0x48 +
    # return address = 0x70) and nothing in PT SetState reads or writes it.
    ('''		mov dword ptr ds:[rsp+70h], r15d ; store it in unused spill space''',
     '''		mov dword ptr ds:[rsp+70h], edi ; store it in unused spill space ; EEex-PTEE: Torment keeps the state in edi'''),
    # Torment's switch covers states 1..121 (PT 0x2c8ab5 lea eax, [rdi-1]; cmp eax, 0x78; ja). The byte table
    # (Data-CInfButtonArray::SetState()-IndirectJumpTable, PT 0x2ca438) gives configs 0..30 for the same states as
    # BG, 31..37 for the Torment-only states 115..121, and 38 (BG 31) as the default case.
    ('''				cmp eax, 71h''',
     '''				cmp eax, 78h ; EEex-PTEE: Torment's SetState switch has 121 states (PT 0x2c8ab8)'''),
    # UpdateButtons call (PT 0x2ca37f): `this` is in rbx (PT 0x2ca37c mov rcx, rbx; BG r14)
    ('''				call_error:
				#DESTROY_SHADOW_SPACE
				mov rcx, r14''',
     '''				call_error:
				#DESTROY_SHADOW_SPACE
				mov rcx, rbx ; EEex-PTEE: Torment keeps `this` in rbx (PT 0x2ca37c)'''),
    # OnLButtonPressed()-HasFullThieving (PT 0x2c6e1e): same 11 bytes (mov rcx, [rax+0x10c8] 7 / je 2 / mov dl, 0x24
    # 2), only the relocatable 7-byte mov is restored, the call (PT 0x2c6e29, CInfGame::SetTempCursor(rcx, dl) like BG)
    # is the return address. The sprite is at [rsp+0x40] (PT 0x2c6dfc / 0x2c6e3c mov rcx, [rsp+0x40]; BG [rsp+0x48]).
    ('''						mov rax, qword ptr ss:[rsp+#LAST_FRAME_TOP(48h)]''',
     '''						mov rax, qword ptr ss:[rsp+#LAST_FRAME_TOP(40h)] ; EEex-PTEE: Torment's sprite slot (PT 0x2c6dfc)'''),
    # CAIGroup::IsPartyLeader()-Override (PT 0x12853a, code identical to BG 0x11ac1a): rbx is the leader's object id
    # (PT 0x128500 movsxd rbx, [rax+0x10] = data of m_memberList's head node, the long id also passed to
    # GetCharacterPortraitNum / CObList::Find), not a CGameSprite*. Upstream pushes it as a CGameSprite (bug in BG
    # too): EEex_Actionbar_Hook_IsPartyLeader -> sprite:getClass() would read memory at the id. Resolve the id with
    # CGameObjectArray::GetShare (ecx = id, rdx = &out, as PT 0x2c6a37..0x2c6a42 calls it) and keep the pointer in
    # rbx: IsPartyLeader only pops rbx after the site (PT 0x12853f..0x128555). Unresolved id -> false (engine result).
    ('''	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CAIGroup::IsPartyLeader()-Override"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},''',
     '''	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CAIGroup::IsPartyLeader()-Override"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RBX}}}, -- EEex-PTEE: rbx'''),
    ('''			{[[
				test rax, rax
				jnz #L(return)

				#MAKE_SHADOW_SPACE(40)
			]]},''',
     '''			{[[
				test rax, rax
				jnz #L(return)

				#MAKE_SHADOW_SPACE(40)

				; EEex-PTEE: rbx is the leader's object id (PT 0x128500), resolve it to the sprite
				mov ecx, ebx
				lea rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
				mov qword ptr ss:[rdx], 0
				call #L(CGameObjectArray::GetShare)
				mov rbx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)] ; rbx is only popped after the site
				test rbx, rbx
				jz call_error
			]]},'''),
]
