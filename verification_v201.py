"""V20.1 observation-level verification; never asserts a universal theorem."""
import hashlib, json

def native_state_fingerprint(raw):
    return hashlib.sha256(raw).hexdigest()

def channel_totals(cells):
    return {c:sum((int(v) >> shift)&255 for v in cells) for c,shift in [('R',16),('G',8),('B',0)]}

def structure(cells):
    return {'distinct_values':len(set(cells)), 'adjacent_transitions':sum(a!=b for a,b in zip(cells,cells[1:]))}

def evaluate_transition(before,after):
    a,b=before['cells'],after['cells']
    if len(a)!=len(b):raise ValueError('Mismatched cell counts')
    ia,ib=channel_totals(a),channel_totals(b)
    delta={c:ib[c]-ia[c] for c in ia}
    sa,sb=structure(a),structure(b)
    return {'tick_before':before['tick'],'tick_after':after['tick'],'rgb_before':ia,'rgb_after':ib,'rgb_delta':delta,'rgb_conserved_observed':all(v==0 for v in delta.values()),'structure_before':sa,'structure_after':sb,'structure_changed_observed':sa!=sb,'classification':'OBSERVED_PASS' if all(v==0 for v in delta.values()) else 'OBSERVED_COUNTEREXAMPLE'}

def coverage_report(frame,native_bytes):
    return {'native_state_struct_bytes':native_bytes,'native_fields':['cells','stages','stage_changes','tick','checksum','flags','dimension','count'],'serialized_fields':sorted(frame),'not_guaranteed':['C static trace buffers and configuration','Python global counters and experimental histories','background worker scheduling','future-relevant external files and auxiliary state'],'claim':'Partial documented coverage; complete state restoration unproven.'}
