# Release package: build/release/ = setup-EEex.exe (WeiDU) + EEex/ (mod folder), zipped to build/EEex-PSTEE-<ver>.zip.
# Sources: installer/ (tp2, tra, readme), upstream InfinityLoader binaries (ref/EEex/EEex/loader, unchanged),
# our builds (build/EEex-PSTEE/EEex.dll, build/LuaBindings-PSTEE/LuaBindings.dll), poc/ (Torment pattern DB, extra
# pattern DB, profiler names), eeexlua/generated/ (Lua port, no dev-only test files), eeexlua/src/patch/ (IDS).
#   python tools/package.py        (run eeexlua/build.py and the DLL builds first: tools/rebuild_all.sh)
import os, re, sys, shutil, zipfile
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
UP = os.path.join(REPO, r'ref\EEex\EEex')
OUT = os.path.join(REPO, r'build\release')
MOD = os.path.join(OUT, 'EEex')
# dev-only scripts appended by eeexlua/build.py --deploy (never in eeexlua/generated, checked anyway)
DEV_ONLY = re.compile(r'^PSTEE_(SkipIntro|SpellTest|FeatureTest|UIProbe|AttackTrace|VisMapTest)\.lua$')


def P(*a):
    return os.path.join(REPO, *a)


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def copytree(src, dst):
    for name in sorted(os.listdir(src)):
        s = os.path.join(src, name)
        if os.path.isfile(s):
            if DEV_ONLY.match(name):
                raise SystemExit('dev-only file in release sources: ' + s)
            copy(s, os.path.join(dst, name))


def loader_ini():
    """Upstream InfinityLoader.ini set up for Torment.exe (same values as the tested dev game, Debug off)."""
    s = open(os.path.join(UP, r'loader\InfinityLoader.ini'), encoding='utf-8').read()
    for old, new in (('ExeNames=Baldur.exe,BaldurII.exe,icewind.exe,SiegeOfDragonspear.exe', 'ExeNames=Torment.exe'),
                     ('ExeSwitchAlias=BaldurII.exe:Baldur.exe,SiegeOfDragonspear.exe:Baldur.exe', 'ExeSwitchAlias='),
                     # Torment's main object is 0x1910 bytes (BG 0x1918): PLAN.md findings
                     ('Pattern=B918190000', 'Pattern=B910190000'),
                     ('LogFile=\n', 'LogFile=EEex.log\n')):
        if s.count(old) != 1:
            raise SystemExit('InfinityLoader.ini: expected once: ' + old)
        s = s.replace(old, new)
    return s


def main():
    tp2 = open(P('installer', 'EEex.tp2'), encoding='utf-8').read()
    ver = re.search(r'^VERSION ~(.+?)~', tp2, re.M).group(1)
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(MOD)
    copy(P(r'tools\weidu\weidu.exe'), os.path.join(OUT, 'setup-EEex.exe'))
    copy(P('installer', 'EEex.tp2'), os.path.join(MOD, 'EEex.tp2'))
    copy(P('installer', 'readme-EEex-PSTEE.txt'), os.path.join(MOD, 'readme-EEex-PSTEE.txt'))
    for lang in ('english', 'french'):
        copy(P('installer', 'language', lang, 'setup.tra'), os.path.join(MOD, 'language', lang, 'setup.tra'))
    copy(os.path.join(UP, r'lib\always.tph'), os.path.join(MOD, r'lib\always.tph'))
    copytree(P(r'eeexlua\src\patch'), os.path.join(MOD, 'patch'))
    # loader folder: copied as-is to the game root by the main component
    ld = os.path.join(MOD, 'loader')
    for f in ('InfinityLoader.exe', 'InfinityLoaderCommon.dll', 'InfinityLoaderDLL.dll', 'InfinityLoaderUtil.dll',
              'LuaBindingsCore.dll', 'EEex.ini'):
        copy(os.path.join(UP, 'loader', f), os.path.join(ld, f))
    copy(os.path.join(UP, r'loader\Lua52\LuaProvider.dll'), os.path.join(ld, 'LuaProvider.dll'))
    copy(P(r'build\EEex-PSTEE\EEex.dll'), os.path.join(ld, 'EEex.dll'))
    copy(P(r'build\LuaBindings-PSTEE\LuaBindings.dll'), os.path.join(ld, 'LuaBindings.dll'))
    copy(P(r'poc\InfinityLoader.db'), os.path.join(ld, 'InfinityLoader.db'))
    open(os.path.join(ld, 'InfinityLoader.ini'), 'w', encoding='utf-8', newline='\n').write(loader_ini())
    copy(P(r'poc\extra_pattern_dbs\pstee.db'), os.path.join(ld, r'pattern_dbs\pstee.db'))
    copy(P(r'poc\profiler\function_names.db'), os.path.join(ld, r'profiler\function_names.db'))
    # Lua port
    for sub in ('EEex_scripts', 'override'):
        copytree(P('eeexlua', 'generated', sub), os.path.join(MOD, 'copy', sub))
    zpath = P('build', f'EEex-PSTEE-{ver}.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, OUT))
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f'{n} files -> {OUT}\n{zpath} ({os.path.getsize(zpath) // 1024} KB)')


if __name__ == '__main__':
    main()
