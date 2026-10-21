# Torment port of EEex's Lua (upstream ref/EEex/EEex/copy). The upstream files stay untouched; patched
# copies are written to eeexlua/generated/ (EEex_scripts/ and override/):
#  - eeexlua/patches/<file>.py: PATCHES = [(old, new), ...] for upstream <file> (exact, once; '@all:N old'
#    replaces exactly N occurrences; '@file' as old replaces the whole file with new,
#    '@file-end' appends new);
#  - eeexlua/src/EEex_scripts/*, eeexlua/src/override/*: Torment-only files, copied as they are.
#   python build.py [--deploy]   (--deploy: copy to the dev game, tools/deploy.py's GAME)
import os, sys, glob, shutil, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.join(HERE, r'..\ref\EEex\EEex\copy')
OUT = os.path.join(HERE, 'generated')
GAME = r'E:\Enhanced Edition\Environnement de test\PTEE (EEex dev)'
# dev-only scripts (bindings/test/) loaded after EEex's startup in the dev game
DEV_FILES = ['PTEE_SkipIntro', 'PTEE_SpellTest', 'PTEE_FeatureTest', 'PTEE_BatterySpells', 'PTEE_Battery']


def load_patches():
    out = {}
    for path in sorted(glob.glob(os.path.join(HERE, 'patches', '*.py'))):
        spec = importlib.util.spec_from_file_location('p', path)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        out[os.path.basename(path)[:-3]] = mod.PATCHES
    return out


def apply(name, s, reps):
    for old, new in reps:
        if old == '@file':
            s = new
            continue
        if old == '@file-end':
            s = s.rstrip('\n') + '\n' + new
            continue
        if old.startswith('@all:'):
            cnt, old = old[len('@all:'):].split(' ', 1)
            if s.count(old) != int(cnt):
                raise SystemExit(f'{name}: expected {cnt} matches, found {s.count(old)}: {old}')
            s = s.replace(old, new)
            continue
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{name}: patch matches {n} times:\n{old}')
        s = s.replace(old, new)
    return s


def build():
    patches = load_patches()
    # empty the output folders (not removed: a shell may have one as its current directory)
    for f in glob.glob(os.path.join(OUT, '*', '*')):
        os.remove(f)
    done = set()
    for sub in ('EEex_scripts', 'override'):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
        for src in glob.glob(os.path.join(UP, sub, '*')):
            name = os.path.basename(src)
            dst = os.path.join(OUT, sub, name)
            key = name[:-4] if name.endswith('.lua') else name
            if key in patches:
                s = open(src, encoding='utf-8').read()
                s = apply(name, s, patches[key])
                open(dst, 'w', encoding='utf-8', newline='\n').write(s)
                done.add(key)
                print(f'{sub}/{name}: {len(patches[key])} patches')
            else:
                shutil.copy(src, dst)
        for src in glob.glob(os.path.join(HERE, 'src', sub, '*')):
            shutil.copy(src, os.path.join(OUT, sub, os.path.basename(src)))
            print(f'{sub}/{os.path.basename(src)}: Torment-only')
    missing = set(patches) - done
    if missing:
        raise SystemExit('patches without upstream file: ' + ', '.join(sorted(missing)))


def deploy():
    scripts = os.path.join(GAME, 'EEex_scripts')
    for f in glob.glob(os.path.join(scripts, '*.lua')):
        os.remove(f)
    for f in glob.glob(os.path.join(OUT, 'EEex_scripts', '*')):
        shutil.copy(f, scripts)
    os.makedirs(os.path.join(GAME, 'override'), exist_ok=True)
    for f in glob.glob(os.path.join(OUT, 'override', '*')):
        shutil.copy(f, os.path.join(GAME, 'override'))
    # IDS additions (installer's job in the release): Torment's own IDS + EEex's Torment ids (src/patch/*.IDS)
    import subprocess
    # dev only: test resources (bindings/test/dev_override/*, copied) and IDS lines (bindings/test/dev_patch/*.IDS)
    for f in glob.glob(os.path.join(HERE, r'..\bindings\test\dev_override', '*')):
        shutil.copy(f, os.path.join(GAME, 'override'))
    for f in glob.glob(os.path.join(HERE, 'src', 'patch', '*.IDS')) + glob.glob(os.path.join(HERE, r'..\bindings\test\dev_patch', '*.IDS')):
        name = os.path.basename(f)[:-4]
        base = subprocess.run([sys.executable, os.path.join(HERE, r'..\tools\bifextract.py'), GAME, name, 'ids'],
                              capture_output=True, text=True, encoding='latin-1').stdout
        ov = os.path.join(GAME, 'override', name + '.IDS')
        if os.path.exists(ov):
            os.remove(ov)
            base = subprocess.run([sys.executable, os.path.join(HERE, r'..\tools\bifextract.py'), GAME, name, 'ids'],
                                  capture_output=True, text=True, encoding='latin-1').stdout
        lines = base.rstrip('\r\n').split('\n')
        have = {l.strip() for l in lines}
        add = [l.strip() for l in open(f, encoding='latin-1') if l.strip() and l.strip() not in have]
        open(ov, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(lines + add) + '\n')
        print(f'override/{name}.IDS: +{len(add)}')
    ini = os.path.join(GAME, 'EEex.ini')
    if not os.path.exists(ini):
        shutil.copy(os.path.join(HERE, r'..\ref\EEex\EEex\loader\EEex.ini'), ini)
    # dev only: skip the intro movies (bindings/test/PTEE_SkipIntro.lua), loaded after EEex's startup
    with open(os.path.join(scripts, 'EEex_Main.lua'), 'a', encoding='utf-8', newline='\n') as m:
        m.write('\n-- EEex-PTEE dev deploy only\n')
        for dev in DEV_FILES:
            shutil.copy(os.path.join(HERE, r'..\bindings\test', dev + '.lua'), scripts)
            m.write(f'EEex_DoFile("{dev}")\n')
    print('deployed to', GAME)


if __name__ == '__main__':
    build()
    if '--deploy' in sys.argv:
        deploy()
