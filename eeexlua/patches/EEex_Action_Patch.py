# EEex_Action_Patch.lua: Torment register allocation / code layout at the hook sites.
# - CGameAIBase::ExecuteAction (PT 0x16c8e0): this in rdi (PT 0x16c914 mov rdi, rcx; BG rbx), esi = -2 return
#   value, rbx = 0 (BG r13) stored by NormalBranch (PT 0x172234 mov [rdi+0x4aa], si / mov [rdi+0x4b4], ebx). The
#   default case (PT 0x172220) starts with lea rdx, [rip+X] (7 bytes, RIP-relative: upstream restores it verbatim,
#   which is only reached on a Lua error but would then pass a wrong string pointer). Torment version: nothing is
#   restored, the error path loads the string address itself, then returns to PT 0x172227 (lea rcx, [rbp-0x80]).
# - CGameSprite::SetCurrAction (PT 0x42b610): Torment has no CString local, so there is no last call; the label
#   points at the epilogue (PT 0x42bbd1 mov rbx, [rsp+0x48], 5 bytes, reached by all paths: fallthrough, PT 0x42b9cd,
#   0x42bbc9; the only ret is PT 0x42bbe9). Restore-style hook before it: sprite in rbx (PT 0x42b632 mov rbx, rcx),
#   action in rsi (PT 0x42b62f mov rsi, rdx; BG r14). rsp is 16-aligned there (3 pushes + 0x20); the volatile
#   registers are dead (the function returns void, rax holds a field value).
PATCHES = [
    ('''	EEex_HookBeforeRestoreWithLabels(EEex_Label("Hook-CGameAIBase::ExecuteAction()-DefaultCase"), 0, 7, 7, {''',
     '''	-- EEex-PSTEE: the 7 overwritten bytes are lea rdx, [rip+X] (PT 0x172220): not restorable, rebuilt on the error path
	local ptExecuteActionDefaultCase = EEex_Label("Hook-CGameAIBase::ExecuteAction()-DefaultCase")
	if EEex_ReadU8(ptExecuteActionDefaultCase) ~= 0x48 or EEex_ReadU8(ptExecuteActionDefaultCase + 1) ~= 0x8D
		or EEex_ReadU8(ptExecuteActionDefaultCase + 2) ~= 0x15
	then
		EEex_Error("[EEex-PSTEE] Unexpected CGameAIBase::ExecuteAction() default case")
	end
	local ptExecuteActionDefaultCaseString = ptExecuteActionDefaultCase + 7 + EEex_Read32(ptExecuteActionDefaultCase + 3)
	EEex_HookBeforeRestoreWithLabels(ptExecuteActionDefaultCase, 0, 0, 7, {'''),
    ('''					function(rspOffset) return {[[
						mov qword ptr ss:[rsp+#$(1)], rbx
					]], {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,
				},
				["returnType"] = EEex_LuaCallReturnType.Number,''',
     '''					function(rspOffset) return {[[
						mov qword ptr ss:[rsp+#$(1)], rdi ; EEex-PSTEE: rdi (PT 0x16c914)
					]], {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,
				},
				["returnType"] = EEex_LuaCallReturnType.Number,'''),
    ('''				call_error:
				#RESUME_SHADOW_ENTRY
				#DESTROY_SHADOW_SPACE
			]]}
		})
	)''',
     '''				call_error:
				#RESUME_SHADOW_ENTRY
				#DESTROY_SHADOW_SPACE
				mov rdx, #$(1) ; EEex-PSTEE: string of the overwritten RIP-relative lea rdx
			]], {ptExecuteActionDefaultCaseString}}
		})
	)'''),
    ('''	EEex_HookAfterCallWithLabels(EEex_Label("CGameSprite::SetCurrAction()-LastCall"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
		{[[
			cmp word ptr ds:[r14], 0 ; Don't call the hook for NoAction() since the engine spams it
			jz #L(return)

			mov rcx, rdi                                          ; pSprite''',
     '''	-- EEex-PSTEE: no last call in Torment; hook before the epilogue's mov rbx, [rsp+0x48] (PT 0x42bbd1, 5 bytes)
	EEex_HookBeforeRestoreWithLabels(EEex_Label("CGameSprite::SetCurrAction()-LastCall"), 0, 5, 5, {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}}},
		{[[
			cmp word ptr ds:[rsi], 0 ; Don't call the hook for NoAction() since the engine spams it ; EEex-PSTEE: action in rsi
			jz #L(return)

			mov rcx, rbx                                          ; pSprite ; EEex-PSTEE: rbx'''),
]
