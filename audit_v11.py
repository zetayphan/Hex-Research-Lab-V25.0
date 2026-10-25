"""V11 empirical complete-record audit. No claim of native mathematical invertibility."""
import hashlib,json

def fingerprint(frame):
    return hashlib.sha256(json.dumps(frame,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def rgb(frame):
    values=frame['cells']
    return [sum((int(v)>>shift)&255 for v in values) for shift in (16,8,0)]

def structure(frame):
    v=frame['cells']
    return {'distinct':len(set(v)),'adjacent_changes':sum(a!=b for a,b in zip(v,v[1:]))}

def audit(capture,restore,step,steps=20):
    if type(steps)!=int or not 1<=steps<=500:raise ValueError('steps must be 1..500')
    initial=capture();records=[];seen={fingerprint(initial):0};prior=initial;recurrence=None
    try:
        restore(initial)
        if fingerprint(capture())!=fingerprint(initial):
            raise RuntimeError('Initial state restoration failed')
        for t in range(1,steps+1):
            step();cur=capture();before=rgb(prior);after=rgb(cur);key=fingerprint(cur)
            records.append({'step':t,'tick':cur.get('tick'),'fingerprint':key,'rgb_before':before,'rgb_after':after,'rgb_delta':[b-a for a,b in zip(before,after)],'rgb_conserved':before==after,'structural_before':structure(prior),'structural_after':structure(cur)})
            if key in seen and recurrence is None:recurrence={'first_seen':seen[key],'reappeared':t,'period':t-seen[key]}
            seen.setdefault(key,t);prior=cur
    finally:
        restore(initial)
    restored=fingerprint(capture())==fingerprint(initial)
    return {'steps':steps,'initial_fingerprint':fingerprint(initial),'restored':restored,'conserved_steps':sum(x['rgb_conserved'] for x in records),'nonconserved_steps':sum(not x['rgb_conserved'] for x in records),'recurrence':recurrence,'records':records,'limitations':['Recorded-frame recurrence is not necessarily complete-state recurrence.','Forward-state observation cannot establish existence of an inverse.','RGB conservation applies only to recorded transitions.','Uncaptured native or auxiliary state may affect future evolution.']}
