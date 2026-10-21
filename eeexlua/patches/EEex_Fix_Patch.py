# EEex_Fix_Patch.lua: Torment register allocation / code layout at the hook sites (tools/hookreview.py, notes in
# eeexlua/notes/EEex_Fix_Patch.md).
# Reviewed hooks without a change: TRAPLIMT snare jle (PT 0x1e3809, same short 0x7E), AddSpecialAbility LastCall
# (rsi = sprite, CSpell at [rsp+0x48], same frame), Spell/SpellPoint ApplyCastingEffect (rbx = sprite), op182
# CheckRetVal (PT FindItemPersonal returns -1 too, same 6-byte je), ProcessEffectList FirstRandCall/AfterRandCalls
# (identical skipped block: rsi = sprite, [rsi+0x48], edi = r12d), the FoW-cap overrides and CVisibilityMap::Construct
# (identical prologues, as bindings/test/PTEE_VisMapTest.lua), SynchronousUpdate / uiEventMenuStack / bsearchrange
# JITs, uiKillCapture (6 relocatable bytes: push rbx; sub rsp,0x20), CScreenMap vtable slot 28 (PT 0x33b770),
# op135 FormToForm jne (PT 0x1d95b5, short, [rbx+0x1088] = m_bPolymorphed, esi 0 / edi 1).
PATCHES = [
    # WSPECIAL SPEED: CheckCombatStatsWeapon keeps the sprite in rbx in Torment (PT 0x3bd01b mov rbx, rcx;
    # 0x3bd36e movzx edi, word ptr [rbx+0x794] right after the hooked CString::Format call). r12w (proficiency level,
    # PT 0x3bd281 movsx edi, r12w) and [rbp+0x50] (bOffHand, r8d home slot, PT 0x3bcff5 / 0x3bd0a7) are unchanged.
    # EEex.dll's Fix_Hook_ImplementWSPECIALSpeedColumn is empty on Torment (WSPECIAL.2DA has no SPEED column).
    ('''			mov rcx, r14                     ; pSprite''',
     '''			mov rcx, rbx                     ; pSprite ; EEex-PTEE: Torment keeps the sprite in rbx'''),

    # op33 ImmediateSaveWriteOffset: label unsupported in Torment (PATTERNS.md): Torment's op33 is a different
    # implementation without BG v2.5+'s wrong `sub [rdi+1136h]` write, so the bug does not exist. Skip the fix.
    ('''	EEex_WriteU32(
		EEex_Label("Hook-CGameEffectSaveVsDeath::ApplyEffect()-ImmediateSaveWriteOffset"),
		EEex_OffsetOf("CGameSprite.m_derivedStats.m_nSaveVSDeath")
	)''',
     '''	-- EEex-PTEE: label absent in Torment (op33 has no wrong SAVEVSWANDS write there): fix skipped
	if EEex_TryLabel("Hook-CGameEffectSaveVsDeath::ApplyEffect()-ImmediateSaveWriteOffset") then
	EEex_WriteU32(
		EEex_Label("Hook-CGameEffectSaveVsDeath::ApplyEffect()-ImmediateSaveWriteOffset"),
		EEex_OffsetOf("CGameSprite.m_derivedStats.m_nSaveVSDeath")
	)
	end -- EEex-PTEE'''),

    # op206/318/324 item indexing: label unsupported in Torment. Torment's CGameEffect::CheckAdd (PT 0x1eba60) has no
    # strref test / item-list indexing after the immunity lookup (PT 0x1ebfd9 call 0x21bd30 -> 0x1ebfef uses the
    # immunity strref [rbx+8] directly), so the bug does not exist. Skip the hook.
    ('''	EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CGameEffect::CheckAdd()-FixSpellImmunityShouldSkipItemIndexing"), 4, {''',
     '''	-- EEex-PTEE: label absent in Torment (CheckAdd never indexes the source's item list): fix skipped
	if EEex_TryLabel("Hook-CGameEffect::CheckAdd()-FixSpellImmunityShouldSkipItemIndexing") then
	EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CGameEffect::CheckAdd()-FixSpellImmunityShouldSkipItemIndexing"), 4, {'''),
    ('''			call #L(EEex::Fix_Hook_SpellImmunityShouldSkipItemIndexing)
			test al, al
			jnz #L(jmp_success)
		]]}
	)''',
     '''			call #L(EEex::Fix_Hook_SpellImmunityShouldSkipItemIndexing)
			test al, al
			jnz #L(jmp_success)
		]]}
	)
	end -- EEex-PTEE'''),

    # Spell() direction check: the CPoint* is not kept in a register in Torment (BG r14 = r15+0xC; PT 0x42c44c
    # lea rax, [r15+0xC] / mov [rbp-0x40], rax, and rax is the GetDirection result at the hook). r15 (target) is
    # still live (restored `cmp r15, rbx`, PT 0x42c464): rebuild it. rbx = sprite. Restore: same 3-byte cmp.
    ('''			mov rdx, r14                                                  ; point''',
     '''			lea rdx, qword ptr ds:[r15+0xC]                               ; point ; EEex-PTEE: PT 0x42c44c'''),

    # SpellPoint() direction check: the CPoint is at [rsp+0x70] in Torment (PT 0x42f885 lea rdx, [rsp+0x70] for
    # GetDirection, 0x42f8ac mov rax, [rsp+0x70]); BG [rsp+0x60]. Restore: same 5-byte mov ecx, 0x18.
    ('''			lea rdx, qword ptr ss:[rsp+0x60]                              ; point''',
     '''			lea rdx, qword ptr ss:[rsp+0x70]                              ; point ; EEex-PTEE: PT 0x42f885'''),

    # IsProtectedFromSpell -> Compare: Torment keeps the stat id in r12 (PT 0x2aac85 mov r12d, eax; 0x2ab3c4
    # movzx edx, r12w for GetAtOffset), constant in r13d -> r8d, relation in r15d -> r9d (PT 0x2ab3d6/0x2ab3d9);
    # edx/r8d/r9d at the call are the same arguments. Compare (PT 0x299e20) is BG's (same 12-entry jump table,
    # relations 0..5 = <=, ==, <, >, >=, != unsigned). Execution after the call: jmp 0x2aad9c (epilogue, returns eax).
    ('''	--   r13w = stat id, still available from the surrounding IsProtectedFromSpell() loop''',
     '''	--   r12w = stat id, still available from the surrounding IsProtectedFromSpell() loop (EEex-PTEE: BG r13w)'''),
    ('''			movzx r11d, r13w''',
     '''			movzx r11d, r12w ; EEex-PTEE: Torment keeps the stat id in r12'''),

    # CVisibilityMap::Destruct: Torment's prologue is `push rsi` (40 56) + `sub rsp, 0x20` (48 83 EC 20) = 6 bytes
    # (PT 0x2b79d0); restoring 5 bytes would cut `sub rsp, 0x20` in half. Restore / return 6 (relocatable bytes).
    ('''	EEex_HookBeforeRestoreWithLabels(EEex_Label("Hook-CVisibilityMap::Destruct()-FirstInstruction"), 0, 5, 5, {''',
     '''	EEex_HookBeforeRestoreWithLabels(EEex_Label("Hook-CVisibilityMap::Destruct()-FirstInstruction"), 0, 6, 6, { -- EEex-PTEE: 6-byte prologue'''),

    # op206/232/256 strref transform: label unsupported in Torment (same CheckAdd block as above: Torment always shows
    # the immunity's own strref, PT 0x1ebfef mov edx, [rbx+8]), so neither regression exists. Skip the hook.
    ('''	EEex_HookAfterRestoreWithLabels(EEex_Label("Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrref"), 0, 5, 5, {''',
     '''	-- EEex-PTEE: labels absent in Torment (CheckAdd uses the immunity strref as is): fix skipped
	if EEex_TryLabel("Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrref") then
	EEex_HookAfterRestoreWithLabels(EEex_Label("Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrref"), 0, 5, 5, {'''),
    ('''			jmp #L(Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrrefElse)
		]]}
	)''',
     '''			jmp #L(Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrrefElse)
		]]}
	)
	end -- EEex-PTEE'''),

    # CGameText::Render: Torment's renderer (PT 0x215600) is a different routine; EEex's BG fix does not apply and
    # EEex.dll's Override_Render is a log-once no-op on Torment (AUDIT.md): installing it would hide all floating text.
    ('''	EEex_JITAt(EEex_Label("Hook-CGameText::Render()-FirstInstruction"), {"jmp #L(CGameText::Override_Render)"})''',
     '''	-- EEex-PTEE: not installed: Torment's CGameText::Render is a different routine (EEex.dll override is a no-op)
	-- EEex_JITAt(EEex_Label("Hook-CGameText::Render()-FirstInstruction"), {"jmp #L(CGameText::Override_Render)"})'''),
]
