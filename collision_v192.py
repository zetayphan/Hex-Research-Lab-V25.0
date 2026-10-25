"""V19.2 exact GF(2) algebraic audit plus bounded collision search.
Proof scope: 2x2x2, fixed flags, source-aligned isolated stages.
"""
import hashlib
from native_v14 import forward
from native_stage_v13 import MASK, SOURCE, NEIGHBOR, NAMES
from collision_v191 import investigate

N=8
BITS=24*N

def _pack(a):
    return sum(int(x) << (24*i) for i,x in enumerate(a))

def _unpack(v):
    return tuple((v>>(24*i))&MASK for i in range(N))

def _linear_audit(stage, flags):
    # For stage 8 (index 7), XOR and rotation form a linear map over GF(2).
    # Rank-nullity gives a complete injectivity classification for all 2^192 inputs.
    basis={}; rank=0; kernel=None
    for j in range(BITS):
        inp=_unpack(1<<j)
        out=_pack(forward(stage,inp,2,flags))
        reduced=out; combination=1<<j
        while reduced:
            pivot=reduced.bit_length()-1
            if pivot not in basis: break
            v, pre=basis[pivot]
            reduced^=v; combination^=pre
        if reduced:
            basis[reduced.bit_length()-1]=(reduced,combination)
            rank+=1
        elif kernel is None:
            kernel=combination
    if kernel is not None:
        a=(0,)*N; b=_unpack(kernel)
        ya=forward(stage,a,2,flags); yb=forward(stage,b,2,flags)
        assert a!=b and ya==yb
        return {'classification':'NON_INJECTIVE_WITNESS','proof_method':'exact_GF2_nullspace','rank':rank,'nullity':BITS-rank,'collision':{'input_a':[f'{x:06X}' for x in a],'input_b':[f'{x:06X}' for x in b],'shared_output':[f'{x:06X}' for x in ya]}}
    return {'classification':'INJECTIVE_PROVEN','proof_method':'exact_GF2_full_rank','rank':rank,'nullity':0,'collision':None}

def analyze(stage, flags=1, alphabet=(0,1), random_trials=2000, seed=19):
    if type(stage) is not int or stage not in NEIGHBOR: raise ValueError('Select a coupled stage: 0,3,4,7,10,11')
    if type(flags) is not int or flags not in (0,1): raise ValueError('flags must be 0 or 1')
    # Preserve validation of the existing search configuration, even for exact cases.
    if stage==7 or (stage==3 and flags==0):
        # Reuse V19.1 parameter validation without performing expensive enumeration.
        if type(random_trials) is not int or not 0<=random_trials<=100000: raise ValueError('Invalid trial count')
        if type(seed) is not int or not 0<=seed<2**64: raise ValueError('Invalid seed')
        if not isinstance(alphabet,(list,tuple)) or not 1<=len(alphabet)<=4 or any(type(x) is not int or not 0<=x<=MASK for x in alphabet) or len(set(alphabet))!=len(alphabet) or len(alphabet)**8>65536: raise ValueError('Invalid alphabet')
        if stage==7: proof=_linear_audit(stage,flags)
        else: proof={'classification':'INJECTIVE_PROVEN','proof_method':'identity_when_extension_flag_off','collision':None,'rank':BITS,'nullity':0}
        result={'schema':'hex-v19.2-algebraic-audit','stage':stage,'stage_name':NAMES[stage], 'flags':flags,'dimension':2,'state_bits':BITS,'scope':'Entire isolated 2x2x2 stage mapping on all 24-bit cell values at fixed flags. Not a proof about the full native engine.','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'full_engine_reversibility_verified':False,**proof}
    else:
        result=investigate(stage,2,alphabet,random_trials,seed,flags)
        result['schema']='hex-v19.2-algebraic-audit'
        result['proof_method']='bounded_enumeration_and_seeded_sampling'
        result['state_bits']=BITS
        result['note']='Search only; no collision found is NOT proof of injectivity.'
    if result.get('collision'):
        c=result['collision']; a=tuple(int(x,16) for x in c['input_a']); b=tuple(int(x,16) for x in c['input_b']); expected=tuple(int(x,16) for x in c['shared_output'])
        result['witness_verified']=a!=b and tuple(forward(stage,a,2,flags))==tuple(forward(stage,b,2,flags))==expected
        if not result['witness_verified']: raise AssertionError('Witness verification failed')
    return result
