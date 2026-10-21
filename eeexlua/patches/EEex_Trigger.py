# EEex_Trigger.lua: EEex's trigger ids 0x410D..0x4110 are real Torment triggers (PT TRIGGER.IDS: 0x410d
# ExtraProficiency, 0x410e ExtraProficiencyGT, 0x410f ExtraProficiencyLT, 0x4110 LastPersonTalkedTo, 0x4111
# NearSavedLocationPST). Torment's CGameAIBase::EvaluateStatusTrigger switch (PT 0x16579b add eax, -0x400A;
# cmp eax, 0x106; ja 0x16c455) dispatches 0x410D..0x4110 through its jump table to their own cases (byte table
# PT 0x16c7d8 / dword table 0x16c4fc: none of them maps to the default target), so EEex's hook never sees them.
# Ids above 0x4110 take the `ja` into the hook. 0x4111 (NearSavedLocationPST) is listed in TRIGGER.IDS but has no
# case and no other handler in Torment.exe (no 0x4111 immediate anywhere): it stays vanilla (the Lua hook returns
# false for unknown ids, as the engine's default). EEex's triggers move to the next free ids 0x4112..0x4115
# (TRIGGER.IDS lines in eeexlua/notes/EEex_Trigger_Patch.md).
PATCHES = [
    ('	if triggerID == 0x410D then -- EEex_HasDispellableEffect',
     '	if triggerID == 0x4112 then -- EEex_HasDispellableEffect ; EEex-PTEE: 0x410D is Torment\'s ExtraProficiency'),
    ('	elseif triggerID == 0x410E then -- EEex_LuaTrigger',
     '	elseif triggerID == 0x4113 then -- EEex_LuaTrigger ; EEex-PTEE: 0x410E is Torment\'s ExtraProficiencyGT'),
    ('	elseif triggerID == 0x410F then -- EEex_IsImmuneToOpcode',
     '	elseif triggerID == 0x4114 then -- EEex_IsImmuneToOpcode ; EEex-PTEE: 0x410F is Torment\'s ExtraProficiencyLT'),
    ('	elseif triggerID == 0x4110 then -- EEex_MatchObject / EEex_MatchObjectEx',
     '	elseif triggerID == 0x4115 then -- EEex_MatchObject / EEex_MatchObjectEx ; EEex-PTEE: 0x4110 is Torment\'s LastPersonTalkedTo'),
]
