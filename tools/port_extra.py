# Port the game-version extra pattern DB (EEex/loader/v2.6.6.0/pattern_dbs/v2.6.6.0.db, installed by
# EEex as EEex_scripts/extra_pattern_dbs/) to Torment.exe. Its patterns come from a slightly different
# BG2EE build and match neither our Baldur_bg2ee.exe nor Torment.exe, so function entries are located
# by name (bgnames.py -> ptnames.json) and checked by hand (show.py: identical code on both sides).
# The 4 drawItem/OnResizeWindow hooks (EEex_Menu_Patch.lua) are located by context in LABELS.
# Writes poc/extra_pattern_dbs/ptee.db
import os
from ilib import *
from gen import unique_at

OUT = REPO + r'\poc\extra_pattern_dbs\ptee.db'
# name -> (BG rva, PT rva), verified with show.py
FUNCS = {
    'CChitin::OnResizeWindow': (0x41a830, 0x4a4080),
    'CRes::Demand': (0x3f6d50, 0x47d9b0),
    'CResFont::GetFont': (0x3f78f0, 0x47e550),
}
# EEex-PTEE dev labels (not in upstream): CScreenStart::TimerAsynchronousUpdate first tick plays
# PlayMovie("LOGO") then PlayMovieNext("OPENING") (0x346a54..0x346aab); used by PTEE_SkipIntro.lua
LABELS = {
    # Torment-only engine functions bound by eeexdll/source/ptee_engine.cpp
    'PTEE-CGameSprite::GetEffectiveAlignment': 0x3c4fe0,
    'PTEE-uiNavigateEvent': 0x459ff0,
    'PTEE-CGameAIBase::PartyHasItem': 0x174e00,
    'PTEE-CVariableHash::GetValue': 0x2b4b80,
    'PTEE-CGameSprite::HasFistOfIron': 0x3d0ae0,
    # SDL 2.0.4's SDL_SetHint (called by Torment's CChitin::WinMain, not bound by EEex)
    'PTEE-SDL_SetHint': 0x4dafe0,
    # CInfinity::SetZoomEnabled (BG has it too but EEex does not bind it); used by Torment's EndDialog
    'PTEE-CInfinity::SetZoomEnabled': 0x3097f0,
    # Torment-only: UI rect = screen inset by CChitin's UI edge fraction (+0x1f4), used by uiDrawMenuStack
    'PTEE-CChitin::GetUIRect': 0x4a3180,
    # CVidMode window -> internal screen coordinates (BG 0x41e8d0, not bound by EEex); Torment's middle-mouse
    # drag (CScreenWorld::OnEvent PT 0x35ba53) converts the motion deltas with it
    'PTEE-CVidMode::WindowToScreen': 0x4a7fe0,
    # CAIScript::Read(resref, bPlayerScript) (BG 0x11fe10): Torment's CAIScript constructor has no player
    # flag (it calls Read(resref, 0)); CGameSprite::JoinParty reads player scripts with Read(resref, 1)
    'PTEE-CAIScript::Read': 0x12d240,
    # same function under the name the Lua bindings resolve (manual_types_pt.txt: CAIScript $pattern_name(Read(CResRef,int)))
    'CAIScript::Read(CResRef,int)': 0x12d240,
    # EEex_Menu_Patch.lua hooks of the version extra DB, located by context (identical code, the uiItem is in
    # r13 in Torment's drawItem instead of r15: the phase-5 Lua must use r13)
    'Hook-CChitin::OnResizeWindow()-B3Scale': 0x4a41af,             # call SDL_GL_GetDrawableSize after SCREENWIDTH/HEIGHT
    'Hook-drawItem()-AfterEnabledCheck': 0x44eb2b,                  # after the item "enabled" Lua check
    'Hook-drawItem()-CheckScrollbarContentHeight': 0x450db3,        # Torment: jg (short), BG: jle (near): inverted
    'Hook-drawItem()-FixForcedScrollbarDivideByZero2': 0x451199,    # 11 bytes: mov [rbp+0x28], 0x12; sub eax, [r13+0x4c]
    # Torment-only CDerivedStats::Reload call (sprite in r15) in the ExecuteAction helper PT 0x173c00 (EEex_Stats_Patch.lua)
    'Hook-PTEE-ExecuteActionHelper()-CDerivedStats::Reload()': 0x17421e,
    # Torment's own spell action handlers (called from the ExecuteAction switches) decode their projectile themselves:
    # return addresses for EEex_Projectile.lua's decode sources (Spell 31 / SpellNoDec 191 -> PT 0x42e3f0, SpellPoint
    # 95 / 192 -> 0x431790 in CGameSprite::ExecuteAction; ForceSpell 113 / 181 / 240 / 466 -> 0x180e20, ForceSpellPoint
    # 114 / 337 -> 0x182b60 in CGameAIBase::ExecuteAction)
    'Data-PTEE-SpellAction()-CProjectile::DecodeProjectile()-RetPtr': 0x42f2a6,
    'Data-PTEE-SpellPointAction()-CProjectile::DecodeProjectile()-RetPtr': 0x43229b,
    'Data-PTEE-ForceSpellAction()-CProjectile::DecodeProjectile()-RetPtr': 0x181345,
    'Data-PTEE-ForceSpellPointAction()-CProjectile::DecodeProjectile()-RetPtr': 0x183143,
    'Hook-CScreenStart::TimerAsynchronousUpdate()-StartupMovies': 0x346a54,
    'Hook-CScreenStart::TimerAsynchronousUpdate()-AfterStartupMovies': 0x346aab,
    # CInfGame::RestPartyPrivate heal-on-rest loop: call of the party heal pass (PT 0x2de370), EEex_Fix_Patch.lua
    # leaves the loop when a pass heals nothing and the per-rest heal amount is 0 (AUDIT.md, RestParty() hang)
    'Hook-PTEE-CInfGame::RestPartyPrivate()-HealPartyCall': 0x2edd60,
}
# Torment-only engine globals: name -> (rva of a RIP-relative instruction, offset of its disp32, length)
DATA = {
    # Sprite update spreading mask (BG2EE 1, Torment 7): staggered sprite work runs when
    # (m_id & mask) == (worldTime & mask); CheckIfVisible sets m_canBeSeen = (mask + 1) * 4.
    # Read by CGameSprite::CheckIfVisible PT 0x3be3a8 `movzx eax, byte ptr [rip + X]`.
    'PTEE-g_nSpriteUpdateMask': (0x3be3a8, 3, 7),
    # g_pChitin (CChitin*), passed to CChitin::GetUIRect by uiDrawMenuStack PT 0x456fa8 `mov rcx, [rip + X]`
    'PTEE-g_pChitin': (0x456fa8, 3, 7),
}
lines = ['; EEex-PTEE: Torment.exe v3.2.2.0 port of EEex/loader/v2.6.6.0/pattern_dbs/v2.6.6.0.db', '']
for name, (bg, pt) in FUNCS.items():
    p, start = unique_at(pt)
    ops = f'ADD {pt - start}' if pt != start else ''
    lines += [f'[{name}]', f'Pattern={p}'] + ([f'Operations={ops}'] if ops else []) + ['']
    print(name, hex(pt), p, ops)
for name, pt in LABELS.items():
    p, start = unique_at(pt)
    ops = f'ADD {pt - start}' if pt != start else ''
    lines += [f'[{name}]', f'Pattern={p}'] + ([f'Operations={ops}'] if ops else []) + ['']
    print(name, hex(pt), p, ops)
for name, (pt, doff, ilen) in DATA.items():
    p, start = unique_at(pt)
    lines += [f'[{name}]', f'Pattern={p}', f'Operations=ADD {pt + doff - start}, PUSH, READ DWORD, ADD, ADD {ilen - doff}', '']
    print(name, hex(pt), p)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', newline='\n').write('\n'.join(lines))
