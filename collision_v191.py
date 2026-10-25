"""Bounded source-aligned collision search; a witness proves non-injectivity only for the isolated tested stage."""
import hashlib, itertools, random, time
from native_v14 import forward
from native_stage_v13 import SOURCE, NEIGHBOR, MASK, NAMES

def investigate(stage, dimension=2, alphabet=(0,1), random_trials=2000, seed=19, flags=1):
    if type(stage) is not int or stage not in NEIGHBOR: raise ValueError('Select a coupled stage: 0,3,4,7,10,11')
    if dimension != 2: raise ValueError('V19.1 bounded search supports a 2x2x2 lattice only')
    if type(random_trials) is not int or not 0 <= random_trials <= 100000: raise ValueError('random_trials must be 0..100000')
    if type(seed) is not int or not 0 <= seed < 2**64: raise ValueError('Invalid seed')
    if type(flags) is not int or flags not in (0,1): raise ValueError('flags must be 0 or 1')
    if not isinstance(alphabet,(tuple,list)) or not 1 <= len(alphabet) <= 4 or any(type(x) is not int or not 0 <= x <= MASK for x in alphabet) or len(set(alphabet))!=len(alphabet): raise ValueError('Use 1-4 distinct 24-bit alphabet values')
    if len(alphabet)**8 > 65536: raise ValueError('Exhaustive alphabet is too large')
    seen={};checked=0;collision=None;mode='exhaustive restricted-input enumeration'
    def probe(a):
        nonlocal checked,collision
        out=tuple(forward(stage,a,dimension,flags))
        checked+=1
        prev=seen.get(out)
        if prev is not None and prev!=a:
            collision={'input_a':[f'{v:06X}' for v in prev],'input_b':[f'{v:06X}' for v in a], 'shared_output':[f'{v:06X}' for v in out]}
            return True
        seen[out]=a
        return False
    for vals in itertools.product(alphabet,repeat=8):
        if probe(vals):break
    exhaustive_completed=collision is None
    if collision is None and random_trials:
        mode='restricted enumeration plus randomized 24-bit sampling'
        rng=random.Random(seed)
        # Random samples may find a collision; failure to find one is inconclusive.
        for _ in range(random_trials):
            if probe(tuple(rng.getrandbits(24) for _ in range(8))):break
    result={'schema':'hex-v19.1-collision-audit','stage':stage,'stage_name':NAMES[stage], 'dimension':dimension,'flags':flags,'alphabet':[f'{x:06X}' for x in alphabet], 'random_seed':seed,'random_trials_requested':random_trials,'tested_inputs':checked,'restricted_enumeration_completed':exhaustive_completed,'collision':collision,'classification':'NON_INJECTIVE_WITNESS' if collision else 'UNRESOLVED_NO_COLLISION_FOUND','mode':mode,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'scope':'Isolated simultaneous 24-bit coupled stage, 2x2x2 lattice, fixed flags. A distinct-input equal-output witness proves this isolated stage is non-injective for this dimension. No witness does NOT prove injectivity; does not establish full native-engine reversibility.','full_engine_reversibility_verified':False}
    return result
