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

	// Torment-only activity flag of CGameSprite at +0x3910, right after m_activeImprisonment (+0x390c;
	// m_bSelected follows at +0x3914). Set to 1 by the constructor like m_activeAI/m_activeImprisonment,
	// cleared and restored by Torment's spell-cinematic projectiles (AIUpdate of the Abyssal Fury S077* and
	// Celestial Host S091* classes, ...). Every Torment target search that tests m_active / m_activeAI /
	// m_activeImprisonment also tests it (CGameArea::GetNearest both overloads, GetAllInRange, ... 40 sites).
	inline bool IsActiveCinematic(const CGameSprite& sprite) {
		return reinterpret_cast<const int*>(&sprite.m_activeImprisonment)[1] != 0;
	}

	// Sprite update spreading mask, a constant byte of the engine (BG2EE 1, Torment 7): staggered sprite
	// work runs when (m_id & mask) == (worldTime & mask), and CGameSprite::CheckIfVisible keeps a sprite
	// seen for m_canBeSeen = (mask + 1) * 4 ticks. EEex's CheckIfVisible hard-codes BG's 8.
	extern byte* p_g_nSpriteUpdateMask;
	inline short CanBeSeenTicks() {
		return static_cast<short>((*p_g_nSpriteUpdateMask + 1) << 2);
	}

	// Torment's CChitin::ENGINE_MODE value (absent from the BG2EE EngineMode enum)
	constexpr int ENGINE_MODE_PST = 3;

	// Fill the pointers above (called first thing from EEex::InitEEex; not named InitBindings, which is the DLL export). Missing patterns are logged.
	void BindEngine();
}
