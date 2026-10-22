# Torment.exe semantic patches for upstream EEex.dll sources. The upstream files under ref/ stay
# untouched; patched copies are written to eeexdll/generated/src/ and compiled instead of them
# (make_vcxproj.py). Every replacement must match exactly once, so upstream changes fail loudly.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, r'..\ref\InfinityLoader\EEex-Core-Shared-Files\source')
OUT = os.path.join(HERE, r'generated\src')

# PSTEE item slots (ITMSLOTS.2DA) keep the BG2EE indices for FIST (10), SPECIAL/magic weapon (34) and
# WEAPONS (35-38), but slot 9 is TATTOO3 and there is no shield / off-hand slot: nothing can attack
# with the left hand.
PATCHES = {
    'EEex.cpp': [
        ("""bool EEex::CanAttackWithLeftHand(CGameSprite* pSprite)
{
""", """bool EEex::CanAttackWithLeftHand(CGameSprite* pSprite)
{
	// EEex-PSTEE: Torment has no off-hand slot (slot 9 is TATTOO3 in ITMSLOTS.2DA)
	return false;
"""),
        ("""	CItem *const pLeftHandItem = this->m_equipment.m_items[9];
	const bool isLeftHand = lastSwing && pLeftHandItem != nullptr && pLeftHandItem->pRes->pHeader->itemType != 12;""",
         """	// EEex-PSTEE: Torment has no off-hand slot (slot 9 is TATTOO3 in ITMSLOTS.2DA)
	const bool isLeftHand = false;"""),
        # Bind Torment-only engine functions before anything else uses them
        ('''void EEex::InitEEex() {
''', '''void EEex::InitEEex() {

	PSTEE::BindEngine();
'''),
        ('''#include "Baldur_generated.h"
''', '''#include "Baldur_generated.h"
#include "pstee_engine.hpp"
'''),
        # op319 (CGameEffectUsability::CheckUsability), Torment rules (PT 0x1ed180): param2 = 8 compares
        # the effective alignment (Nameless One: from the Law/Good globals) and PT adds param2 = 12, a
        # byte of the creature header at +0x87 (BG m_trackingTarget bytes, reused by PSTEE).
        ('''			case 8: {
				match = pAIType->m_Alignment == this->m_effectAmount;
				break;
			}''', '''			case 8: {
				// EEex-PSTEE: Torment compares the effective alignment (PT 0x3c4fe0). The type is passed
				// by value: the callee destroys the copy (its CString), as the engine's caller expects.
				alignas(CAIObjectType) byte aiTypeCopyStorage[sizeof(CAIObjectType)];
				CAIObjectType *const pAITypeCopy = reinterpret_cast<CAIObjectType*>(aiTypeCopyStorage);
				pAITypeCopy->Construct(pAIType);
				match = PSTEE::p_CGameSprite_GetEffectiveAlignment(pSprite, pAITypeCopy) == this->m_effectAmount;
				break;
			}'''),
        ('''				#pragma warning(default:6054)
				break;
			}
		}''', '''				#pragma warning(default:6054)
				break;
			}
			case 12: {
				// EEex-PSTEE: Torment-only mode, creature header byte +0x87
				match = reinterpret_cast<const byte*>(&pSprite->m_baseStats)[0x87] == this->m_effectAmount;
				break;
			}
		}'''),
        # CGameEffect::CheckSave: Torment's saving-throw code differs from BG2EE's (similarity 0.41);
        # EEex's BG reimplementation is replaced by a call to PT's own base implementation.
        ('@body int EEex::Override_CGameEffect_CheckSave(', '''{
	// EEex-PSTEE: forward to Torment's own CGameEffect::CheckSave (PT rules)
	return PSTEE::p_CGameEffect_CheckSave(pEffect, pTarget, saveVSDeathRollRaw, saveVSWandsRollRaw, saveVSPolyRollRaw,
		saveVSBreathRollRaw, saveVSSpellRollRaw, resistMagicRollRaw);
}'''),
        # uiEventMenuStack, Torment version (PT 0x457b40): keyboard/controller navigation first, the overlay
        # menu swallows events, controller button A presses skip stacked menus, and some handled events are
        # still passed to the engine (quit/window, mouse motion, user events, Alt+F4/Enter, Cmd+Q/F/H/M,
        # Ctrl). EEex's capture item lifetime fix is kept.
        ('@body bool __cdecl EEex::Override_uiEventMenuStack(', '''{
	CBaldurChitin *const pChitin = *p_g_pBaldurChitin;

	if (p_uiIsHidden() && pChitin->pActiveEngine == pChitin->m_pEngineWorld) {
		return false;
	}

	// Fix: capture item might be deleted by the event stack processing (see upstream comment)
	exInUseCaptureItemDeleted = false;
	exInUseCaptureItem = p_capture->item;

	bool handled = false;
	int nIndex = getMenuStackTop();

	if (PSTEE::p_uiNavigateEvent(pEvent, pWindow)) {
		handled = true;
	}
	else if (*p_g_overlayMenu != nullptr) {
		p_eventMenu(*p_g_overlayMenu, pEvent, pWindow);
		handled = true;
	}
	else {
		for (uiMenu* pMenu = getStackMenu(nIndex); pMenu != nullptr; pMenu = getStackMenu(--nIndex)) {
			// SDL_CONTROLLERBUTTONDOWN of button 0 (A): not offered to stacked menus (Torment)
			if (static_cast<uint32_t>(pEvent->type) == 0x651 && reinterpret_cast<const byte*>(pEvent)[0xC] == 0) {
				continue;
			}
			if (p_eventMenu(pMenu, pEvent, pWindow)) {
				handled = true;
				break;
			}
		}
	}

	if (handled) {
		// Torment passes these through to the engine even when a menu handled them
		const uint32_t type = static_cast<uint32_t>(pEvent->type);
		if (type > 0x301) {
			if (type == 0x400 || (type >= 0x8003 && type <= 0x8006)) {
				handled = false;
			}
		}
		else if (type >= 0x300) {
			const int32_t sym = static_cast<int32_t>(pEvent->key.keysym.sym);
			const uint16_t mod = static_cast<uint16_t>(pEvent->key.keysym.mod);
			if (sym == 0x40000046 || sym == 0x400000E0 || sym == 0x400000E4) {
				handled = false;
			}
			else if ((sym == 0x4000003D || sym == 0x0D || sym == 0x40000058) && (mod & 0x300) != 0) {
				handled = false;
			}
			else if ((sym == 0x71 || sym == 0x66 || sym == 0x68 || sym == 0x6D) && (mod & 0xC00) != 0) {
				handled = false;
			}
		}
		else if (type == 0x100 || type == 0x200) {
			handled = false;
		}
	}

	if (exInUseCaptureItemDeleted) {
		p_free(exInUseCaptureItem);
	}
	exInUseCaptureItem = nullptr;

	return handled;
}'''),
        # uiDoFile, Torment version (PT 0x456d60): the .lua resource is loaded from its text CString
        # (CResText at +0x58 once demanded) with that string's length, and released with dimmDump.
        ('''		const char *const pResBuffer = reinterpret_cast<char*>(pRes->Demand());

		if (luaL_loadbufferx(L, pResBuffer, pRes->nSize, fullFileName->m_pchData, nullptr) == LUA_OK) {''',
         '''		// EEex-PSTEE: Torment reads the resource text CString (+0x58) and its length
		pRes->Demand();
		alignas(CString) byte resTextStorage[sizeof(CString)];
		CString *const pResText = reinterpret_cast<CString*>(resTextStorage);
		pResText->Construct(reinterpret_cast<const CString*>(reinterpret_cast<const byte*>(pRes) + 0x58));
		const int nResTextLength = *reinterpret_cast<const int*>(pResText->m_pchData - 8);
		const int nLoadResult = luaL_loadbufferx(L, pResText->m_pchData, nResTextLength, fullFileName->m_pchData, nullptr);
		pResText->Destruct();

		if (nLoadResult == LUA_OK) {'''),
        ('''		pRes->virtual_Dump();
	}

	EngineVal<CString> langFile{};''', '''		p_dimmDump(pRes); // EEex-PSTEE: Torment releases the resource with dimmDump
	}

	EngineVal<CString> langFile{};'''),
        # CGameText::Render: Torment's floating-text renderer is a different routine (PT 0x215600: dialog
        # bubbles in Torment mode, fade, cached size, zoom already handled); EEex's override carries BG
        # renderer fixes only. Not to be installed on Torment (phase 5); never runs BG code if reached.
        ('@body void CGameText::Override_Render(', '''{
	// EEex-PSTEE: BG renderer fixes do not apply to Torment's CGameText::Render (see eeexdll/patch_sources.py)
	static bool reported = false;
	if (!reported) {
		reported = true;
		FPrint("[!][EEex.dll] CGameText::Override_Render must not be installed on Torment (EEex-PSTEE); ignored\\n");
	}
}'''),
        # Simulated attack rolls (EEex.GetWeaponHitChance / FakeAttackRoll): Torment's CGameSprite::Hit
        # (PT 0x4147b0) differs from BG2EE's in four places, applied here.
        # 1) Torment-only threshold modifiers right after the luck roll
        ('''	/////////////////////
	// Damage type mod //
	/////////////////////

	int nDamageTypeMod = 0;''', '''	////////////////////////////////////////////
	// EEex-PSTEE: Torment threshold modifiers //
	////////////////////////////////////////////

	{
		// Attacker animation 0x7703 / 0xF04E / 0xF04F vs a PC target: +3 needed while the party has NTOKEN
		const ushort nAnimationID = pThis->m_animation.m_animation->m_animationID;
		if ((nAnimationID == 0x7703 || static_cast<ushort>(nAnimationID + 0x0FB2) <= 1) && target->m_typeAI.m_EnemyAlly == 2)
		{
			CResRef ntoken { "NTOKEN" };
			if (PSTEE::p_CGameAIBase_PartyHasItem(pThis, &ntoken))
			{
				*nTHAC0VsACDiffOut += 3;
			}
		}

		// Undead (non-PC) attacking a PC during the Mortuary truce: +4 needed (global Dead_Truce == 1)
		if (pThis->m_typeAI.m_General == 4 && pThis->m_typeAI.m_EnemyAlly != 2 && target->m_typeAI.m_EnemyAlly == 2)
		{
			// The name is passed by value: the callee destroys it (PT 0x2b4c53 ~CString on the argument), so it is
			// built in raw storage and not destroyed here (a double free corrupted the CString allocator)
			alignas(CString) byte truceNameStorage[sizeof(CString)];
			CString *const pTruceName = reinterpret_cast<CString*>(truceNameStorage);
			CString::p_Construct_Overload_String(pTruceName, "Dead_Truce");
			if (PSTEE::p_CVariableHash_GetValue(&pGame->m_variables, pTruceName, 0) == 1)
			{
				*nTHAC0VsACDiffOut += 4;
			}
		}
	}

	/////////////////////
	// Damage type mod //
	/////////////////////

	int nDamageTypeMod = 0;'''),
        # 2) no attack of opportunity in Torment mode
        ('''	const byte nAbilityType = static_cast<byte>(pEffectiveWeaponAbility->type);
	const bool bAllowAttackOfOpportunity = nAbilityType != 2 && nAbilityType != 4 && (pThis->m_equipment.m_selectedWeapon != 10 || pThis->virtual_GetAIType()->m_Class == 20);

	if (bAllowAttackOfOpportunity && target->m_equipment.m_selectedWeapon == 10 && target->virtual_GetAIType()->m_Class != 20)''', '''	const byte nAbilityType = static_cast<byte>(pEffectiveWeaponAbility->type);
	const bool bAllowAttackOfOpportunity = nAbilityType != 2 && nAbilityType != 4 && (pThis->m_equipment.m_selectedWeapon != 10 || pThis->virtual_GetAIType()->m_Class == 20);

	if (static_cast<int>(*CChitin::p_ENGINE_MODE) == PSTEE::ENGINE_MODE_PST)
	{
		// EEex-PSTEE: Torment skips the attack of opportunity entirely (no feedback either)
		*sFormatString = "";
	}
	else if (bAllowAttackOfOpportunity && target->m_equipment.m_selectedWeapon == 10 && target->virtual_GetAIType()->m_Class != 20)'''),
        # 3) state bit 22 does not make the target count as invisible in Torment mode
        ('''	if (!pThis->virtual_GetCanSeeInvisible() && ((target->GetActiveStats()->m_generalState & 0x10) != 0 || (target->GetActiveStats()->m_generalState & 0x400000) != 0))''',
         '''	if (!pThis->virtual_GetCanSeeInvisible() && ((target->GetActiveStats()->m_generalState & 0x10) != 0
		|| (static_cast<int>(*CChitin::p_ENGINE_MODE) != PSTEE::ENGINE_MODE_PST && (target->GetActiveStats()->m_generalState & 0x400000) != 0)))'''),
        # 4) Fist of Iron: +3 to the roll after the hated race bonus
        ('''		*sFormatString = " +Hated Race:0";
	}

	*sFeedbackString += sFormatString;''', '''		*sFormatString = " +Hated Race:0";
	}

	*sFeedbackString += sFormatString;

	//////////////////////////////////
	// EEex-PSTEE: Torment Fist of Iron //
	//////////////////////////////////

	{
		const int nFistOfIron = PSTEE::p_CGameSprite_HasFistOfIron(pThis) ? 3 : 0;
		nCurModifiedAttackRoll.intVal += nFistOfIron;
		sFormatString->Format(" +Fist of Iron:%d", nFistOfIron);
		*sFeedbackString += sFormatString;
	}'''),
        # Hand bonus breakdown: m_hitBonusesRight/Left are CStrings (the engine appends "(" text ")");
        # upstream EEex formats them with %d (prints an address).
        ('''		sFormatString->Format(" +Right:%d (%d)", static_cast<short>(pThis->GetActiveStats()->m_THAC0BonusRight), pThis->m_hitBonusesRight);''',
         '''		sFormatString->Format(" +Right:%d (%s)", static_cast<short>(pThis->GetActiveStats()->m_THAC0BonusRight), pThis->m_hitBonusesRight.m_pchData);'''),
        ('''		sFormatString->Format(" +Left:%d (%d)", static_cast<short>(pThis->GetActiveStats()->m_THAC0BonusLeft), pThis->m_hitBonusesLeft);''',
         '''		sFormatString->Format(" +Left:%d (%s)", static_cast<short>(pThis->GetActiveStats()->m_THAC0BonusLeft), pThis->m_hitBonusesLeft.m_pchData);'''),
        # Torment's target searches (CGameArea::GetNearest, ...) also skip sprites whose PT-only activity flag
        # (+0x3910, cleared during spell cinematics) is 0: MatchObject follows the engine
        ('''		if (!sprite.m_active || !sprite.m_activeAI || !sprite.m_activeImprisonment
''', '''		if (!sprite.m_active || !sprite.m_activeAI || !sprite.m_activeImprisonment || !PSTEE::IsActiveCinematic(sprite)
'''),
        # Torment has no CDerivedStats::m_disableSpells (op145 only knows the three spell-type flags)
        ('''		stats.m_disableSpells != exData.oldDisableSpells
		||
		!std::equal(''', '''		!std::equal('''),
        ('''		exData.oldDisableSpells = stats.m_disableSpells;
''', ''),
        # Torment's CAIScript constructor has no player-script argument (PSTEE::NewScript re-reads with the flag)
        ('? newEngineObj<CAIScript>(pEffect->m_res, 0)', '? newEngineObj<CAIScript>(pEffect->m_res)'),
        ('? newEngineObj<CAIScript>(pEffect->m_res2, pEffect->m_effectAmount2)', '? PSTEE::NewScript(pEffect->m_res2, pEffect->m_effectAmount2 != 0)'),
        # WSPECIAL.2DA has no SPEED column in Torment (HIT, DAMAGE only): EEex's BG fix does not apply.
        ('@body void EEex::Fix_Hook_ImplementWSPECIALSpeedColumn(', '''{
	// EEex-PSTEE: Torment's WSPECIAL.2DA has no SPEED column (HIT, DAMAGE); nothing to implement
}'''),
    ],
    'uncap_fps.cpp': [
        ('#include "EEex.h"\n', '#include "EEex.h"\n#include "pstee_engine.hpp"\n'),
        # --- CChitin::WinMain / InitInstance (PT 0x4a65c0): SDL hint, frame rate 40 in [10,90], no frame-time log
        ('''	p_SDL_Log("%s %s\\n", CChitin::p_m_sGameName->m_pchData, sVersion->m_pchData);
''', '''	p_SDL_Log("%s %s\\n", CChitin::p_m_sGameName->m_pchData, sVersion->m_pchData);

	// EEex-PSTEE: Torment disables Alt+F4 window closing by SDL (handled by the engine)
	if (PSTEE::p_SDL_SetHint != nullptr)
	{
		PSTEE::p_SDL_SetHint("SDL_WINDOWS_NO_CLOSE_ON_ALT_F4", "1");
	}
'''),
        ('''	*CChitin::p_TIMER_UPDATES_PER_SECOND = p_BGGetPrivateProfileInt("Program Options", "Maximum Frame Rate", 30);

	if (*CChitin::p_TIMER_UPDATES_PER_SECOND > 90)
	{
		*CChitin::p_TIMER_UPDATES_PER_SECOND = 30;
	}
''', '''	// EEex-PSTEE: Torment's default is 40 and any value outside [10, 90] falls back to it
	const int nMaxFrameRate = p_BGGetPrivateProfileInt("Program Options", "Maximum Frame Rate", 40);
	*CChitin::p_TIMER_UPDATES_PER_SECOND = static_cast<uint>(nMaxFrameRate - 10) > 80 ? 40 : nMaxFrameRate;
'''),
        ('@cut	const int nLogFrameTimes = p_BGGetPrivateProfileInt("Graphics", "Log Frame Times", 0);', '	if (nLogFrameTimes == 2)'),
        ('''	if (nLogFrameTimes == 2)
	{
		pThis->m_bLogFrames = 1;
	}

''', '''	// EEex-PSTEE: Torment has no frame-time log ("Log Frame Times")

'''),
        # --- CChitin::Update (PT 0x4a6350): the Lua stack is emptied after the leak dump; no frame-time log
        ('''	const TimeType nStartTime = getTime();

	// Patch: Run "full ticks" at 30tps like normal''', '''	// EEex-PSTEE: Torment empties the leaked values after printing them
	if (const int nTop = lua_gettop(L); nTop > 0)
	{
		lua_settop(L, -1 - nTop);
	}

	const TimeType nStartTime = getTime();

	// Patch: Run "full ticks" at 30tps like normal'''),
        ('@cut		/////////////////////\n		// Log frame times //', '	}\n\n	// NOT ELSE IF'),
        # --- CInfinity::AdjustViewPosition (PT 0x302090)
        ('''	const int nSpeedBase = static_cast<int>(
		static_cast<float>(*CVidMode::p_SCREENHEIGHT)         // Internal resolution height
		/ pChitin->cVideo.pCurrentMode->nHeight               // Window height
		/ (*CInfinity::p_MAXZOOM_OUT + 1.0f - fEffectiveZoom) // Zoom factor
		* pGame->GetScrollSpeed());                           // Scroll speed
''', '''	// EEex-PSTEE: Torment's speed has no resolution factor; m_nScrollDelay (keyboard scroll ramp-up)
	// scales the option speed by (15 - delay) / 15
	uint nScrollSpeed = pGame->GetScrollSpeed();
	if (pInfinity->m_nScrollDelay != 0)
	{
		nScrollSpeed = nScrollSpeed * (15 - pInfinity->m_nScrollDelay) / 15;
	}
	float fSpeedBase = *CInfinity::p_MAXZOOM_OUT / (*CInfinity::p_MAXZOOM_OUT + 1.0f - fEffectiveZoom);
	fSpeedBase /= *CInfinity::p_MAXZOOM_OUT;
	const int nSpeedBase = static_cast<int>(fSpeedBase * static_cast<int>(nScrollSpeed));
'''),
        ('''	// Patch: Allow theoretical movement
	// |
	if (pExOverrides == nullptr)
	{
		// Stop auto scrolling
		pInfinity->m_ptScrollDest.x = -1;
		pInfinity->m_ptScrollDest.y = -1;
	}

	CBaldurChitin *const pChitin = *p_g_pBaldurChitin;''', '''	CBaldurChitin *const pChitin = *p_g_pBaldurChitin;

	// EEex-PSTEE: in Torment mode the view does not move while it is locked on a creature
	if (static_cast<int>(*CChitin::p_ENGINE_MODE) == PSTEE::ENGINE_MODE_PST && pChitin->m_pEngineWorld->m_scrollLockId != -1)
	{
		return;
	}

	// Patch: Allow theoretical movement
	// |
	if (pExOverrides == nullptr)
	{
		// Stop auto scrolling
		pInfinity->m_ptScrollDest.x = -1;
		pInfinity->m_ptScrollDest.y = -1;
	}
'''),
        # --- CVidTile::RenderTexture (PT 0x4aed20): no grey tone flag
        ('''	DrawTone drawTone = (dwFlags & 0x80000) != 0 ? DrawTone::DRAW_TONE_GREY : DrawTone::DRAW_TONE_NORMAL;''',
         '''	// EEex-PSTEE: Torment's tile renderer ignores the grey flag (dwFlags 0x80000)
	DrawTone drawTone = DrawTone::DRAW_TONE_NORMAL;'''),
        # --- ZoomToMap / ResetZoom: Torment's "Disable Area Map Zoom" option (inverted, other field)
        ('@all:2 pGame->m_options.m_bAreaMapZoom == 0', 'PSTEE::IsAreaMapZoomDisabled(pGame->m_options)'),
        # --- CInfinity::FitViewPosition (PT 0x304c20): Torment margins, scroll lock, centered-axis scroll state
        ('@body static void fitViewPosition(CInfinity* pInfinity, int* pX, int* pY, CRect* pViewPort,',
         open(os.path.join(HERE, 'source', 'pstee_fitviewposition.inc'), encoding='utf-8').read()),
        ('''	bool bWorldQuicklootOpen = false;
''', '''	bool bWorldQuicklootOpen = false;
	bool bWorldActionbarLeftOpen = false; // EEex-PSTEE: Torment-mode actionbar (WORLD_ACTIONBAR_LEFT[_TABLET])
'''),
        ('''	beforeWorldScreenDeactivatedMenuStates.bWorldQuicklootOpen = p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_QUICKLOOT" });
''', '''	beforeWorldScreenDeactivatedMenuStates.bWorldQuicklootOpen = p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_QUICKLOOT" });
	beforeWorldScreenDeactivatedMenuStates.bWorldActionbarLeftOpen = p_uiIsMenuOnStack(EngineVal<CString, false>{
		PSTEE::UseTouchActionbar((*p_g_pBaldurChitin)->m_pObjectGame->m_options) ? "WORLD_ACTIONBAR_LEFT_TABLET" : "WORLD_ACTIONBAR_LEFT" });
'''),
        # --- zoomOutToLocalMap (CScreenWorld::ZoomToMap, PT 0x3686e0): in Torment mode the map is fitted into
        #     the AREA_MAP_TARGET screen rect (Infinity_GetAreaScreen) instead of above AREA_MAP_BACKGROUND
        ('''	const float fViewPortWidthPercentOfArea = static_cast<short>(pInfinity->nAreaX) / static_cast<float>(nViewPortWidth);
	const float fViewPortHeightPercentOfArea = static_cast<short>(pInfinity->nAreaY) / (nViewPortHeight - nAreaMapBackgroundHeight * pInfinity->m_fZoom);
''', '''	// EEex-PSTEE: Torment mode fits the area into AREA_MAP_TARGET's screen rect (x, y, w, h)
	const bool bTormentMapTarget = static_cast<int>(*CChitin::p_ENGINE_MODE) == PSTEE::ENGINE_MODE_PST;
	int nMapTargetX = 0;
	int nMapTargetY = 0;
	float fMapTargetW = 0.0f;
	float fMapTargetH = 0.0f;

	if (bTormentMapTarget)
	{
		lua_getglobal(L, "Infinity_GetAreaScreen");
		lua_pushstring(L, "AREA_MAP_TARGET");
		lua_callk(L, 1, 4, 0, nullptr);
		fMapTargetH = static_cast<float>(lua_tonumberx(L, -1, nullptr));
		fMapTargetW = static_cast<float>(lua_tonumberx(L, -2, nullptr));
		nMapTargetY = static_cast<int>(lua_tonumberx(L, -3, nullptr));
		nMapTargetX = static_cast<int>(lua_tonumberx(L, -4, nullptr));
		lua_settop(L, -5);
	}

	const float fViewPortWidthPercentOfArea = bTormentMapTarget
		? static_cast<short>(pInfinity->nAreaX) / (fMapTargetW * pInfinity->m_fZoom)
		: static_cast<short>(pInfinity->nAreaX) / static_cast<float>(nViewPortWidth);
	const float fViewPortHeightPercentOfArea = bTormentMapTarget
		? static_cast<short>(pInfinity->nAreaY) / (fMapTargetH * pInfinity->m_fZoom)
		: static_cast<short>(pInfinity->nAreaY) / (nViewPortHeight - nAreaMapBackgroundHeight * pInfinity->m_fZoom);
'''),
        ('''	const CPoint ptTarget {
		static_cast<short>(pInfinity->nAreaX) / 2,
		static_cast<short>(pInfinity->nAreaY) / 2 - static_cast<int>(nAreaMapBackgroundHeight * 0.5f * fViewPortPercentOfArea * pInfinity->m_fZoom)
	};
''', '''	// EEex-PSTEE: Torment mode centres the area on AREA_MAP_TARGET (PT 0x3689da..0x368a5a)
	const CPoint ptTarget = bTormentMapTarget
		? CPoint {
			static_cast<int>((static_cast<short>(pInfinity->nAreaX) / 2) - fMapTargetW * 0.5f * fViewPortPercentOfArea)
				+ static_cast<int>((*CVidMode::p_SCREENWIDTH / 2 - nMapTargetX) * fViewPortPercentOfArea),
			static_cast<int>((static_cast<short>(pInfinity->nAreaY) / 2) - fMapTargetH * 0.5f * fViewPortPercentOfArea)
				+ static_cast<int>((*CVidMode::p_SCREENHEIGHT / 2 - nMapTargetY) * fViewPortPercentOfArea) }
		: CPoint {
			static_cast<short>(pInfinity->nAreaX) / 2,
			static_cast<short>(pInfinity->nAreaY) / 2 - static_cast<int>(nAreaMapBackgroundHeight * 0.5f * fViewPortPercentOfArea * pInfinity->m_fZoom) };
'''),
        # --- CScreenWorld::EndDialog (PT 0x357830): zoom lock re-applied; UI reset outside the store screen only
        ('''	////////////////
	// End dialog //
	////////////////
''', '''	// EEex-PSTEE: with "Zoom Lock" Torment disables zooming again once the dialog view is restored (PT 0x357c07)
	if (pGame->m_options.m_bZoomLock && PSTEE::p_CInfinity_SetZoomEnabled != nullptr)
	{
		PSTEE::p_CInfinity_SetZoomEnabled(&pGame->m_gameAreas[pGame->m_visibleArea]->m_cInfinity, 0);
	}

	////////////////
	// End dialog //
	////////////////
'''),
        ('''	if
	(
		p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_DIALOG" })
		&&
		(
			pChitin->pActiveEngine != pChitin->m_pEngineCreateChar
			||
			pChitin->m_pEngineCreateChar->virtual_GetEngineState() != 6
		)
	)
	{
		p_uiPop("WORLD_DIALOG");
		p_uiPush("WORLD_ACTIONBAR");

		if (p_uiIsMenuOnStack(EngineVal<CString, false>{ "JOURNAL" }))
		{
			p_uiPop("JOURNAL");
			p_uiPush("JOURNAL");
		}
	}
''', '''	// EEex-PSTEE: Torment swaps the dialog panel for the actionbar unless the store screen is active
	// (no WORLD_DIALOG / JOURNAL checks, PT 0x357c96)
	if (pChitin->pActiveEngine != pChitin->m_pEngineStore)
	{
		p_uiPop("WORLD_DIALOG");
		p_uiPush("WORLD_ACTIONBAR");
	}
'''),
        # --- uiDrawMenuStack (PT 0x456f60): tooltip switched off below the delay; menus drawn in Torment's UI rect
        ('''	if
	(
		(!pChitin->m_bIsTouchUI || *p_fingerDown)
		&&
		nTooltipDelay != 99 && nCurTime >= nTooltipEnableTime
	)
	{
		p_tooltip->on = true;
	}
''', '''	// EEex-PSTEE: Torment also switches the tooltip off while the delay has not elapsed (or tooltips are off)
	if (nTooltipDelay == 99 || nCurTime < nTooltipEnableTime)
	{
		p_tooltip->on = false;
	}
	else if (!pChitin->m_bIsTouchUI || *p_fingerDown)
	{
		p_tooltip->on = true;
	}
'''),
        ('''	const SDL_Rect rWindow { 0, 0, *CVidMode::p_SCREENWIDTH, *CVidMode::p_SCREENHEIGHT };
''', '''	// EEex-PSTEE: Torment draws the menus inside its UI rect (screen inset by CChitin's UI edge fraction)
	SDL_Rect rWindow { 0, 0, *CVidMode::p_SCREENWIDTH, *CVidMode::p_SCREENHEIGHT };
	if (PSTEE::p_CChitin_GetUIRect != nullptr && PSTEE::p_g_pChitin != nullptr)
	{
		PSTEE::p_CChitin_GetUIRect(*PSTEE::p_g_pChitin, &rWindow);
	}
'''),
        # --- middle-mouse drag (CScreenWorld::OnEvent PT 0x35ba23): Torment converts the motion deltas from
        #     window to internal screen pixels first
        ('''	if (EEex::UncapFPS_RemoveMiddleMouseScrollMultiplier)
	{
		CPoint exactWorldCoordinateSpacePoint;
		cursorToExactWorldCoordinateSpace(pInfinity, pEvent->motion.xrel, pEvent->motion.yrel, &exactWorldCoordinateSpacePoint);
''', '''	// EEex-PSTEE: motion deltas in internal screen pixels, as Torment computes them
	CPoint motion { pEvent->motion.xrel, pEvent->motion.yrel };
	if (PSTEE::p_CVidMode_WindowToScreen != nullptr)
	{
		CVidMode *const pVidMode = pChitin->cVideo.pCurrentMode;
		PSTEE::p_CVidMode_WindowToScreen(pVidMode, &motion, pVidMode->m_nScreenScrollX + pEvent->motion.xrel, pVidMode->m_nScreenScrollY + pEvent->motion.yrel);
	}

	if (EEex::UncapFPS_RemoveMiddleMouseScrollMultiplier)
	{
		CPoint exactWorldCoordinateSpacePoint;
		cursorToExactWorldCoordinateSpace(pInfinity, motion.x, motion.y, &exactWorldCoordinateSpacePoint);
'''),
        ('''		pInfinity->m_ptCurrentPosExact.x -= static_cast<int>(pEvent->motion.xrel * 10000 * pInfinity->m_fZoom);
		pInfinity->m_ptCurrentPosExact.y -= static_cast<int>(pEvent->motion.yrel * 10000 * pInfinity->m_fZoom);
''', '''		pInfinity->m_ptCurrentPosExact.x -= static_cast<int>(motion.x * 10000 * pInfinity->m_fZoom);
		pInfinity->m_ptCurrentPosExact.y -= static_cast<int>(motion.y * 10000 * pInfinity->m_fZoom);
'''),
        # --- Torment's CInfinity::SetZoom(float, bool bForce): EEex's calls are the vanilla non-forced ones
        ('@all:1 pInfinity->SetZoom(pScreenWorld->m_fTargetZoom);', 'pInfinity->SetZoom(pScreenWorld->m_fTargetZoom, false);'),
        ('@all:1 pInfinity->SetZoom(pScreenWorld->m_fOriginalZoom);', 'pInfinity->SetZoom(pScreenWorld->m_fOriginalZoom, false);'),
        ('@all:1 pInfinity->SetZoom(fNewZoom);', 'pInfinity->SetZoom(fNewZoom, false);'),
        # --- CInfinity::SetScrollDest (PT 0x309450): no clamping while a spell cinematic drives the camera
        ('''	int nFitX = this->m_ptScrollDest.x;
	int nFitY = this->m_ptScrollDest.y;
	fitViewPosition(this, &nFitX, &nFitY, &pInfinity->rViewPort, nullptr, true);''', '''	// EEex-PSTEE: Torment's spell cinematics move the camera freely (CInfinity+0x45c)
	if (PSTEE::IsCinematicCamera(*this))
	{
		return;
	}

	int nFitX = this->m_ptScrollDest.x;
	int nFitY = this->m_ptScrollDest.y;
	fitViewPosition(this, &nFitX, &nFitY, &pInfinity->rViewPort, nullptr, true);'''),
        # --- CInfinity::Scroll (PT 0x3084d0): no m_nScrollAttempts failsafe (field absent)
        ('''	// Vanilla bug: This failsafe can't be triggered due to `m_nScrollAttempts` being immediately reset
	if (nOldX == this->nNewX && nOldY == this->nNewY && this->m_nScrollAttempts++ == 10)
	{
		this->m_ptScrollDest.x = -1;
		this->m_ptScrollDest.y = -1;
	}

	this->m_nScrollAttempts = 0;
''', '''	// EEex-PSTEE: Torment has no scroll-attempts failsafe (CInfinity::m_nScrollAttempts does not exist)
'''),
    ],
    'visibility_map.cpp': [
        ('#include "EEex.h"\n', '#include "EEex.h"\n#include "pstee_engine.hpp"\n'),
        # Torment's sprite update spreading mask is 7 (BG 1): vanilla CheckIfVisible keeps a sprite seen for
        # (mask + 1) * 4 = 32 ticks; BG's 8 makes every creature blink between two checks
        ('@all:4 this->m_canBeSeen = 8;', 'this->m_canBeSeen = PSTEE::CanBeSeenTicks();'),
    ],
}

