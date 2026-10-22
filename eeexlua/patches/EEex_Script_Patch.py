# EEex_Script_Patch.lua
# - OnRead (PT 0x12d2e6, call after the resref copy in CAIScript::Read PT 0x12d240): script in rsi (PT 0x12d26e
#   mov rsi, rcx), bPlayerScript in r14 (PT 0x12d26b mov r14d, r8d; next write PT 0x12d5f8, after the site). The
#   instruction after the call overwrites rax. Unchanged.
# - OnDestruct (PT 0x12cf48, CPtrList destructor call in CAIScript::Destruct PT 0x12cef0): script in rsi
#   (PT 0x12cefe). Unchanged.
# - OnCopy1 / OnCopy2: Torment's CAIScript::Construct (PT 0x176d80) has no script-cache copy path, it always parses
#   through CAIScript::Read (PATTERNS.md "unsupported": labels undefined). OnRead covers every Torment script, so the
#   copy hooks are skipped when the label is missing.
PATCHES = [
    ('''	for _, entry in ipairs({
		{"Hook-CAIScript::Construct()-OnCopy1", "rdi"},
		{"Hook-CAIScript::Construct()-OnCopy2", "rsi"}, })
	do
		EEex_HookBeforeCallWithLabels(EEex_Label(entry[1]), {''',
     '''	for _, entry in ipairs({
		{"Hook-CAIScript::Construct()-OnCopy1", "rdi"},
		{"Hook-CAIScript::Construct()-OnCopy2", "rsi"}, })
	do
	if EEex_TryLabel(entry[1]) then -- EEex-PSTEE: no script-cache copy in Torment (labels undefined)
		EEex_HookBeforeCallWithLabels(EEex_Label(entry[1]), {'''),
    ('''				mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
				mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
				#DESTROY_SHADOW_SPACE
			]]}
		)
	end''',
     '''				mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
				mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
				#DESTROY_SHADOW_SPACE
			]]}
		)
	end -- EEex-PSTEE
	end'''),
]
