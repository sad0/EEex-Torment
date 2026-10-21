# EEex_Object_Patch.lua: CAIObjectType::Decode (PT 0x129470) register allocation. BG keeps this in r13, the caller
# (CGameAIBase*) in r12 and the OBJECT.IDS loop index in r15; Torment keeps this in rbx (PT 0x1294a4 mov rbx, rcx),
# the caller in r13 (PT 0x12949a mov r13, rdx) and the loop index in r12 (PT 0x12976c mov r12, r15;
# 0x12979a movzx r14d, byte ptr [r12+rbx+0x10]; 0x12ae55 inc r12 / cmp r12, 5 = NormalBranch).
# Unchanged: both jcc are near (TargetNameOverride PT 0x1294eb je, 6 bytes, restore 0; DefaultJmp PT 0x1297b2 ja,
# 6 bytes); curAIType is still [rbp-0x11] (PT 0x1297db lea rcx, [rbp-0x11]) = rsp+0x68 (same frame: lea rbp,
# [rsp-0x2f] / sub rsp, 0xa8), so IgnoreStackSizes {0x68, sizeof} stays; rdx ([rbp-0x29]) is still live and restored;
# ReturnBranch (PT 0x129ad3, loop exit `jge` PT 0x12ae60) and NormalBranch (PT 0x12ae55) labels verified.
# Torment's OBJECT.IDS ends at 114 (jump table cmp eax, 0x71 on id-1, as BG): EEex's 115..118 reach the hook.
PATCHES = [
    # TargetNameOverride: decodingAIType (this) is rbx (PT 0x1294f1 cmp dword ptr [rbx+0xc], -1)
    ('''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r13 #ENDL", {rspOffset}}, "CAIObjectType" end,
				},
				["returnType"] = EEex_LuaCallReturnType.Boolean,''',
     '''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], rbx #ENDL", {rspOffset}}, "CAIObjectType" end, -- EEex-PTEE: rbx
				},
				["returnType"] = EEex_LuaCallReturnType.Boolean,'''),
    # DefaultJmp: decodingAIType rbx, caller r13, nSpecialCaseI r12
    ('''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r13 #ENDL", {rspOffset}}, "CAIObjectType" end,
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r12 #ENDL", {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r15 #ENDL", {rspOffset}} end,''',
     '''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], rbx #ENDL", {rspOffset}}, "CAIObjectType" end, -- EEex-PTEE: rbx
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r13 #ENDL", {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end, -- EEex-PTEE: r13
					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r12 #ENDL", {rspOffset}} end, -- EEex-PTEE: r12 (loop index)'''),
]
