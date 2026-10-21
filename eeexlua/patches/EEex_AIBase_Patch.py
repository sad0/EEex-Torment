# EEex_AIBase_Patch.lua: no change needed.
# The three JITAt overrides write a jmp to EEex.dll at the first instruction of whole functions that EEex.dll
# reimplements (AUDIT.md: identical code apart from jump-table data): CGameAIBase::ApplyTriggers (PT 0x1640c0,
# 191 bytes), CGameAIBase::SetTrigger (PT 0x175df0, 88 bytes), CMessageSetLastObject::Run (PT 0x2384a0, 642 bytes);
# each label is the .pdata function start, mapped from BG by tools/fmap (prop0 / sig / fuzzy 1.00). Room for a 14-byte
# absolute jmp in every case.
PATCHES = []
