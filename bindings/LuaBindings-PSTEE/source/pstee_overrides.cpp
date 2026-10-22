// EEex-PSTEE: Torment versions of the "Override_*" engine reimplementations bound to Lua by the generated
// bindings (LuaBindings-Core-Shared-Files/references/source/engine_reimplementations.cpp). EEex's own Lua
// never calls them; they stay available to Lua code as in BG:
//  - Override_AdjustTarget / Override_GetNearest2: EEex's copies of the vanilla routines, which Torment
//    has unchanged -> Torment's own functions;
//  - Override_GetNearest: EEex's reimplementation (vanilla + ignoreDead), with Torment's extra check of the
//    sprite activity flag at +0x3910 (Torment's GetNearest tests it next to m_active / m_activeAI /
//    m_activeImprisonment; cleared during spell cinematics);
//  - Override_GroupSetTarget: Torment's formation code differs from BG's (action ids, formation tables):
//    Torment's own CAIGroup::GroupSetTarget.

#define _USE_MATH_DEFINES
#include <math.h>

#include "Baldur_generated.h"
#include "util.hpp"

// CGameSprite +0x3910, right after m_activeImprisonment (+0x390c), see eeexdll/source/pstee_engine.hpp
static bool isActiveCinematic(const CGameSprite& sprite) {
	return reinterpret_cast<const int*>(&sprite.m_activeImprisonment)[1] != 0;
}

int CGameArea::Override_AdjustTarget(CPoint start, CPoint* goal, byte personalSpace, short tolerance) {
	return this->AdjustTarget(start, goal, personalSpace, tolerance);
}

int CGameArea::Override_GetNearest2(CPoint center, const CAIObjectType* type, short range, const byte* terrainTable,
	int lineOfSight, int seeInvisible, byte nNearest)
{
	return this->GetNearest(center, type, range, terrainTable, lineOfSight, seeInvisible, nNearest);
}

void CAIGroup::Override_GroupSetTarget(CPoint target, int additive, ushort formationType, CPoint cursor) {
	using type_GroupSetTarget = void (__fastcall*)(CAIGroup*, CPoint, int, short, CPoint);
	static type_GroupSetTarget p_GroupSetTarget = []() -> type_GroupSetTarget {
		PatternValueHandle handle;
		if (sharedState().GetPatternValue(TEXT("CAIGroup::GroupSetTarget(CPoint,int,short,CPoint)"), handle) != PatternValueType::SINGLE) {
			FPrintT(TEXT("[!][LuaBindings-PSTEE.dll] CAIGroup::Override_GroupSetTarget() - pattern [CAIGroup::GroupSetTarget(CPoint,int,short,CPoint)] missing\n"));
			return nullptr;
		}
		return reinterpret_cast<type_GroupSetTarget>(sharedState().GetSinglePatternValue(handle));
	}();
	if (p_GroupSetTarget != nullptr) {
		p_GroupSetTarget(this, target, additive, static_cast<short>(formationType), cursor);
	}
}

////////////////////////////////////////////////////////////////////////////////////////////////////////
// Override_GetNearest: EEex's reimplementation (upstream text) + Torment's activity flag              //
////////////////////////////////////////////////////////////////////////////////////////////////////////

enum class CheckNearestShortCircuitCallbackResult
{
	SHORT_CIRCUIT = 0,
	SKIP = 1,
	CONTINUE = 2,
};

typedef CheckNearestShortCircuitCallbackResult(*CheckNearestShortCircuitCallback)(int range, int yDiff);

static CheckNearestShortCircuitCallbackResult checkNearestForwardCallback(int range, int yDiff)
{
	if (yDiff >= 0)
	{
		if (yDiff > range) {
			return CheckNearestShortCircuitCallbackResult::SHORT_CIRCUIT;
		}
	}
	else if (-yDiff > range) {
		return CheckNearestShortCircuitCallbackResult::SKIP;
	}
	return CheckNearestShortCircuitCallbackResult::CONTINUE;
}

static CheckNearestShortCircuitCallbackResult checkNearestBackwardCallback(int range, int yDiff)
{
	if (yDiff < 0)
	{
		if (-yDiff > range) {
			return CheckNearestShortCircuitCallbackResult::SHORT_CIRCUIT;
		}
	}
	else if (yDiff > range) {
		return CheckNearestShortCircuitCallbackResult::SKIP;
	}
	return CheckNearestShortCircuitCallbackResult::CONTINUE;
}

