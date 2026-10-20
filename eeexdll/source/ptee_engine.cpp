// EEex-PTEE: bindings for Torment-only engine functions (see ptee_engine.hpp).

#include "ptee_engine.hpp"

namespace PTEE {

	byte (__fastcall* p_CGameSprite_GetEffectiveAlignment)(CGameSprite* pSprite, CAIObjectType* pType) = nullptr;

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
	}
}
