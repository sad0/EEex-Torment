# EEex_Debug_Patch.lua (installed only with EEex_Debug_LogActions / EEex_Debug_LogFontWraps)
# - CGameAIBase::ExecuteAction DefaultJmp (PT 0x16c99c, near ja 0x172220, 6 bytes, restoreSize 0): this in rdi
#   (PT 0x16c914 mov rdi, rcx; BG rbx). r8 = action index (saved, cmp r8d, 0x1D5 rebuilt as in BG). After the ja
#   Torment writes r14 / rax / rcx before use and the default case writes rdx / rcx; rdx, r9..r11 are undefined on the
#   jne path (PT 0x16c960) so no case can read them: upstream ignore list still valid.
# - CGameSprite::ExecuteAction DefaultJmp (PT 0x40bd90, near ja 0x40e653): sprite in rdi (same as BG). Torment
#   compares eax instead of ecx (PT 0x40bd87 movsx rax, r8w / cmp eax, 0x1D7) and indexes the table with rax
#   (PT 0x40bd9d); live across the jcc: rax (index), rdx (edx = word read PT 0x40bd3a / 0x40bd79, used PT 0x40bdb9),
#   r8 (action id), r9 (global pointer, used PT 0x40bdc4); r10 is written right after (lea r10), rcx before use.
#   The hook saves rax / rdx / r8 / r9 and rebuilds the flags with cmp eax, 0x1D7.
# - fontWrap first instruction (PT 0x4cbb40, 123-byte function): JITAt jmp to EEex::Override_fontWrap (AUDIT.md:
#   fontWrap reimplementation identical, 1.00). Unchanged.
PATCHES = [
    ('''						function(rspOffset) return {[[
							mov qword ptr ss:[rsp+#$(1)], rbx
						]], {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,
						function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], 1", {rspOffset}, "#ENDL"} end,''',
     '''						function(rspOffset) return {[[
							mov qword ptr ss:[rsp+#$(1)], rdi ; EEex-PSTEE: rdi (PT 0x16c914)
						]], {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,
						function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], 1", {rspOffset}, "#ENDL"} end,'''),
    ('''			{"hook_integrity_watchdog_ignore_registers", {
				EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R11
			}}},
			EEex_FlattenTable({
				{[[
					#MAKE_SHADOW_SPACE(80)
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rcx
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)], rdx
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)], r9
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)], r10
				]]},''',
     '''			{"hook_integrity_watchdog_ignore_registers", { -- EEex-PSTEE: rax / rdx / r8 / r9 live in Torment
				EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
			}}},
			EEex_FlattenTable({
				{[[
					#MAKE_SHADOW_SPACE(80)
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rax ; EEex-PSTEE
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)], rdx
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)], r8 ; EEex-PSTEE
					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)], r9 ; EEex-PSTEE
				]]},'''),
    ('''					call_error:
					mov r10, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)]
					mov r9, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)]
					mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
					mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
					#DESTROY_SHADOW_SPACE
					cmp ecx, 0x1D7''',
     '''					call_error:
					mov r9, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)] ; EEex-PSTEE
					mov r8, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)] ; EEex-PSTEE
					mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
					mov rax, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)] ; EEex-PSTEE
					#DESTROY_SHADOW_SPACE
					cmp eax, 0x1D7 ; EEex-PSTEE: Torment compares eax (PT 0x40bd8b)'''),
]
