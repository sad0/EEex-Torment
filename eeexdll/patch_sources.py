# Torment.exe semantic patches for upstream EEex.dll sources. The upstream files under ref/ stay
# untouched; patched copies are written to eeexdll/generated/src/ and compiled instead of them
# (make_vcxproj.py). Every replacement must match exactly once, so upstream changes fail loudly.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, r'..\ref\InfinityLoader\EEex-Core-Shared-Files\source')
OUT = os.path.join(HERE, r'generated\src')

# PTEE item slots (ITMSLOTS.2DA) keep the BG2EE indices for FIST (10), SPECIAL/magic weapon (34) and
# WEAPONS (35-38), but slot 9 is TATTOO3 and there is no shield / off-hand slot: nothing can attack
# with the left hand.
PATCHES = {
    'EEex.cpp': [
        ("""bool EEex::CanAttackWithLeftHand(CGameSprite* pSprite)
{
""", """bool EEex::CanAttackWithLeftHand(CGameSprite* pSprite)
{
	// EEex-PTEE: Torment has no off-hand slot (slot 9 is TATTOO3 in ITMSLOTS.2DA)
	return false;
"""),
        ("""	CItem *const pLeftHandItem = this->m_equipment.m_items[9];
	const bool isLeftHand = lastSwing && pLeftHandItem != nullptr && pLeftHandItem->pRes->pHeader->itemType != 12;""",
         """	// EEex-PTEE: Torment has no off-hand slot (slot 9 is TATTOO3 in ITMSLOTS.2DA)
	const bool isLeftHand = false;"""),
        # Bind Torment-only engine functions before anything else uses them
        ('''void EEex::InitEEex() {
''', '''void EEex::InitEEex() {

	PTEE::BindEngine();
'''),
        ('''#include "Baldur_generated.h"
''', '''#include "Baldur_generated.h"
#include "ptee_engine.hpp"
'''),
        # op319 (CGameEffectUsability::CheckUsability), Torment rules (PT 0x1ed180): param2 = 8 compares
        # the effective alignment (Nameless One: from the Law/Good globals) and PT adds param2 = 12, a
        # byte of the creature header at +0x87 (BG m_trackingTarget bytes, reused by PTEE).
        ('''			case 8: {
				match = pAIType->m_Alignment == this->m_effectAmount;
				break;
			}''', '''			case 8: {
				// EEex-PTEE: Torment compares the effective alignment (PT 0x3c4fe0). The type is passed
				// by value: the callee destroys the copy (its CString), as the engine's caller expects.
				alignas(CAIObjectType) byte aiTypeCopyStorage[sizeof(CAIObjectType)];
				CAIObjectType *const pAITypeCopy = reinterpret_cast<CAIObjectType*>(aiTypeCopyStorage);
				pAITypeCopy->Construct(pAIType);
				match = PTEE::p_CGameSprite_GetEffectiveAlignment(pSprite, pAITypeCopy) == this->m_effectAmount;
				break;
			}'''),
        ('''				#pragma warning(default:6054)
				break;
			}
		}''', '''				#pragma warning(default:6054)
				break;
			}
			case 12: {
				// EEex-PTEE: Torment-only mode, creature header byte +0x87
				match = reinterpret_cast<const byte*>(&pSprite->m_baseStats)[0x87] == this->m_effectAmount;
				break;
			}
		}'''),
        # CGameEffect::CheckSave: Torment's saving-throw code differs from BG2EE's (similarity 0.41);
        # EEex's BG reimplementation is replaced by a call to PT's own base implementation.
        ('@body int EEex::Override_CGameEffect_CheckSave(', '''{
	// EEex-PTEE: forward to Torment's own CGameEffect::CheckSave (PT rules)
	return PTEE::p_CGameEffect_CheckSave(pEffect, pTarget, saveVSDeathRollRaw, saveVSWandsRollRaw, saveVSPolyRollRaw,
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

	if (PTEE::p_uiNavigateEvent(pEvent, pWindow)) {
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
    ],
}

os.makedirs(OUT, exist_ok=True)
for name, reps in PATCHES.items():
    s = open(os.path.join(SRC, name), encoding='utf-8-sig').read()
    for old, new in reps:
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
