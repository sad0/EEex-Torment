# EEex_Trigger_Patch.lua: CGameAIBase::EvaluateStatusTrigger (PT 0x1656b0) keeps `this` in r15 (BG r14:
# PT 0x1656e0 mov r15, rcx) and its CAITrigger copy at [rbp+0x370] (BG [rbp+0x350]: PT 0x1656e7 lea rcx, [rbp+0x370]
# + copy ctor, 0x16578d movsx eax, word ptr [rbp+0x370]); frame is 0x20 bytes larger (lea rbp, [rsp-0x4b0]).
# DefaultJmp (PT 0x1657ac) is the same near `ja` (restore 0); the default target (PT 0x16c455 mov r13d, esi) still
# takes the result from esi; rax/rcx/rdx/r8-r11 are dead there (CString destructors follow).
# Torment's switch covers 0x400A..0x4110 (cmp eax, 0x106): ids > 0x4110 reach the hook. EEex's own trigger ids
# 0x410D..0x4110 are Torment triggers (ExtraProficiency*, LastPersonTalkedTo): renumbered in EEex_Trigger.py.
PATCHES = [
    ('''				function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r14 #ENDL", {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end,''',
     '''				function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r15 #ENDL", {rspOffset}}, "CGameAIBase", "EEex_GameObject_CastUT" end, -- EEex-PSTEE: r15'''),
    ('''						lea rax, qword ptr ss:[rbp+350h]''',
     '''						lea rax, qword ptr ss:[rbp+370h] ; EEex-PSTEE: Torment's CAITrigger copy'''),
    # Header: the trigger ids Torment uses (renumbered in EEex_Trigger.py, TRIGGER.IDS lines in notes/EEex_Trigger_Patch.md)
    ('|   0x410D EEex_HasDispellableEffect(O:Object*)  ', '|   0x4112 EEex_HasDispellableEffect(O:Object*)  '),
    ('|   0x410E EEex_LuaTrigger(S:Chunk*)  ', '|   0x4113 EEex_LuaTrigger(S:Chunk*)  '),
    ('|   0x410F EEex_IsImmuneToOpcode(O:Object*,I:Opcode*)  ', '|   0x4114 EEex_IsImmuneToOpcode(O:Object*,I:Opcode*)  '),
    ('|   0x4110 EEex_MatchObject(S:Chunk*)  ', '|   0x4115 EEex_MatchObject(S:Chunk*)  '),
    ('|   0x4110 EEex_MatchObjectEx(', '|   0x4115 EEex_MatchObjectEx('),
]
