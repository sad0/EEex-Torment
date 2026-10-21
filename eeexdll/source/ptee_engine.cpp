// EEex-PTEE: bindings for Torment-only engine functions (see ptee_engine.hpp).

#include "ptee_engine.hpp"

namespace PTEE {

	byte (__fastcall* p_CGameSprite_GetEffectiveAlignment)(CGameSprite* pSprite, CAIObjectType* pType) = nullptr;
	int (__fastcall* p_CGameEffect_CheckSave)(CGameEffect* pThis, CGameSprite* pTarget, byte* saveVSDeathRollRaw,
		byte* saveVSWandsRollRaw, byte* saveVSPolyRollRaw, byte* saveVSBreathRollRaw, byte* saveVSSpellRollRaw, byte* resistMagicRollRaw) = nullptr;
	bool (__cdecl* p_uiNavigateEvent)(SDL_Event* pEvent, SDL_Rect* pWindow) = nullptr;
	int (__fastcall* p_CGameAIBase_PartyHasItem)(CGameAIBase* pThis, CResRef* pItem) = nullptr;
	int (__fastcall* p_CVariableHash_GetValue)(CVariableHash* pThis, CString* pName, int nDefault) = nullptr;
	int (__fastcall* p_CGameSprite_HasFistOfIron)(CGameSprite* pThis) = nullptr;
	byte* p_g_nSpriteUpdateMask = nullptr;
	int (__cdecl* p_SDL_SetHint)(const char* name, const char* value) = nullptr;
	void (__fastcall* p_CInfinity_SetZoomEnabled)(CInfinity* pThis, int bEnabled) = nullptr;
	SDL_Rect* (__fastcall* p_CChitin_GetUIRect)(CChitin* pThis, SDL_Rect* pRect) = nullptr;
	CChitin** p_g_pChitin = nullptr;
	CPoint* (__fastcall* p_CVidMode_WindowToScreen)(CVidMode* pThis, CPoint* pOut, int x, int y) = nullptr;
	void (__fastcall* p_CAIScript_Read)(CAIScript* pThis, CResRef res, int bPlayerScript) = nullptr;

	CAIScript* NewScript(CResRef res, bool bPlayerScript) {
		CAIScript *const pScript = newEngineObj<CAIScript>(res);
		if (bPlayerScript && p_CAIScript_Read != nullptr) {
			p_CAIScript_Read(pScript, res, 1);
		}
		return pScript;
	}

	template<typename OutType>
	static void bind(const String& patternName, OutType& pointerOut) {
		PatternValueHandle patternHandle;
		if (sharedState().GetPatternValue(patternName, patternHandle) == PatternValueType::SINGLE) {
			pointerOut = reinterpret_cast<OutType>(sharedState().GetSinglePatternValue(patternHandle));
		}
		else {
			FPrintT(TEXT("[!][EEex.dll] PTEE::bind() - Torment binding pattern [%s] missing (EEex_scripts/extra_pattern_dbs/ptee.db)\n"), patternName.c_str());
		}
	}

	void BindEngine() {
		bind(TEXT("PTEE-CGameSprite::GetEffectiveAlignment"), p_CGameSprite_GetEffectiveAlignment);
		bind(TEXT("PTEE-uiNavigateEvent"), p_uiNavigateEvent);
		bind(TEXT("PTEE-CGameAIBase::PartyHasItem"), p_CGameAIBase_PartyHasItem);
		bind(TEXT("PTEE-CVariableHash::GetValue"), p_CVariableHash_GetValue);
		bind(TEXT("PTEE-CGameSprite::HasFistOfIron"), p_CGameSprite_HasFistOfIron);
		bind(TEXT("PTEE-g_nSpriteUpdateMask"), p_g_nSpriteUpdateMask);
		bind(TEXT("PTEE-SDL_SetHint"), p_SDL_SetHint);
		bind(TEXT("PTEE-CInfinity::SetZoomEnabled"), p_CInfinity_SetZoomEnabled);
		bind(TEXT("PTEE-CChitin::GetUIRect"), p_CChitin_GetUIRect);
		bind(TEXT("PTEE-g_pChitin"), p_g_pChitin);
		bind(TEXT("PTEE-CVidMode::WindowToScreen"), p_CVidMode_WindowToScreen);
		bind(TEXT("PTEE-CAIScript::Read"), p_CAIScript_Read);

		void** pBaseEffectVtbl = nullptr;
		bind(TEXT("Data-CGameEffect::vftable"), pBaseEffectVtbl);
		if (pBaseEffectVtbl != nullptr) {
			p_CGameEffect_CheckSave = reinterpret_cast<decltype(p_CGameEffect_CheckSave)>(pBaseEffectVtbl[7]);
		}
	}
}

// Torment UI struct layouts (tools/bindings/manual_fields*.json, eeexlua/notes/uiItem_layout.md): a header
// regression must not compile
static_assert(sizeof(uiMenu) == 0x98, "Torment uiMenu");
static_assert(sizeof(CGameEffect) == 0x160, "Torment CGameEffect (CResRef at +0x154)");
static_assert(sizeof(CGameSprite) == 0x52c8, "Torment CGameSprite (operator new size)");
static_assert(sizeof(CAIAction) == 0x80, "Torment CAIAction (no m_source)");
static_assert(offsetof(uiMenu, items) == 0x28 && offsetof(uiMenu, onOpen) == 0x50 && offsetof(uiMenu, ignoreEsc) == 0x74, "Torment uiMenu");
static_assert(sizeof(uiItem) == 0x3b0, "Torment uiItem");
static_assert(offsetof(uiItem, text) == 0x98 && offsetof(uiItem, bam) == 0xe8 && offsetof(uiItem, list) == 0x130, "Torment uiItem");
static_assert(offsetof(uiItem, scrollbar) == 0x198 && offsetof(uiItem, edit) == 0x1e8 && offsetof(uiItem, button) == 0x248, "Torment uiItem");
static_assert(offsetof(uiItem, rectangle) == 0x2e8 && offsetof(uiItem, action) == 0x2f8 && offsetof(uiItem, tooltip) == 0x328, "Torment uiItem");
static_assert(offsetof(uiItem, glow) == 0x380 && offsetof(uiItem, next) == 0x3a8, "Torment uiItem");
