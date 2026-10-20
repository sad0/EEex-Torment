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

	// Torment's own CGameEffect::CheckSave (base vtable slot 7, read before EEex patches any vtable).
	// EEex::Override_CGameEffect_CheckSave forwards to it: PT's saving-throw rules differ from BG's.
	extern int (__fastcall* p_CGameEffect_CheckSave)(CGameEffect* pThis, CGameSprite* pTarget, byte* saveVSDeathRollRaw,
		byte* saveVSWandsRollRaw, byte* saveVSPolyRollRaw, byte* saveVSBreathRollRaw, byte* saveVSSpellRollRaw, byte* resistMagicRollRaw);

	// Torment's keyboard / controller UI navigation (arrows / controller buttons move the focused item,
	// Enter activates it). Called first by uiEventMenuStack; true = event consumed. PT 0x459ff0.
	extern bool (__cdecl* p_uiNavigateEvent)(SDL_Event* pEvent, SDL_Rect* pWindow);

	// To-hit rules of Torment's CGameSprite::Hit (PT 0x4147b0), used by EEex's simulated attack rolls:
	// CGameAIBase::PartyHasItem (PT 0x174e00), the value of a global variable (PT 0x2b4b80: variable
	// hash, name, default) and the Fist of Iron test (PT 0x3d0ae0: opcode 382 effect + animation 0x?32).
	extern int (__fastcall* p_CGameAIBase_PartyHasItem)(CGameAIBase* pThis, CResRef* pItem);
	extern int (__fastcall* p_CVariableHash_GetValue)(CVariableHash* pThis, CString* pName, int nDefault);
	extern int (__fastcall* p_CGameSprite_HasFistOfIron)(CGameSprite* pThis);

	// Torment's CChitin::ENGINE_MODE value (absent from the BG2EE EngineMode enum)
	constexpr int ENGINE_MODE_PST = 3;

	// Fill the pointers above (called first thing from EEex::InitEEex; not named InitBindings, which is the DLL export). Missing patterns are logged.
	void BindEngine();
}
