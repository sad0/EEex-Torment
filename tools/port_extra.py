# Port the game-version extra pattern DB (EEex/loader/v2.6.6.0/pattern_dbs/v2.6.6.0.db, installed by
# EEex as EEex_scripts/extra_pattern_dbs/) to Torment.exe. Its patterns come from a slightly different
# BG2EE build and match neither our Baldur_bg2ee.exe nor Torment.exe, so function entries are located
# by name (bgnames.py -> ptnames.json) and checked by hand (show.py: identical code on both sides).
# The 4 drawItem/OnResizeWindow hooks are only used by EEex_Menu_Patch.lua (phase 5) and are left out.
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
    'Hook-CScreenStart::TimerAsynchronousUpdate()-StartupMovies': 0x346a54,
    'Hook-CScreenStart::TimerAsynchronousUpdate()-AfterStartupMovies': 0x346aab,
}
lines = ['; EEex-PTEE: Torment.exe v3.2.2.0 port of EEex/loader/v2.6.6.0/pattern_dbs/v2.6.6.0.db',
         '; TODO(phase 5): Hook-CChitin::OnResizeWindow()-B3Scale, Hook-drawItem()-AfterEnabledCheck,',
         ';   Hook-drawItem()-CheckScrollbarContentHeight, Hook-drawItem()-FixForcedScrollbarDivideByZero2', '']
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
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', newline='\n').write('\n'.join(lines))
