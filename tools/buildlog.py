# Summarize an MSBuild log: errors per file, missing members, other error kinds.
# Usage: python buildlog.py <log> [--all]
import re, sys, collections
L = open(sys.argv[1], encoding='utf-8', errors='ignore').read().splitlines()
errs = [l for l in L if ' error ' in l]
files, miss, other = collections.Counter(), collections.Counter(), collections.Counter()
for l in errs:
    m = re.search(r'[\\/]([^\\/(]+)\((\d+),\d+\): error (C\d+)', l)
    if m:
        files[m.group(1)] += 1
    m2 = re.search(r"'(\w+)' n'est pas membre de '([^']+)'", l)
    if m2:
        miss[(m2.group(2), m2.group(1))] += 1
    else:
        other[re.sub(r'\[.*', '', l.split(' error ', 1)[1])[:110]] += 1
print(len(errs), 'errors;', files.most_common(12))
print(len(miss), 'missing members')
for k, v in sorted(miss.items()):
    print('  ', k[0], k[1], v)
print('other:')
for k, v in other.most_common(40 if '--all' in sys.argv else 15):
    print('  ', v, k)
