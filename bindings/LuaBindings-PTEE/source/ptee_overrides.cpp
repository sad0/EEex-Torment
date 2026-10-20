// EEex-PTEE: stand-ins for the BG "Override_*" engine reimplementations
// (LuaBindings-Core-Shared-Files/references/source/engine_reimplementations.cpp).
// Those reimplement BG engine code against BG field layouts, so they are not built for Torment.
// Where Torment has the original engine function bound, forward to it; otherwise do nothing and
// report it. EEex only routes engine calls here once its Lua patches are ported (phase 5).

#include "Baldur_generated.h"

static void reportUnported(const TCHAR* name) {
	FPrintT(TEXT("[!][LuaBindings-PTEE.dll] %s() is not ported to Torment.exe yet\n"), name);
}

int CGameArea::Override_AdjustTarget(CPoint start, CPoint* goal, byte personalSpace, short tolerance) {
	return this->AdjustTarget(start, goal, personalSpace, tolerance);
}

int CGameArea::Override_GetNearest2(CPoint center, const CAIObjectType* type, short range, const byte* terrainTable,
	int lineOfSight, int seeInvisible, byte nNearest)
{
	return this->GetNearest(center, type, range, terrainTable, lineOfSight, seeInvisible, nNearest);
}

int CGameArea::Override_GetNearest(int startObject, const CAIObjectType* type, short range, const byte* terrainTable,
	int checkLOS, int seeInvisible, int ignoreSleeping, byte nNearest, int ignoreDead)
{
	reportUnported(TEXT("CGameArea::Override_GetNearest"));
	return -1;
}

void CAIGroup::Override_GroupSetTarget(CPoint target, int additive, ushort formationType, CPoint cursor) {
	reportUnported(TEXT("CAIGroup::Override_GroupSetTarget"));
}
