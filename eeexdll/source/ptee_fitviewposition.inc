{
	// EEex-PTEE: Torment's CInfinity::FitViewPosition (PT 0x304c20) decides the allowed out-of-bounds margins
	// differently from BG2EE; EEex's structure (exact coordinates, theoretical fits, scroll destination,
	// edge-scroll-only cursor reset) is kept, the margins and the end-of-fit cursor handling follow Torment:
	//  - black space is shown when the option is on OR while the world screen auto-zooms;
	//  - with black space the margin is half the viewport on every side (no sidebar / actionbar margins);
	//  - otherwise left/right margins are the sidebar widths, the bottom margin the actionbar height: in
	//    Torment mode WORLD_ACTIONBAR_LEFT (or _TABLET with "Use Touch Actionbar"), else WORLD_ACTIONBAR plus
	//    the dialog or messages panel; the actionbar only counts outside the map screen;
	//  - no cursor reset while the view is locked on a creature (CScreenWorld::m_scrollLockId);
	//  - when an axis is centered (area smaller than the viewport) its edge-scroll direction is removed.
	lua_State *const L = *p_g_lua;
	CBaldurChitin *const pChitin = *p_g_pBaldurChitin;
	CInfGame *const pGame = pChitin->m_pObjectGame;
	CScreenWorld *const pWorld = pChitin->m_pEngineWorld;

	const bool bShowBlackSpace = pGame->m_options.m_bShowBlackSpace || pWorld->m_bAutoZooming;
	const int nViewPortWidth = pViewPort->right - pViewPort->left;
	const int nViewPortHeight = pViewPort->bottom - pViewPort->top;

	bool bSetNoScrollCursor = false;
	bool bCenteredX = false;
	bool bCenteredY = false;

	const float fEffectiveZoom = pMenuStateOverrides == nullptr ? pInfinity->m_fZoom : pMenuStateOverrides->fZoom;

	// Infinity_GetArea(name) -> x, y, w, h; nResult: 3 = w, 4 = h (same stack handling as Torment)
	const auto getAreaValue = [&](const char* sName, int nResult) -> lua_Number
	{
		lua_getglobal(L, "Infinity_GetArea");
		lua_pushstring(L, sName);
		lua_callk(L, 1, 4, 0, nullptr);
		lua_settop(L, nResult - 5);
		const lua_Number nValue = lua_tonumberx(L, -1, nullptr);
		lua_settop(L, -nResult - 1);
		return nValue;
	};

	//////////////////////////////////////
	// Calculate allowed horizontal OOB //
	//////////////////////////////////////

	int nAllowedOOBLeft = 0;
	int nAllowedOOBRight = 0;

	if (bShowBlackSpace)
	{
		nAllowedOOBLeft = nViewPortWidth / 2;
		nAllowedOOBRight = nAllowedOOBLeft;
	}
	else if (!p_uiIsHidden())
	{
		if (p_uiIsMenuOnStack(EngineVal<CString, false>{ "LEFT_SIDEBAR" }))
		{
			nAllowedOOBLeft = static_cast<int>(getAreaValue("leftSidebarBackground", 3) * fEffectiveZoom + 0.0);
		}

		if (p_uiIsMenuOnStack(EngineVal<CString, false>{ "RIGHT_SIDEBAR" }))
		{
			nAllowedOOBRight = static_cast<int>(getAreaValue("rightSidebarBackground", 3) * fEffectiveZoom + 0.0);
		}
	}

	////////////////
	// Check left //
	////////////////

	const int nAllowedWidth = pInfinity->nAreaX + nAllowedOOBLeft + nAllowedOOBRight;

	if (nViewPortWidth > nAllowedWidth)
	{
		// Center
		const int nNewX = (nAllowedWidth - nViewPortWidth) / 2 - nAllowedOOBLeft;

		if (*pX != nNewX)
		{
			// Snap - Viewport width too large
			*pX = nNewX;

			if (!bTheoretical)
			{
				pInfinity->m_ptCurrentPosExact.x = *pX * 10000;
				bCenteredX = true;

				if (pInfinity->m_ptScrollDest.x != -1)
				{
					pInfinity->m_ptScrollDest.x = *pX;
				}
			}
		}
	}
	else if (*pX < -nAllowedOOBLeft)
	{
		// Snap - x too far left
		*pX = -nAllowedOOBLeft;

		if (!bTheoretical)
		{
			pInfinity->m_ptCurrentPosExact.x = *pX * 10000;
			bSetNoScrollCursor = true;

			if (pInfinity->m_ptScrollDest.x != -1)
			{
				pInfinity->m_ptScrollDest.x = *pX;
			}
		}
	}
	else
	{
		const int nMaxAllowedXRight = (pInfinity->nAreaX - nViewPortWidth) + nAllowedOOBRight;

		if (*pX > nMaxAllowedXRight)
		{
			// Snap - x too far right
			*pX = nMaxAllowedXRight;

			if (!bTheoretical)
			{
				pInfinity->m_ptCurrentPosExact.x = *pX * 10000;
				bSetNoScrollCursor = true;

				if (pInfinity->m_ptScrollDest.x != -1)
				{
					pInfinity->m_ptScrollDest.x = *pX;
				}
			}
		}
	}

	////////////////////////////////////
	// Calculate allowed vertical OOB //
	////////////////////////////////////

	int nAllowedOOBTop = 0;
	int nAllowedOOBBottom = 0;

	if (bShowBlackSpace)
	{
		nAllowedOOBTop = nViewPortHeight / 2;
		nAllowedOOBBottom = nAllowedOOBTop;
	}
	else if (!p_uiIsHidden())
	{
		const bool bActionbarOpen = pMenuStateOverrides != nullptr
			? pMenuStateOverrides->bWorldActionbarOpen
			: p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_ACTIONBAR" }) && pChitin->pActiveEngine != pChitin->m_pEngineMap;

		if (bActionbarOpen)
		{
			if (static_cast<int>(*CChitin::p_ENGINE_MODE) == PTEE::ENGINE_MODE_PST)
			{
				const char *const sActionbar = PTEE::UseTouchActionbar(pGame->m_options) ? "WORLD_ACTIONBAR_LEFT_TABLET" : "WORLD_ACTIONBAR_LEFT";
				const bool bLeftActionbarOpen = pMenuStateOverrides != nullptr
					? pMenuStateOverrides->bWorldActionbarLeftOpen
					: p_uiIsMenuOnStack(EngineVal<CString, false>{ sActionbar });

				if (bLeftActionbarOpen)
				{
					nAllowedOOBBottom = static_cast<int>(getAreaValue(sActionbar, 4) * fEffectiveZoom + 0.0);
				}
			}
			else
			{
				nAllowedOOBBottom = static_cast<int>(getAreaValue("WORLD_ACTIONBAR", 4) * fEffectiveZoom + 0.0);

				if (pMenuStateOverrides != nullptr ? pMenuStateOverrides->bWorldDialogOpen : p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_DIALOG" }))
				{
					nAllowedOOBBottom = static_cast<int>(getAreaValue("worldDialogBackground", 4) * fEffectiveZoom + nAllowedOOBBottom);
				}
				else if (pMenuStateOverrides != nullptr ? pMenuStateOverrides->bWorldMessagesOpen : p_uiIsMenuOnStack(EngineVal<CString, false>{ "WORLD_MESSAGES" }))
				{
					nAllowedOOBBottom = static_cast<int>(getAreaValue("messagesRect", 4) * fEffectiveZoom + nAllowedOOBBottom);
				}
			}
		}
	}

	///////////////
	// Check top //
	///////////////

	const int nAllowedHeight = pInfinity->nAreaY + nAllowedOOBTop + nAllowedOOBBottom;

	if (nViewPortHeight > nAllowedHeight)
	{
		// Center
		const int nNewY = (nAllowedHeight - nViewPortHeight) / 2 - nAllowedOOBTop;

		if (*pY != nNewY)
		{
			// Snap - Viewport height too large
			*pY = nNewY;

			if (!bTheoretical)
			{
				pInfinity->m_ptCurrentPosExact.y = *pY * 10000;
				bCenteredY = true;

				if (pInfinity->m_ptScrollDest.y != -1)
				{
					pInfinity->m_ptScrollDest.y = *pY;
				}
			}
		}
	}
	else if (*pY < -nAllowedOOBTop)
	{
		// Snap - y too far up
		*pY = -nAllowedOOBTop;

		if (!bTheoretical)
		{
			pInfinity->m_ptCurrentPosExact.y = *pY * 10000;
			bSetNoScrollCursor = true;

			if (pInfinity->m_ptScrollDest.y != -1)
			{
				pInfinity->m_ptScrollDest.y = *pY;
			}
		}
	}
	else
	{
		const int nMaxAllowedYBottom = (pInfinity->nAreaY - nViewPortHeight) + nAllowedOOBBottom;

		if (*pY > nMaxAllowedYBottom)
		{
			// Snap - y too far down
			*pY = nMaxAllowedYBottom;

			if (!bTheoretical)
			{
				pInfinity->m_ptCurrentPosExact.y = *pY * 10000;
				bSetNoScrollCursor = true;

				if (pInfinity->m_ptScrollDest.y != -1)
				{
					pInfinity->m_ptScrollDest.y = *pY;
				}
			}
		}
	}

	/////////////////////////////////
	// Check "at world edge" state //
	/////////////////////////////////

	CGameArea *const pArea = pGame->m_gameAreas[pGame->m_visibleArea];

	if (pArea == nullptr)
	{
		return;
	}

	CInfCursor *const pCursor = pChitin->m_pObjectCursor;

	// Patch: Only reset the cursor if it is edge scrolling
	// |
	// EEex-PTEE: Torment keeps the edge-scroll cursor while the view is locked on a creature
	// |
	if (bSetNoScrollCursor && pWorld->m_scrollLockId == -1 && pArea->m_nScrollState >= 1 && pArea->m_nScrollState <= 8)
	{
		pArea->m_nScrollState = 9;
		pCursor->SetCursor(6, 0, -1);
	}

	// EEex-PTEE: Torment drops the scroll direction of a centered axis (cursor ids as in PT 0x305296..0x305437)
	if (bCenteredX)
	{
		switch (pArea->m_nScrollState)
		{
			case 3: case 7: pCursor->SetCursor(6, 0, -1); pArea->m_nScrollState = 9; break; // right / left -> none
			case 2: case 8: pCursor->SetCursor(0, 0, -1); pArea->m_nScrollState = 1; break; // up-right / up-left -> up
			case 4: case 6: pCursor->SetCursor(4, 0, -1); pArea->m_nScrollState = 5; break; // down-right / down-left -> down
			default: break;
		}
	}

	if (bCenteredY)
	{
		switch (pArea->m_nScrollState)
		{
			case 1: case 5: pCursor->SetCursor(6, 0, -1); pArea->m_nScrollState = 9; break; // up / down -> none
			case 2: case 4: pCursor->SetCursor(2, 0, -1); pArea->m_nScrollState = 3; break; // up-right / down-right -> right
			case 6: case 8: pCursor->SetCursor(6, 0, -1); pArea->m_nScrollState = 7; break; // down-left / up-left -> left
			default: break;
		}
	}
}
