# Run the dev test battery (bindings/test/PTEE_Battery.lua) end to end in the running dev game, keys sent with
# PostMessage (tools/gamekey.py: no focus change, nothing reaches other windows):
#   F9 start -> wait for the PAUSE after the rest step (quick save done by the battery) -> write the newest save's
#   folder name to EEex_scripts/PTEE_BatteryLoad.lua -> F6 load -> F9 resume -> wait for DONE -> print the results.
#   python tools/battery.py [--from-log]
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


def main():
    pos = os.path.getsize(LOG)
    # F9 is ignored until the world screen is up (save still loading): resend until the battery starts
    for _ in range(20):
        key('F9')
        if wait_for(pos, 'START', 10):
            break
    else:
        sys.exit('battery did not start')
    if not wait_for(pos, 'PAUSE', 1500):
        sys.exit('no PAUSE (battery stuck?)')
    time.sleep(5)   # quick save written
    newest = max((d for d in os.listdir(SAVES) if os.path.isdir(os.path.join(SAVES, d))),
                 key=lambda d: os.path.getmtime(os.path.join(SAVES, d)))
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
