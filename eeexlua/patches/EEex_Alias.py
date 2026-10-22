# EEex_Alias.lua: Torment has no out-of-line CAIAction destructor. Every Torment site inlines it as five CString
# destructors (m_string2 +0x68, m_string1 +0x60, then the m_name of m_acteeID2 +0x38, m_acteeID +0x20, m_actorID +0x08;
# e.g. PT 0x1251c2, 0x12cbcc, 0x413b82), so the phase-2 label CAIAction::Destruct resolved to CString::Destruct
# (PT 0x4843c0) and `CAIAction.Destruct(action)` destroyed a CString at action+0 (m_actionID): heap corruption /
# access violation when EEex_MemoryManager freed its CAIAction copy (EEex_Action_ExecuteResponseStringOnAIBaseInstantly).
# BG2EE's ~CAIAction (BG 0x120680) destroys the same members plus m_source (+0x80), absent in Torment.
# Replaced here, before EEex_MemoryManagerDefinitions.lua captures CAIAction.Destruct.
PATCHES = [
    ('''	CAIAction.Construct1 = alias(CAIAction.Construct_Overload_ActionID_DestPoint_SpecificID_SpecificID2)''',
     '''	CAIAction.Construct1 = alias(CAIAction.Construct_Overload_ActionID_DestPoint_SpecificID_SpecificID2)
	-- EEex-PTEE: Torment inlines ~CAIAction (no function to bind): the same five CString destructors in Lua
	CAIAction.Destruct = function(action)
		CString.Destruct(action.m_string2)
		CString.Destruct(action.m_string1)
		CString.Destruct(action.m_acteeID2.m_name)
		CString.Destruct(action.m_acteeID.m_name)
		CString.Destruct(action.m_actorID.m_name)
	end'''),
]
