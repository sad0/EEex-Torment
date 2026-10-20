# Generated from Core fixup.py: every fixup tolerates fields made opaque by the PTEE layout.

from generate_bindings import relocateGroup

def fixup(mainState):

	try:
		relocateGroup(mainState, "frameTableEntryVersion_t", f"frameTableEntry_st::{mainState.resolveAlias("frameTableEntryVersion_t")}")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])

	try:
		mainState.getGroup("d3d_t").retypeField(mainState, "textures", "Array<texture_t_DX,512>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("C2DArray").retypeField(mainState, "m_pArray", "VariableArray<CString>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("C2DArray").retypeField(mainState, "m_pNamesX", "VariableArray<CString>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("C2DArray").retypeField(mainState, "m_pNamesY", "VariableArray<CString>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAIGroup").retypeField(mainState, "m_memberList", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAIIdList").retypeField(mainState, "m_pIdArray", "VariableArray<CAIId*>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileCharacterEntryPoint").retypeField(mainState, "m_entryName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileContainer").retypeField(mainState, "m_keyType", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileContainer").retypeField(mainState, "m_ownedBy", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileContainer").retypeField(mainState, "m_script", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileContainer").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileHeader").retypeField(mainState, "m_areaEdgeEast", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileHeader").retypeField(mainState, "m_areaEdgeNorth", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileHeader").retypeField(mainState, "m_areaEdgeSouth", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileHeader").retypeField(mainState, "m_areaEdgeWest", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileHeader").retypeField(mainState, "m_areaName", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileProjectileObject").retypeField(mainState, "m_portraitNum", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileProjectileObject").retypeField(mainState, "m_resref", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileRandomMonsterSpawningPoint").retypeField(mainState, "m_randomCreature", "Array<CResRef,10>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileRandomMonsterSpawningPoint").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileRestEncounter").retypeField(mainState, "m_randomCreature", "Array<CResRef,10>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileRestEncounter").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileSoundObject").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileSoundObject").retypeField(mainState, "m_soundObject", "Array<CResRef,10>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileStaticObject").retypeField(mainState, "m_paletteResref", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileStaticObject").retypeField(mainState, "m_resref", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaFileStaticObject").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaSoundsAndMusic").retypeField(mainState, "m_dayAmbient", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaSoundsAndMusic").retypeField(mainState, "m_dayAmbientExtended", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaSoundsAndMusic").retypeField(mainState, "m_nightAmbient", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaSoundsAndMusic").retypeField(mainState, "m_nightAmbientExtended", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaVariable").retypeField(mainState, "m_name", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CAreaVariable").retypeField(mainState, "m_stringValue", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CChitin").retypeField(mainState, "lEngines", "CTypedPtrList<CPtrList,CWarp*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CChitin").retypeField(mainState, "m_lstMouseWheel", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_luckBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_portraitLarge", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_portraitSmall", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_proficiencies", "Array<__int8,15>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_repChangeJoined", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_repChangeKicked", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_repChangeKilled", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistAcidBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistColdBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistCrushingBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistElectricityBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistFireBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistMagicBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistMagicColdBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistMagicFireBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistMissileBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistPiercingBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_resistSlashingBase", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_scriptClass", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_scriptDefault", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_scriptGeneral", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_scriptOverRide", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_scriptRace", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_toHitArmorClass0Base", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileHeader").retypeField(mainState, "m_trackingTarget", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileItem").retypeField(mainState, "m_itemId", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileKnownSpell").retypeField(mainState, "m_knownSpellId", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CCreatureFileMemorizedSpell").retypeField(mainState, "m_spellId", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CDWordArray").retypeField(mainState, "m_pData", "VariableArray<int>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameAIBase").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameAIBase_vtbl").retypeFunctionFieldRet(mainState, "GetVisibleTerrainTable", "byte*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lContainersNeedingUpdate", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lGameTextObjects", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSort", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortAdd", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortBack", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortBackAdd", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortFlight", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortFlightAdd", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortTransition", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortUnder", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameArea").retypeField(mainState, "m_lVertSortUnderAdd", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameContainer").retypeField(mainState, "m_ownedBy", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameContainer").retypeField(mainState, "m_scriptRes", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameDoor").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameDoor").retypeField(mainState, "m_scriptRes", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameDoor").retypeField(mainState, "m_triggerName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameEffect_vtbl").addFunctionFieldParameter(mainState, "Destruct", "unsigned int")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameEffectBase").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject").retypeField(mainState, "m_listType", "VertListType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject").retypeField(mainState, "m_objectType", "CGameObjectType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject_vtbl").addFunctionFieldParameter(mainState, "Destruct", "unsigned int")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject_vtbl").retypeFunctionFieldRet(mainState, "GetObjectType", "CGameObjectType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject_vtbl").retypeFunctionFieldRet(mainState, "GetVertListPos", "CTypedPtrList<CPtrList,long>::CNode*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameObject_vtbl").retypeFunctionFieldRet(mainState, "GetVertListType", "VertListType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameSprite").retypeField(mainState, "m_circleFacing", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameSprite").retypeField(mainState, "m_lstTargetIds", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameSprite").retypeField(mainState, "m_nPathTemp", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameSprite").retypeField(mainState, "m_spriteEffectBaseIntensity", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameTiledObject").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameTrigger").retypeField(mainState, "m_newArea", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameTrigger").retypeField(mainState, "m_newEntryPoint", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameTrigger").retypeField(mainState, "m_scriptName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CGameTrigger").retypeField(mainState, "m_scriptRes", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CImmunitiesProjectile").retypeExtendsIndex(mainState, 0, "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CImmunitiesSchoolAndSecondary").retypeExtendsIndex(mainState, 0, "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfButtonArray").retypeField(mainState, "m_nSelectedButton", "CButtonType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_allies", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_characterOverflow", "CTypedPtrArray<CPtrArray,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_familiars", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_lDisposableItems", "CTypedPtrList<CPtrList,CItem*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_lstGlobalCreatures", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_lstTargetIds", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CInfGame").retypeField(mainState, "m_resrefFamiliarsDefault", "Array<CResRef,9>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CObArray").retypeField(mainState, "m_pData", "VariableArray<CObject*>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CObject_vtbl").addFunctionFieldParameter(mainState, "Destruct", "unsigned int")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CProjectileArea").retypeField(mainState, "m_portraitNum", "__int8")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CPtrArray").retypeField(mainState, "m_pData", "VariableArray<void*>*")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CResBinary").retypeField(mainState, "m_resVersion", "LCharString<4>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_areaName", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_creatureResRef", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_lSpellStatsName", "Array<CResRef,4>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_lWeaponStatsName", "Array<CResRef,4>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_name", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_pad1", "Array<__int8,2>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_quickSpellsSpellId", "Array<CResRef,3>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGamePartyCreature").retypeField(mainState, "m_secondarySounds", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSavedGameStoredLocation").retypeField(mainState, "m_areaName", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenCreateChar").retypeField(mainState, "m_aBaseProficiencySlots", "CTypedPtrArray<CPtrArray,__int8>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenStore").retypeField(mainState, "m_lGroupItems", "CTypedPtrList<CPtrList,CScreenStoreItem*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenStore").retypeField(mainState, "m_lIdentifyItems", "CTypedPtrList<CPtrList,CScreenStoreItem*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenStore").retypeField(mainState, "m_lSpellItems", "CTypedPtrList<CPtrList,CScreenStoreItem*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenStore").retypeField(mainState, "m_lStoreItems", "CTypedPtrList<CPtrList,CScreenStoreItem*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenWorld").retypeField(mainState, "m_otherTalkers", "CTypedPtrList<CPtrList,long>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenWorld").retypeField(mainState, "m_szChapterTransitionResRef", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenWorld").retypeField(mainState, "m_szMovieResRef", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CScreenWorld").retypeField(mainState, "m_szTextScreenTransitionResRef", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSoundChannel").retypeField(mainState, "lQueue", "CTypedPtrList<CPtrList,CSound*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSoundMixerImp").retypeField(mainState, "aChannels", "CTypedPtrArray<CPtrArray,CSoundChannel*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSoundMixerImp").retypeField(mainState, "lLooping", "CTypedPtrList<CPtrList,CSound*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSoundMixerImp").retypeField(mainState, "lVoices", "CTypedPtrList<CPtrList,CVoice*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CSoundMixerImp").retypeField(mainState, "lWaiting", "CTypedPtrList<CPtrList,CSound*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStore").retypeField(mainState, "m_pVersion", "LCharString<8>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileDrinks").retypeField(mainState, "m_icon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileHeader").retypeField(mainState, "m_resDonation", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileHeader").retypeField(mainState, "m_resRumor", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileHeader").retypeField(mainState, "m_script", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileItem").retypeField(mainState, "m_itemId", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CStoreFileSpell").retypeField(mainState, "m_spell", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWarp").retypeField(mainState, "lTimers", "CTypedPtrList<CPtrList,CTimer*>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapArea").retypeField(mainState, "m_resAreaLoadMosaic", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapArea").retypeField(mainState, "m_resCurrentArea", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapArea").retypeField(mainState, "m_resOriginalArea", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapArea").retypeField(mainState, "m_strName", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapData").retypeField(mainState, "m_resAreaIcons", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapData").retypeField(mainState, "m_resMosaic", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_entryPoint", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_resRandomEncounterArea0", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_resRandomEncounterArea1", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_resRandomEncounterArea2", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_resRandomEncounterArea3", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("CWorldMapLinks").retypeField(mainState, "m_resRandomEncounterArea4", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("DP_Player").retypeField(mainState, "name", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("DP_Player").retypeField(mainState, "remoteAddr", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_ability_st").retypeField(mainState, "quickSlotIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_effect_st").retypeField(mainState, "res", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_Header_st").retypeField(mainState, "animationType", "LCharString<2>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_Header_st").retypeField(mainState, "descriptionPicture", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_Header_st").retypeField(mainState, "groundIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_Header_st").retypeField(mainState, "itemIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Item_Header_st").retypeField(mainState, "usedUpItemID", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SDL_Event").retypeField(mainState, "type", "SDL_EventType")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SDL_Keysym").retypeField(mainState, "sym", "SDL_Keycode")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SDL_TextEditingEvent").retypeField(mainState, "text", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SDL_TextInputEvent").retypeField(mainState, "text", "LCharString<32>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Spell_ability_st").retypeField(mainState, "quickSlotIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Spell_Header_st").retypeField(mainState, "descriptionPicture", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Spell_Header_st").retypeField(mainState, "groundIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Spell_Header_st").retypeField(mainState, "itemIcon", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("Spell_Header_st").retypeField(mainState, "usedUpItemID", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCDetails_t").retypeField(mainState, "m_pchFileName", "LCharString<260>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCDetails_t").retypeField(mainState, "m_rgchDescription", "LCharString<8000>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCDetails_t").retypeField(mainState, "m_rgchTags", "LCharString<1025>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCDetails_t").retypeField(mainState, "m_rgchTitle", "LCharString<129>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCDetails_t").retypeField(mainState, "m_rgchURL", "LCharString<256>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("SteamUGCQueryCompleted_t").retypeField(mainState, "m_rgchNextCursor", "LCharString<256>")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("UI_PanelHeader_st").retypeField(mainState, "refMosaic", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("WED_LayerHeader_st").retypeField(mainState, "rrTileSet", "CResRef")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])

	# The real header for these types is included; these internal fields cannot be accessed
	try:
		mainState.getGroup("ID3DXInclude").removeFieldByName(mainState, "__vftable")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3D9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DBaseTexture9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DCubeTexture9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DDevice9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DIndexBuffer9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DPixelShader9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DQuery9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DStateBlock9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DSurface9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DSwapChain9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DTexture9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DVertexBuffer9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DVertexDeclaration9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DVertexShader9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DVolume9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IDirect3DVolumeTexture9").removeFieldByName(mainState, "lpVtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.getGroup("IUnknown").removeFieldByName(mainState, "__vftable")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])

	# The real header for these types is included; prevent these internal vftable structs from being processed
	try:
		mainState.removeGroup("ID3DXBaseEffect_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXBuffer_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXEffect_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXEffectPool_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXEffectStateManager_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXInclude_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IUnknown_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])

	# Just to remove warnings from the script about vftable this type mismatches
	try:
		mainState.removeGroup("ID3DXFont_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ID3DXSprite_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IDirect3DResource9_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IDispatch_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IEnumSTATSTG_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IErrorInfo_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IPersist_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IPersistStream_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IRecordInfo_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ISequentialStream_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IShellItem_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IShellLibrary_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IStorage_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("IStream_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ITypeComp_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ITypeInfo_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
	try:
		mainState.removeGroup("ITypeLib_vtbl")
	except Exception as e:
		print('fixup skipped:', repr(e)[:120])