os.makedirs(OUT, exist_ok=True)
for name, reps in PATCHES.items():
    s = open(os.path.join(SRC, name), encoding='utf-8-sig').read()
    for old, new in reps:
        if old.startswith('@cut'):
            # remove the text from this start marker (inclusive) to the end marker `new` (exclusive)
            start = old[len('@cut'):]
            if s.count(start) != 1 or s.count(new) < 1:
                raise SystemExit(f'{name}: cut markers not found: {start!r} .. {new!r}')
            i = s.index(start); j = s.index(new, i)
            s = s[:i] + s[j:]
            continue
        if old.startswith('@all:'):
            # replace every occurrence; the expected count guards against upstream changes
            cnt, old = old[len('@all:'):].split(' ', 1)
            if s.count(old) != int(cnt):
                raise SystemExit(f'{name}: expected {cnt} matches, found {s.count(old)}: {old}')
            s = s.replace(old, new)
            continue
        if old.startswith('@body '):
            # replace the whole body of the function whose definition starts with this signature
            sig = old[len('@body '):]
            if s.count(sig) != 1:
                raise SystemExit(f'{name}: function signature matches {s.count(sig)} times: {sig}')
            i = s.index(sig); j = s.index('{', i); depth = 0
            for k in range(j, len(s)):
                depth += s[k] == '{'; depth -= s[k] == '}'
                if depth == 0:
                    break
            s = s[:j] + new + s[k + 1:]
            continue
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{name}: patch matches {n} times:\n{old}')
        s = s.replace(old, new)
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n').write(
        f'// GENERATED by eeexdll/patch_sources.py from ref/InfinityLoader/EEex-Core-Shared-Files/source/{name}\n' + s)
    print(name, len(reps), 'patches')
