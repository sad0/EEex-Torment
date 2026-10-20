
#include "Baldur_generated.h"
#include "EEexLua_generated.h"

static void exportPattern(const String& name, void* value) {

	PatternValueHandle handle;
	if (sharedState().GetOrCreatePatternValue(name, PatternValueType::SINGLE, handle)) {
		FPrintT(TEXT("[!][LuaBindings-PTEE.dll] exportPattern() - [%s].Type must be SINGLE\n"), name.c_str());
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
	// EEex-PTEE: CGameSprite::MakeLocal is a BG reimplementation (BG field layout); not exported for Torment.
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
