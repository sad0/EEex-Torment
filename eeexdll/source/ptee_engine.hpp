// EEex-PTEE: Torment.exe engine functions that have no BG2EE counterpart (or a different signature),
// bound by name from EEex_scripts/extra_pattern_dbs/ptee.db (tools/port_extra.py). Used by the
// Torment rewrites of EEex's engine reimplementations (eeexdll/patch_sources.py).
#pragma once

#include "Baldur_generated.h"

namespace PTEE {

	// Effective alignment of a sprite: for the Nameless One in Torment mode it is derived from the
	// "Law"/"Good" global counters, otherwise from the AI type. Used by CGameEffectUsability (op319)
	// param2 = 8. PT 0x3c4fe0. pType is a by-value argument: the callee destroys it.
	extern byte (__fastcall* p_CGameSprite_GetEffectiveAlignment)(CGameSprite* pSprite, CAIObjectType* pType);

	// Fill the pointers above (called first thing from EEex::InitEEex; not named InitBindings, which is the DLL export). Missing patterns are logged.
	void BindEngine();
}
