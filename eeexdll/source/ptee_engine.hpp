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

	// SDL_SetHint (SDL 2.0.4 inside Torment.exe): Torment's WinMain sets SDL_WINDOWS_NO_CLOSE_ON_ALT_F4.
	extern int (__cdecl* p_SDL_SetHint)(const char* name, const char* value);

	// CInfinity::SetZoomEnabled (PT 0x3097f0): Torment's CScreenWorld::EndDialog disables zooming again when
	// the "Zoom Lock" option is on.
	extern void (__fastcall* p_CInfinity_SetZoomEnabled)(CInfinity* pThis, int bEnabled);

	// Torment's UI rect (PT 0x4a3180): {W*f, H*f, W*(1-f), H*(1-f)} with W/H = CVidMode::SCREENWIDTH/HEIGHT and
	// f = a float of CChitin (+0x1f4); uiDrawMenuStack draws every menu inside it. g_pChitin is its argument.
	extern SDL_Rect* (__fastcall* p_CChitin_GetUIRect)(CChitin* pThis, SDL_Rect* pRect);
	extern CChitin** p_g_pChitin;

	// CVidMode window -> internal screen coordinates (PT 0x4a7fe0): x' = SCREENWIDTH * (x - scrollX) / nWidth,
	// y' = SCREENHEIGHT * (2 * [+0x190] - scrollY + y) / nHeight.
	extern CPoint* (__fastcall* p_CVidMode_WindowToScreen)(CVidMode* pThis, CPoint* pOut, int x, int y);

	// CAIScript::Read(resref, bPlayerScript) (PT 0x12d240). It first frees the script's current content.
	extern void (__fastcall* p_CAIScript_Read)(CAIScript* pThis, CResRef res, int bPlayerScript);

	// New AI script; Torment's constructor always reads a non-player script, so a player script is read
	// again with the flag, like CGameSprite::JoinParty (PT 0x416435).
	CAIScript* NewScript(CResRef res, bool bPlayerScript);

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

	// Torment replaced CGameOptions::m_bAreaMapZoom by "Disable Area Map Zoom" ([Graphics], read by
	// CBaldurChitin::LoadOptions PT 0x2e77b5 into CGameOptions+0x274): non-zero = zoom to the area map
	// instantly (CScreenWorld::ZoomToMap / ResetZoom PT 0x3686e0 / 0x363080). m_bExpireTraps (+0x268)
	// is the last proven field before it.
	inline bool IsAreaMapZoomDisabled(const CGameOptions& options) {
		return *reinterpret_cast<const int*>(reinterpret_cast<const char*>(&options.m_bExpireTraps) + 0xc) != 0;
	}

	// "Use Touch Actionbar" ([Program Options], CBaldurChitin::LoadOptions PT 0x2e7800 -> CGameOptions+0x280):
	// Torment-mode actionbar menu WORLD_ACTIONBAR_LEFT_TABLET instead of WORLD_ACTIONBAR_LEFT (PT 0x304f6a).
	inline bool UseTouchActionbar(const CGameOptions& options) {
		return *reinterpret_cast<const int*>(reinterpret_cast<const char*>(&options.m_bExpireTraps) + 0x18) != 0;
	}

	// Torment-only CInfinity flag (+0x45c, after m_bZooming +0x448): set by spell-cinematic projectiles
	// (e.g. Celestial Host, PT 0x2891d9 / 0x26c599) while they drive the camera; CInfinity::SetScrollDest
	// (PT 0x309450) then keeps the destination unclamped.
	inline bool IsCinematicCamera(const CInfinity& infinity) {
		return *reinterpret_cast<const int*>(reinterpret_cast<const char*>(&infinity.m_bZooming) + 0x14) != 0;
	}

	// Torment's CChitin::ENGINE_MODE value (absent from the BG2EE EngineMode enum)
	constexpr int ENGINE_MODE_PST = 3;

	// Fill the pointers above (called first thing from EEex::InitEEex; not named InitBindings, which is the DLL export). Missing patterns are logged.
	void BindEngine();
}
