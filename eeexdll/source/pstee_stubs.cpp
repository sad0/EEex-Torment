// EEex-PSTEE: stand-ins for the EEex.dll reimplementations that EEex never installs (debug.cpp:
// CVidPalette::RealizeResource3d; engine_reimplementations.cpp is not compiled at all): no Lua patch jumps
// to them and they are $nobinding (AUDIT.md). They log once if ever reached.

#include <unordered_set>

#include "debug_window.hpp"
#include "EEex.h"
#include "time_util.hpp"

static void notPorted(const char* name) {
	static std::unordered_set<const char*> reported;
	if (reported.insert(name).second) {
		FPrint("[!][EEex.dll] %s is not ported to Torment.exe yet (EEex-PSTEE); ignored\n", name);
	}
}

#define NOT_PORTED() notPorted(__FUNCTION__)

//------------------------------------//
//  engine_reimplementations / debug  //
//------------------------------------//

void CVidPalette::Override_RealizeResource3d(uint* a, uint b, CVIDIMG_PALETTEAFFECT* c, uint d) { NOT_PORTED(); }