static bool checkNearest(
	// Loop data
	const CheckNearestShortCircuitCallback shortCircuitCallback, int *const idArray, int *const distanceArray, const short nArray,
	// Area data
	CGameArea& area, const byte *const terrainTable,
	// Checking object
	const int objectID,
	// Caller data
	const CAIObjectType& callerType, const CPoint& callerPos, const CPoint& callerPosAdj,
	// Restrictions
	const short range, const int rangeSquared, const CAIObjectType& matchType, const bool bCheckLOS,
	const bool bSeeInvisible, const bool bIgnoreSleeping, const bool bIgnoreDead)
{
	CGameObject* object;
	if (CGameObjectArray::GetShare(objectID, &object) != 0) {
		return false;
	}

	if (object->virtual_GetVertListPos() == nullptr) {
		return false;
	}

	const CPoint& objectPos { object->m_pos };
	const CPoint objectPosAdj { objectPos.x, objectPos.y * 4/3 };

	const int yDiff { objectPosAdj.y - callerPosAdj.y };

	// Short-circuit loop based on the sorted nature of m_lVertSort
	if (CheckNearestShortCircuitCallbackResult result { shortCircuitCallback(range, yDiff) };
		result == CheckNearestShortCircuitCallbackResult::SHORT_CIRCUIT)
	{
		return true;
	}
	else if (result == CheckNearestShortCircuitCallbackResult::SKIP) {
		return false;
	}

	const int distanceSquared { square(objectPosAdj.x - callerPosAdj.x) + square(yDiff) };
	if (distanceSquared > rangeSquared) {
		return false;
	}

	if (object->virtual_GetObjectType() == CGameObjectType::SPRITE)
	{
		CGameSprite& sprite { *reinterpret_cast<CGameSprite*>(object) };
		CDerivedStats& stats { *sprite.GetActiveStats() };
		const uint generalState { stats.m_generalState };

		if (!sprite.m_active || !sprite.m_activeAI || !sprite.m_activeImprisonment || !isActiveCinematic(sprite)
			|| (!bSeeInvisible && ((generalState & 0x10) != 0 || stats.m_bSanctuary))
			|| (bIgnoreSleeping && (generalState & 1) != 0)
			|| (bIgnoreDead && (generalState & 0x800) != 0)
			|| !sprite.m_animation.m_animation->virtual_GetAboveGround()
			|| stats.m_cImmunitiesAIType.OnList(&callerType))
		{
			return false;
		}
	}

	if (!object->virtual_GetAIType()->OfType(&matchType, 0, 0, 0)
		|| (bCheckLOS && !area.CheckLOS(&callerPos, &objectPos, terrainTable, 0, 0)))
	{
		return false;
	}

	for (short i { 0 }; i <= nArray; ++i)
	{
		if (distanceSquared < distanceArray[i])
		{
			const short slotsAfter { nArray - i };
			memmove(&idArray[i + 1], &idArray[i], sizeof(int) * slotsAfter);
			memmove(&distanceArray[i + 1], &distanceArray[i], sizeof(int) * slotsAfter);
			idArray[i] = object->m_id;
			distanceArray[i] = distanceSquared;
			return false;
		}
	}

	return false;
}

int CGameArea::Override_GetNearest(int startObject, const CAIObjectType* type, short range, const byte* terrainTable,
	int checkLOS, int seeInvisible, int ignoreSleeping, byte nNearest, int ignoreDead)
{
	CGameObject* pCaller { };
	if (CGameObjectArray::GetShare(startObject, &pCaller) != 0) {
		return -1;
	}

	if (pCaller->virtual_GetVertListType() != VertListType::LIST_FRONT) {
		return this->GetNearest(pCaller->m_pos, type, range, terrainTable, checkLOS, seeInvisible, nNearest);
	}

	const CTypedPtrList<CPtrList,long>::CNode *const pVertListPos { pCaller->virtual_GetVertListPos() };
	if (pVertListPos == nullptr) {
		return -1;
	}

	const short arraySize { static_cast<short>(nNearest) + 1 };
	int *const idArray { reinterpret_cast<int*>(alloca(sizeof(int) * arraySize * 2)) };
	int *const distanceArray { idArray + arraySize };

	for (short i { 0 }; i <= nNearest; ++i) {
		idArray[i] = -1;
		distanceArray[i] = INT_MAX;
	}

	const CAIObjectType& callerType { *pCaller->virtual_GetAIType() };
	const CPoint& callerPos { pCaller->m_pos };
	const CPoint callerPosAdj { callerPos.x, callerPos.y * 4/3 };

	const int rangeSquared { square(range) };

	CTypedPtrList<CPtrList,long>::CNode* pPrevNode { pVertListPos->pPrev };
	CTypedPtrList<CPtrList,long>::CNode* pNextNode { pVertListPos->pNext };

	while (pPrevNode != nullptr || pNextNode != nullptr)
	{
		if (pPrevNode != nullptr)
		{
			if (checkNearest(
				// Loop data
				checkNearestBackwardCallback, idArray, distanceArray, nNearest,
				// Area data
				*this, terrainTable,
				// // Checking object
				pPrevNode->data,
				// Caller data
				callerType, callerPos, callerPosAdj,
				// Restrictions
				range, rangeSquared, *type, checkLOS, seeInvisible, ignoreSleeping, ignoreDead))
			{
				pPrevNode = nullptr;
			}
			else {
				pPrevNode = pPrevNode->pPrev;
			}
		}

		if (pNextNode != nullptr)
		{
			if (checkNearest(
				// Loop data
				checkNearestForwardCallback, idArray, distanceArray, nNearest,
				// Area data
				*this, terrainTable,
				// // Checking object
				pNextNode->data,
				// Caller data
				callerType, callerPos, callerPosAdj,
				// Restrictions
				range, rangeSquared, *type, checkLOS, seeInvisible, ignoreSleeping, ignoreDead))
			{
				pNextNode = nullptr;
			}
			else {
				pNextNode = pNextNode->pNext;
			}
		}
	}

	const int returnVal { idArray[nNearest] };
	return nNearest == 0 || returnVal != -1
		? returnVal
		: 0;
}
