# Show BG vs PT context for entries: python review.py <regex> [n] [--alt 0xPT]
import sys, re, json, subprocess
R = json.load(open('port2.json')); G = json.load(open('gen_report.json'))
n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 18
alt = sys.argv[sys.argv.index('--alt') + 1] if '--alt' in sys.argv else None
for name, r in G.items():
    if not re.search(sys.argv[1], name) or name not in R or 'bg_key' not in R[name]:
        continue
    pt = alt or r.get('site') or r.get('addr')
    print('#####', name, '|', r['status'], r.get('conf'), r.get('method'), '| bg', R[name]['bg_key'], 'pt', pt, r.get('note', ''))
    if pt:
        print(subprocess.run(['python', 'show.py', R[name]['bg_key'], pt, str(n), '--around'], capture_output=True, text=True).stdout)
