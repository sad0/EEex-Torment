// EEex-PTEE: bindings for Torment-only engine functions (see ptee_engine.hpp).

#include "ptee_engine.hpp"

namespace PTEE {

	byte (__fastcall* p_CGameSprite_GetEffectiveAlignment)(CGameSprite* pSprite, CAIObjectType* pType) = nullptr;
	int (__fastcall* p_CGameEffect_CheckSave)(CGameEffect* pThis, CGameSprite* pTarget, byte* saveVSDeathRollRaw,
		byte* saveVSWandsRollRaw, byte* saveVSPolyRollRaw, byte* saveVSBreathRollRaw, byte* saveVSSpellRollRaw, byte* resistMagicRollRaw) = nullptr;
	bool (__cdecl* p_uiNavigateEvent)(SDL_Event* pEvent, SDL_Rect* pWindow) = nullptr;

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

		void** pBaseEffectVtbl = nullptr;
		bind(TEXT("Data-CGameEffect::vftable"), pBaseEffectVtbl);
		if (pBaseEffectVtbl != nullptr) {
			p_CGameEffect_CheckSave = reinterpret_cast<decltype(p_CGameEffect_CheckSave)>(pBaseEffectVtbl[7]);
		}
	}
}
