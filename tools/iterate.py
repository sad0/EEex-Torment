# Re-run call-graph propagation from every mapped function, then link-order gap filling.
import json
from globalmap import propagate
import globalmap3

J = json.load(open('fmap.json'))
known = {int(k, 16): int(v[0], 16) for k, v in J.items()}
meth = {int(k, 16): v[1] for k, v in J.items()}
propagate(known, meth, dict(known), tag='reprop')
json.dump({hex(k): [hex(v), meth[k]] for k, v in known.items()}, open('fmap.json', 'w'), indent=0)
globalmap3.main()
