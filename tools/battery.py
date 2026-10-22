# Run the dev test battery (bindings/test/PTEE_Battery.lua) end to end in the running dev game, keys sent with
# PostMessage (tools/gamekey.py: no focus change, nothing reaches other windows):
#   F9 start -> wait for the PAUSE after the rest step (quick save done by the battery) -> write the newest save's
#   folder name to EEex_scripts/PTEE_BatteryLoad.lua -> F6 load -> F9 resume -> wait for DONE -> print the results.
#   python tools/battery.py [--started]   (--started: the battery was started by hand, follow it)
import os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r'E:\Enhanced Edition\Environnement de test\PTEE (EEex dev)'
LOG = os.path.join(GAME, 'EEex_PTEE.log')
SAVES = os.path.join(os.path.expanduser('~'), r'Documents\Planescape Torment - Enhanced Edition\save')


def key(name):
    subprocess.run([sys.executable, os.path.join(HERE, 'gamekey.py'), name], check=True, capture_output=True)


def lines_since(pos):
    with open(LOG, encoding='latin-1', errors='replace') as f:
        f.seek(pos)
        return [l.rstrip('\n') for l in f.readlines() if 'PTEE-BATTERY' in l]


def wait_for(pos, word, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for l in lines_since(pos):
            if 'PTEE-BATTERY: ' + word in l:
                return True
        time.sleep(2)
    return False


def newest_file(d):
    # a save folder's own mtime does not change when a quick save rewrites its files: use its newest file
    files = [os.path.join(SAVES, d, f) for f in os.listdir(os.path.join(SAVES, d))]
    return max((os.path.getmtime(f) for f in files), default=0)


def save_dirs():
    return [d for d in os.listdir(SAVES) if os.path.isdir(os.path.join(SAVES, d))]


def newest_save_time():
    return max((newest_file(d) for d in save_dirs()), default=0)


def main():
    pos = os.path.getsize(LOG)
    if '--started' in sys.argv:
        # battery already started by hand: follow it from its last START in the log
        data = open(LOG, 'rb').read()
        pos = data.rfind(b'PTEE-BATTERY: START')
        if pos < 0:
            sys.exit('no START in the log')
    else:
        # F9 only works on the world screen: after a failed try, Escape closes whatever screen is open
        for i in range(20):
            if i:
                key('ESCAPE')
                time.sleep(1)
            key('F9')
            if wait_for(pos, 'START', 10):
                break
        else:
            sys.exit('battery did not start')
    if not wait_for(pos, 'PAUSE', 1500):
        sys.exit('no PAUSE (battery stuck?)')
    t_pause = time.time() - 30
    # the battery quick saves at the PAUSE; the engine refuses while enemies are around: retry (F4) until written
    for _ in range(12):
        time.sleep(5)
        if newest_save_time() > t_pause:
            break
        key('F4')
    else:
        sys.exit('no quick save written')
    newest = max(save_dirs(), key=newest_file)
    open(os.path.join(GAME, 'EEex_scripts', 'PTEE_BatteryLoad.lua'), 'w', encoding='utf-8').write(f'PTEE_BAT_LOAD = "{newest}"\n')
    key('F6')
    if not wait_for(pos, 'LOAD', 30):
        sys.exit('F6 load not seen')
    time.sleep(20)  # area loaded
    key('F9')
    if not wait_for(pos, 'DONE', 300):
        sys.exit('no DONE after the reload')
    for l in lines_since(pos):
        if re.search(r'PTEE-BATTERY: (PASS|FAIL|DONE|PAUSE|LOAD)', l):
            print(l.split('PTEE-BATTERY: ', 1)[1][:200])


if __name__ == '__main__':
    main()
