# EEex_Opcode_Patch.lua: Torment code layout at the hook sites (tools/hookreview.py, notes/EEex_Opcode_Patch.md).
# Reviewed hooks without a change: CGameEffect::Destruct FirstCall (rdi, PT 0x159ca1), ProcessEffectList
# AfterListsResolved-1/-2 (PT 0x425cd7 je / 0x425ce0 jne, both short, restored 7 / 3 bytes identical: cmp dword ptr
# [rsi+0x4bd8], 0 / mov rcx, rsi) and -3 (PT 0x425ce5, rsi), op148 (rdi = effect, PT 0x1c2c8a; rdx = message),
# op214 (identical function, fdiff 1.000; 5-byte entry restore), op219 (rbx = effect, rdi = CSelectiveBonus,
# PT 0x1dad26), op248 (rbx / rdi, PT 0x1d6be2), op249 (6-byte entry restore push rdi; sub rsp, 0x40; AddTail rbx),
# op280 entry (identical 9 bytes, PT 0x1cf460), WildSpell OverrideSurgeNumber / Feedback / SuppressVisualEffectJmp /
# SPFLESHS Load / operator new / AddMessage (r14 = sprite, r13d = surge roll, same restore bytes and near je;
# CVisualEffect::Load identical, fdiff 1.000), CheckUsability JIT (5-byte entry), GetUsabilityText jne (4-byte cmp
# restore, rcx = effect), op326 OverrideSplprotContext (7-byte restore mov rcx, [rax+0x10c8]; rbx = effect, r8/r9 =
# source/target as BG), op333 CopyOp333Call (call [rax+8] + mov edx, [rbx+0x150] = 9 bytes), op342 LastParam2Jmp
# (rsi / rdi, near jne), GetAttackFrameType NOPs (6-byte virtual call [rax+0x198], rdi / rbx = sprite, dl = numAttacks),
# CImmunitiesEffect::OnList entry (5 bytes, rdx = effect), AddEffect noSave-Override (short jne + 3-byte test rbx, rbx).
# Opcode classes: 101/148/214/219/248/249/280/326/333/342 are the BG classes in Torment (tools/opcodes.json);
# 400..409 are free (Torment's table ends at 383, cmp eax, 0x17f).
PATCHES = [
    # CGameEffect::CopyFromBase (PT 0x1fce30): Torment swaps the two registers: this (dst) in rsi, the source
    # CGameEffectBase in rdi (PT 0x1fce4e mov rdi, rdx / 0x1fce51 mov rsi, rcx). The return address is still at
    # [rsp+0x38] (push rdi; sub rsp, 0x30). Only DecodeEffectFromBase passes a bare CGameEffectBase (as BG): every
    # other Torment caller is a Copy() (lea rdx, [rsi+8] / cmove).
    ('''			mov rdx, rdi                                             ; pDstEffect
			lea rcx, qword ptr ds:[rsi-#$(1)] ]], {EEex_PtrSize}, [[ ; pSrcEffect''',
     '''			mov rdx, rsi                                             ; pDstEffect ; EEex-PTEE: rsi
			lea rcx, qword ptr ds:[rdi-#$(1)] ]], {EEex_PtrSize}, [[ ; pSrcEffect ; EEex-PTEE: rdi'''),

    # CGameSprite::ProcessAI BeforeReturn (PT 0x42319f, same 8-byte mov r15, [rsp+0x158]): the sprite is in rbx
    # (PT 0x421858 mov rbx, rcx; reloaded at 0x421f22 from [rsp+0x60]; every jump to the site comes after it).
    ('''			mov rcx, rsi                                               ; pSprite
			call #L(EEex::Opcode_Hook_FlushDeferredAfterListsResolved)''',
     '''			mov rcx, rbx                                               ; pSprite ; EEex-PTEE: rbx
			call #L(EEex::Opcode_Hook_FlushDeferredAfterListsResolved)'''),

    # op146: Torment already uses m_special in the param2 == 0 path: m_special != 0 queues action 0x1d2 = 466
    # ForceSpellRESNoFeedback instead of ForceSpell (PT 0x1c2ae1 cmp dword ptr [rsi+0x48], edi; 0x1c2ae6 mov eax,
    # 0x1d2). EEex's (special & 1) -> SpellNoDec would overwrite Torment's vanilla no-feedback casts: disabled.
    ('''	EEex_HookBeforeCallWithLabels(EEex_Label("Hook-CGameEffectCastSpell::ApplyEffect()-CMessageHandler::AddMessage()"), {''',
     '''	if false then -- EEex-PTEE: Torment's op146 special != 0 means ForceSpellRESNoFeedback (action 466)
	EEex_HookBeforeCallWithLabels(EEex_Label("Hook-CGameEffectCastSpell::ApplyEffect()-CMessageHandler::AddMessage()"), {'''),
    ('''			mov word ptr ds:[rdx+#OFFSET_OF(CMessageInsertAction.m_action.m_actionID)], 191 ;     yes -> swap to SpellNoDec()
		]]}
	)''',
     '''			mov word ptr ds:[rdx+#OFFSET_OF(CMessageInsertAction.m_action.m_actionID)], 191 ;     yes -> swap to SpellNoDec()
		]]}
	)
	end -- EEex-PTEE'''),

    # CGameEffect::CheckAdd (PT 0x1eba60): the sprite is in rsi (PT 0x1eba8d mov rsi, rdx; 0x1ebace
    # cmp dword ptr [rsi+0x4bbc], 0), BG r14. rdi = effect, rdx still the sprite (PT 0x1ebaa7 mov eax, [rdx+0x48]);
    # LastProbabilityJmp is a near jb (PT 0x1ebaa1) to ProbabilityFailed (PT 0x1ebbea xor eax, eax; epilogue).
    ('''				mov rdx, r14                          ; pSprite''',
     '''				mov rdx, rsi                          ; pSprite ; EEex-PTEE: rsi'''),

    # New opcodes, Copy(): Torment's CGameEffect is 0x160 bytes (every Torment Copy, e.g. PT 0x1ed3ac mov ecx,
    # 0x160); the rest of the Copy body is identical (PT 0x1ed390: +0x88 / +0x80 / +0x110, Construct args, delete
    # of the 0x30-byte item effect, CopyFromBase(rbx, rsi+8)). CGameEffect::Construct takes the same arguments
    # (fdiff 0.989: Torment only constructs one more member at +0x154).
    ('''				mov ecx, 158h''',
     '''				mov ecx, #$(1) ]], {CGameEffect.sizeof}, [[ ; EEex-PTEE: Torment's CGameEffect is 160h'''),

    # New opcodes, DecodeEffect: Torment's cases end with `mov rbx, rax; jmp 0x2030a6` and their null check jumps to
    # the same 0x2030a6 (mov eax, [rsp+0x80], then mov r15, [rsp+0x60] = the "Fail" label PT 0x2030ad, 7 bytes later).
    # There is no shared `mov rbx, rax` like BG's "Success" (0x1e272d): the Torment "Success" label (PT 0x2030a3) is
    # `mov dword ptr [rbx+0x1c], eax` of the default case and "Fail" skips the eax load. Join at Fail - 7 instead.
    ('''				jz #L(Hook-CGameEffect::DecodeEffect()-Fail)''',
     '''				jz #L(ptee_decode_join) ; EEex-PTEE: Torment's join (Fail - 7, PT 0x2030a6)'''),
    ('''				call #$(1) ]], {constructor}, [[ #ENDL
				jmp #L(Hook-CGameEffect::DecodeEffect()-Success)''',
     '''				call #$(1) ]], {constructor}, [[ #ENDL
				mov rbx, rax ; EEex-PTEE: done by each Torment case
				jmp #L(ptee_decode_join)'''),
    # DefaultJmp (PT 0x1fe3b6, near ja): rdi = Item_effect_st, r14 = source, ebp = sourceID, rsi = target, eax = opcode,
    # rbx = 0, as BG. Torment already stores r15 at [rsp+0x60] before the ja (PT 0x1fe3ac): EEex's store is redundant.
    ('''	EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CGameEffect::DecodeEffect()-DefaultJmp"), 0, {
		{"hook_integrity_watchdog_ignore_registers", {''',
     '''	EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CGameEffect::DecodeEffect()-DefaultJmp"), 0, {
		{"ptee_decode_join", EEex_Label("Hook-CGameEffect::DecodeEffect()-Fail") - 7}, -- EEex-PTEE: PT 0x2030a6
		{"hook_integrity_watchdog_ignore_registers", {'''),
]
