# Torment port of EEex's Lua (upstream ref/EEex/EEex/copy). The upstream files stay untouched; patched
# copies are written to eeexlua/generated/ (EEex_scripts/ and override/):
#  - eeexlua/patches/<file>.py: PATCHES = [(old, new), ...] for upstream <file> (exact, once; '@all:N old'
#    replaces exactly N occurrences; '@file' as old replaces the whole file with new);
#  - eeexlua/src/EEex_scripts/*, eeexlua/src/override/*: Torment-only files, copied as they are.
#   python build.py [--deploy]   (--deploy: copy to the dev game, tools/deploy.py's GAME)
import os, sys, glob, shutil, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.join(HERE, r'..\ref\EEex\EEex\copy')
OUT = os.path.join(HERE, 'generated')
GAME = r'E:\Enhanced Edition\Environnement de test\PTEE (EEex dev)'


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
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    done = set()
    for sub in ('EEex_scripts', 'override'):
        os.makedirs(os.path.join(OUT, sub))
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
    print('deployed to', GAME)


if __name__ == '__main__':
    build()
    if '--deploy' in sys.argv:
        deploy()
