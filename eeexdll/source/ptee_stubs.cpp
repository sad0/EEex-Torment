// EEex-PTEE: stand-ins for EEex.dll code that reimplements BG engine functions and is not ported
// to Torment.exe yet (uncap_fps.cpp, visibility_map.cpp, engine_reimplementations.cpp, debug.cpp).
// Those files rewrite engine routines (render loop, scrolling, fog of war, tint, palettes) against
// BG code paths and BG field layouts; PTEE changed several of these routines, so they must be
// re-derived from Torment's own code before being enabled.
//
// Until then:
//  - pure utilities with no engine dependency are reproduced as-is (GetMicroseconds, OpenDebugWindow);
//  - every reimplementation/hook entry point logs once and does nothing (or returns a neutral value).
// These entry points are only reached when EEex's Lua patches redirect engine code to them (phase 5).

#include <unordered_set>

#include "debug_window.hpp"
#include "EEex.h"
#include "time_util.hpp"

static void notPorted(const char* name) {
	static std::unordered_set<const char*> reported;
	if (reported.insert(name).second) {
		FPrint("[!][EEex.dll] %s is not ported to Torment.exe yet (EEex-PTEE); ignored\n", name);
	}
}

#define NOT_PORTED() notPorted(__FUNCTION__)

//----------------------//
//  uncap_fps.cpp       //
//----------------------//

void initUncapFPS() {
	EEex::UncapFPS_LuaGCSteps = 50;
}

TimeType EEex::GetMicroseconds() {
	return getTime() - getInitTime();
}

void EEex::OpenDebugWindow() {
	if (!IsDebugWindowOpen()) {
		CreateDebugWindow();
	}
}

void EEex::OnTargetExecutableInitialized() {}

void EEex::SetUncapFPSEnabled(bool bEnabled) { if (bEnabled) NOT_PORTED(); }
void EEex::SetVSyncEnabled(bool bEnable, bool bResetDevice) { NOT_PORTED(); }
void EEex::UpdateLastScrollTime() {}

void EEex::Fix_Hook_HandleMiddleMouseDrag(SDL_Event* pEvent) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnAfterAreaActivated(CGameArea* pArea) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnAfterAreaEdgeScrollPossiblyStarted(CGameArea* pArea) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnAfterDrawInit() { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnAfterWindowResized() { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnBeforeAreaDeactivated(CGameArea* pArea) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnBeforeAreaRendered() { NOT_PORTED(); }
void EEex::UncapFPS_Hook_OnBeforeWorldScreenDeactivated() { NOT_PORTED(); }
void EEex::UncapFPS_Hook_HandleScreenShake(CInfinity* pInfinity) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_HandleScreenShakePost(CInfinity* pInfinity) { NOT_PORTED(); }
void EEex::UncapFPS_Hook_HandleTransitionMenuFade() { NOT_PORTED(); }

void EEex::Override_DrawReadPixels(int x, int y, int width, int height, byte* pixels) { NOT_PORTED(); }
int __cdecl EEex::Override_Infinity_TransitionMenu(lua_State* L) { NOT_PORTED(); return 0; }
void __cdecl EEex::Override_uiDrawMenuStack() { NOT_PORTED(); }

int CChitin::Override_WinMain() { NOT_PORTED(); return 0; }
void CChitin::Override_Update() { NOT_PORTED(); }
void CInfinity::Override_AdjustViewPosition(byte nScrollState) { NOT_PORTED(); }
void CInfinity::Override_FitViewPosition(int* x, int* y, CRect* rViewPort) { NOT_PORTED(); }
void CInfinity::Override_Scroll(CPoint ptDest, short speed) { NOT_PORTED(); }
void CInfinity::Override_SetScreenShake(int duration, ushort magnitude, CPoint* direction) { NOT_PORTED(); }
void CInfinity::Override_SetScrollDest(CPoint* ptDest) { NOT_PORTED(); }
void CScreenMap::Override_CenterViewPort(CPoint* pt) { NOT_PORTED(); }
void CScreenWorld::Override_EndDialog(byte bForceExecution, byte fullEnd) { NOT_PORTED(); }
void CScreenWorld::Override_ResetZoom() { NOT_PORTED(); }
void CScreenWorld::Override_StartScroll(CPoint dest, short speed) { NOT_PORTED(); }
void CScreenWorld::Override_ZoomToMap(bool bZoomOut) { NOT_PORTED(); }
void CGameArea::Override_RenderZoomed() { NOT_PORTED(); }
void CVidTile::Override_RenderTexture(int a, CRect* b, int c, int d, uint e) { NOT_PORTED(); }

//------------------------------------//
//  engine_reimplementations / debug  //
//------------------------------------//

void CVidPalette::Override_RealizeResource3d(uint* a, uint b, CVIDIMG_PALETTEAFFECT* c, uint d) { NOT_PORTED(); }
