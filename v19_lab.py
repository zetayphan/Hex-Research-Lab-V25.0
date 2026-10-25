"""V19 experiment math: deterministic fingerprints and RGB conservation checks."""
import hashlib,json

def fingerprint(frame):
    fields={k:frame[k] for k in ('cells','stages','stage_changes','tick','checksum','flags')}
    return hashlib.sha256(json.dumps(fields,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def rgb_totals(cells):
    return [sum((int(x)>>shift)&255 for x in cells) for shift in (16,8,0)]

def audit(before,after):
    a,b=rgb_totals(before['cells']),rgb_totals(after['cells'])
    delta=[y-x for x,y in zip(a,b)]
    return {'before_rgb':a,'after_rgb':b,'delta_rgb':delta,'conserved':all(v==0 for v in delta),'changed_cells':sum(x!=y for x,y in zip(before['cells'],after['cells'])),'before_fingerprint':fingerprint(before),'after_fingerprint':fingerprint(after)}
