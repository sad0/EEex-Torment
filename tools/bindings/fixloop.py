# Compile dump.cpp repeatedly, commenting out lines that error, until it builds (max 30 rounds).
import re, subprocess, sys
bat = sys.argv[1]; cpp = sys.argv[2]
for r in range(30):
    subprocess.run(['powershell', '-c', f"cmd /c '\"{bat}\"'"], capture_output=True)
    log = open('cl.log', encoding='mbcs', errors='ignore').read()
    bad = {int(m.group(1)) for m in re.finditer(r'^dump\.cpp\((\d+)\)', log, re.M)}
    hdr = re.findall(r'^(\S+\.h)\((\d+)\).*error', log, re.M)
    print('round', r, 'bad lines', len(bad), 'header errors', len(hdr))
    if hdr and not bad:
        print(hdr[:5]); break
    if not bad:
        break
    L = open(cpp).read().split('\n')
    for b in bad:
        if 0 < b <= len(L) and not L[b - 1].startswith('//') and b > 8:
            L[b - 1] = '//' + L[b - 1]
    open(cpp, 'w').write('\n'.join(L))
