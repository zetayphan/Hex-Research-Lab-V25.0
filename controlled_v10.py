"""V10 controlled repeatability trials. Requires exclusive native engine lock."""
import hashlib,json

def digest(frame):
    return hashlib.sha256(json.dumps(frame,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def trial(capture,restore,step,replicates=3,steps=10):
    if type(replicates)!=int or not 2<=replicates<=12:raise ValueError('replicates must be 2..12')
    if type(steps)!=int or not 1<=steps<=200:raise ValueError('steps must be 1..200')
    baseline=capture()
    traces=[]
    try:
        for _ in range(replicates):
            restore(baseline)
            trace=[digest(capture())]
            for _ in range(steps):
                step();trace.append(digest(capture()))
            traces.append(trace)
    finally:
        restore(baseline)
    matches=[sum(a==b for a,b in zip(traces[0],t)) for t in traces]
    return {'replicates':replicates,'steps':steps,'initial_fingerprint':digest(baseline),'matching_frames_per_replica':matches,'frames_per_replica':steps+1,'repeatable':all(m==steps+1 for m in matches),'restored_initial_state':digest(capture())==digest(baseline),'note':'Tests repeatability of serialized native state and configuration; does not prove full engine invertibility.'}
