# Torment vtable structs for the PT header, from vtmap.json (vtsolve.py).
# A header vtbl struct lists the slots flat; each entry's `this` type is the class that introduced the
# virtual (the generator splits the list per class on it). For each introducing class T the PT index of
# its own slots is the consensus of every solved class that contains T (all must agree). Then:
#   - own slots are emitted in PT order, PT-only slots become `pstee_slot_<n>` placeholders,
#     slots removed in Torment are dropped;
#   - a class whose own slots are not all proven keeps them in BG order renamed `pstee_unproven_<name>`
#     (callable by nobody), and so does every descendant past that point.
# rewrite(text) -> text with the vtbl structs replaced; report in vtheader_report.json.
import os, re, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RX_VT = re.compile(r'struct /\*VFT\*/ (\w+)_vtbl\n\{\n(.*?)\n\};', re.S)
RX_ENTRY = re.compile(r'\(__\w+ \*([~\w]+)\)\((?:const )?(\w+) \*this')
# Interfaces implemented outside Torment.exe (steam_api64.dll, same Steamworks interface versions as
# BG2EE v2.6.6.0, see PLAN.md phase 4a): the vtable is the SDK's, identical by construction.
SAME_ABI = {'ISteamRemoteStorage', 'ISteamUGC', 'ISteamUserStats', 'ISteamUser', 'ISteamFriends', 'ISteamUtils',
            'ISteamApps', 'ISteamMatchmaking', 'ISteamNetworking', 'ISteamScreenshots', 'ISteamHTTP', 'ISteamController',
            'CCallbackBase'}
RX_BASE = re.compile(r'struct __cppobj (?:/\*VFT\*/ )?(?:__declspec\(align\(\d+\)\) )?(\w+) : (\w+)')


def solve(text):
    vt = {m.group(1): m.group(2).split('\n') for m in RX_VT.finditer(text)}
    base = dict(RX_BASE.findall(text))
    VM = json.load(open(os.path.join(HERE, 'vtmap.json')))

    def owner(ln):
        e = RX_ENTRY.search(ln)
        return e.group(2) if e else None

    # BG start index of each introducing class' own run, inside each flat list
    votes = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))  # T -> bg k -> {pt|'x'}
    ptlen = collections.defaultdict(collections.Counter)  # T -> PT index of the first slot after T's run
    for S, lines in vt.items():
        r = VM.get(S)
        if not r or not r.get('map'):
            continue
        own = [owner(l) for l in lines]
        for k, T in enumerate(own):
            if T is None or k >= len(r['map']):
                continue
            p, why = r['map'][k], r['proof'][k]
            if why == 'unresolved' or 'conflict' in why:
                continue
            votes[T][k][p if p is not None else 'x'] += 1
        # first slot of the next class' run gives the PT size of the previous runs
        for k in range(1, len(own)):
            if own[k] != own[k - 1] and own[k - 1] and r['map'][k] is not None and r['proof'][k] not in ('unresolved',) and 'conflict' not in r['proof'][k]:
                ptlen[own[k - 1]][r['map'][k]] += 1
    return vt, base, votes, ptlen, owner


def rewrite(text):
    vt, base, votes, ptlen, owner = solve(text)
    out, report = {}, {'proven': [], 'unproven': {}, 'moved': []}
    layout = {}   # T -> list of PT slots [(line or None)] for T's own run, with its PT start index

    def runs(lines):
        """[(T, [lines])] consecutive runs by introducing class."""
        rs = []
        for l in lines:
            T = owner(l)
            if rs and rs[-1][0] == T:
                rs[-1][1].append(l)
            else:
                rs.append((T, [l]))
        return rs

    def own_layout(T, lines, k0):
        """PT lines for T's own run (BG slots k0..), or None when not proven."""
        if T in layout:
            return layout[T]
        if T in SAME_ABI:
            layout[T] = (k0, k0 + len(lines), list(zip(range(k0, k0 + len(lines)), lines)))
            return layout[T]
        res = None
        V = votes.get(T, {})
        pts = []
        ok = True
        for d, l in enumerate(lines):
            c = V.get(k0 + d)
            if not c or len(c) != 1:
                ok = False; break
            pts.append(next(iter(c)))
        if ok:
            kept = [(p, l) for p, l in zip(pts, lines) if p != 'x']
            ps = [p for p, _ in kept]
            if len(set(ps)) == len(ps) and (not ps or ps == sorted(ps) or True):
                # PT end of the run: last own slot + 1; trailing PT-only slots (if any) are emitted as
                # placeholders by the descendant that shows them. Every descendant's first own slot
                # must lie at or after it.
                start = min(ps) if ps else None
                end = max(ps) + 1 if ps else None
                if end is not None and ptlen[T] and min(ptlen[T]) < end:
                    ok = False
                if ok:
                    res = (start, end, sorted(kept))
        layout[T] = res
        return res

    for S, lines in vt.items():
        rs = runs(lines)
        new, k, broken, moved = [], 0, False, False
        prev_end = 0
        for T, ls in rs:
            lay = None if broken or T is None else own_layout(T, ls, k)
            if lay is not None and lay[0] is not None and lay[0] < prev_end:
                lay = None
            if lay is None:
                broken = True
                report['unproven'].setdefault(S, T)
                new += [re.sub(r'\*([~\w]+)\)', lambda m: '*pstee_unproven_' + m.group(1).replace('~', 'dtor_') + ')', l, count=1) for l in ls]
            else:
                start, end, kept = lay
                start = prev_end if start is None else start
                byp = dict(kept)
                for p in range(prev_end, end if end is not None else prev_end):
                    if p in byp:
                        new.append(byp[p])
                    else:
                        new.append(f'\tvoid (__fastcall *pstee_slot_{p})({T} *this);')
                        moved = True
                if [l for _, l in kept] != [l for l in ls]:
                    moved = True
                prev_end = end if end is not None else prev_end
            k += len(ls)
        out[S] = new
        if S not in report['unproven']:
            report['proven'].append(S)
        if moved:
            report['moved'].append(S)

    def sub(m):
        return f'struct /*VFT*/ {m.group(1)}_vtbl\n{{\n' + '\n'.join(out[m.group(1)]) + '\n};'
    json.dump(report, open(os.path.join(HERE, 'vtheader_report.json'), 'w'), indent=0)
    return RX_VT.sub(sub, text), report


if __name__ == '__main__':
    p = os.path.join(HERE, r'..\..\ref\InfinityLoader\Core-Shared-Files\generate_bindings\in\Baldur-v2.6.6.0.h')
    t, rep = rewrite(open(p, encoding='utf-8', errors='ignore').read())
    print('proven', len(rep['proven']), 'unproven', len(rep['unproven']), 'moved', len(rep['moved']))
