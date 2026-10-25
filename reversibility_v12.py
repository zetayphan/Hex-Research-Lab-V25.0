"""V12: empirical observability checks and proven reversible reference map."""
import copy, hashlib, json

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def forward_reference(values):
    if not isinstance(values,list) or not values or any(type(v)!=int or not 0<=v<2**24 for v in values):
        raise ValueError('Expected nonempty list of 24-bit integers')
    return values[-1:]+values[:-1]

def inverse_reference(values):
    return values[1:]+values[:1]

def investigate(capture,restore,step,steps=12):
    if type(steps)!=int or not 1<=steps<=100:raise ValueError('steps must be 1..100')
    baseline=copy.deepcopy(capture()); baseline_id=digest(baseline)
    traces=[]; restore_checks=[]
    try:
        for trial in range(2):
            restore(copy.deepcopy(baseline))
            restore_checks.append(digest(capture())==baseline_id)
            trajectory=[digest(capture())]
            for _ in range(steps):
                step();trajectory.append(digest(capture()))
            traces.append(trajectory)
    finally:
        restore(copy.deepcopy(baseline))
    reference=baseline['cells'][:]
    roundtrip=inverse_reference(forward_reference(reference))==reference
    matches=sum(a==b for a,b in zip(*traces))
    return {'steps':steps,'reference_roundtrip':roundtrip,'restore_checks':restore_checks,
            'matching_frames':matches,'compared_frames':steps+1,
            'serialized_repeatability':matches==steps+1 and all(restore_checks),
            'final_restoration':digest(capture())==baseline_id,
            'reference_model':'cyclic permutation of 24-bit cell values',
            'native_inverse_verified':False,
            'complete_state_verified':False,
            'limitations':['The inverse applies only to the reference permutation, not to the native 17-stage engine.',
            'Matching serialized frames cannot rule out hidden native or auxiliary state.',
            'Restoration of serialized state is not mathematical inversion of native evolution.',
            'Two repeatable trials do not prove determinism for all states.']}
