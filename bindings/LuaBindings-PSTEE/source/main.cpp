
#include "Baldur_generated.h"
#include "EEexLua_generated.h"

static void exportPattern(const String& name, void* value) {

	PatternValueHandle handle;
	if (sharedState().GetOrCreatePatternValue(name, PatternValueType::SINGLE, handle)) {
		FPrintT(TEXT("[!][LuaBindings-PSTEE.dll] exportPattern() - [%s].Type must be SINGLE\n"), name.c_str());
		return;
	}

	sharedState().SetSinglePatternValue(handle, value);
}

// Ugly hack to get a member-function pointer
template<typename T>
static constexpr void* getMemberPtr(T func) {
	return reinterpret_cast<void*&>(func);
}

static void exportPatterns() {
	// EEex-PSTEE: inverse of CGameSprite::MakeGlobal, which Torment has unchanged (tools/fdiff.py: same code,
	// field offsets only); all fields it uses are proven in the Torment header.
	exportPattern(TEXT("CGameSprite::MakeLocal"), getMemberPtr(&CGameSprite::MakeLocal));
}

void __stdcall InitBindings(SharedState argSharedState) {
	sharedState() = argSharedState;
	InitBindingsInternal();
	exportPatterns();
}

void __stdcall OpenBindings() {

	InitLuaBindingsCommon(sharedState());

	// Export lua bindings
	OpenBindingsInternal(luaState());
}
