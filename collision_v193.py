"""V19.3 exact bit-vector collision search for isolated 2x2x2 stages.
An SMT SAT witness is independently checked against the source-aligned Python stage model.
UNSAT proves injectivity for the specified fixed 192-bit model; UNKNOWN proves nothing.
"""
import hashlib
from native_v14 import forward, neighbors
from native_stage_v13 import MASK, SOURCE, NEIGHBOR, NAMES
from collision_v192 import analyze as previous_analyze


def analyze(stage, flags=1, timeout_ms=5000, fallback_trials=1000, seed=19):
    if type(stage) is not int or stage not in NEIGHBOR: raise ValueError('Invalid coupled stage')
    if type(flags) is not int or flags not in (0,1): raise ValueError('Invalid flags')
    if type(timeout_ms) is not int or not 100 <= timeout_ms <= 60000: raise ValueError('timeout_ms must be 100..60000')
    if type(fallback_trials) is not int or not 0 <= fallback_trials <= 100000: raise ValueError('Invalid trials')
    if type(seed) is not int or not 0 <= seed < 2**64: raise ValueError('Invalid seed')
    base={'schema':'hex-v19.3-symbolic-audit','stage':stage,'stage_name':NAMES[stage],
          'flags':flags,'state_bits':192,'dimension':2,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'scope':'Isolated source-aligned 2x2x2 stage, 24-bit cells, fixed flags; NOT full native engine',
          'full_engine_reversibility_verified':False,'solver_timeout_ms':timeout_ms}
    # Retain established exact classifications without rerunning a solver.
    if stage==7 or (stage==3 and flags==0):
        result=previous_analyze(stage,flags,random_trials=0)
        return {**base,**{k:v for k,v in result.items() if k in ('classification','proof_method','rank','nullity','collision','witness_verified')}}
    try:
        import z3
    except ImportError:
        result=previous_analyze(stage,flags,random_trials=fallback_trials,seed=seed)
        return {**base,'classification':result['classification'], 'proof_method':'bounded_search_no_z3',
                'collision':result.get('collision'),'witness_verified':result.get('witness_verified',False),
                'note':'Install z3-solver to enable exact symbolic checks; no collision found is inconclusive.'}
    a=[z3.BitVec(f'a{i}',24) for i in range(8)]
    b=[z3.BitVec(f'b{i}',24) for i in range(8)]
    def rol(x,n):return z3.RotateLeft(x,n)
    def transform(x):
        out=[]
        for i,v in enumerate(x):
            l,r,u,d=neighbors(x,i,2)
            if stage==0: w=v+rol(r,1)
            elif stage==3: w=v+z3.ZeroExt(16,z3.Extract(7,0,l^r)) if flags else v
            elif stage==4: w=v+l-r
            elif stage==7: w=v^rol(l,3)
            elif stage==10: w=v+rol(r^u^d,i%7+1)
            else: w=v^(l+r+u+d)
            out.append(w)
        return out
    solver=z3.Solver();solver.set('timeout',timeout_ms)
    solver.add(z3.Or(*[a[i]!=b[i] for i in range(8)]))
    solver.add(*[x==y for x,y in zip(transform(a),transform(b))])
    status=solver.check()
    if status==z3.unsat:
        return {**base,'classification':'INJECTIVE_PROVEN','proof_method':'SMT_BV_UNSAT','collision':None,
                'note':'Proof covers the specified finite isolated stage model only.'}
    if status==z3.sat:
        model=solver.model()
        aa=tuple(model.eval(x,model_completion=True).as_long() for x in a)
        bb=tuple(model.eval(x,model_completion=True).as_long() for x in b)
        ya=tuple(forward(stage,aa,2,flags));yb=tuple(forward(stage,bb,2,flags))
        if aa==bb or ya!=yb:raise AssertionError('SMT witness failed independent Python verification')
        return {**base,'classification':'NON_INJECTIVE_WITNESS','proof_method':'SMT_BV_SAT_verified',
                'witness_verified':True,'collision':{'input_a':[f'{v:06X}' for v in aa],
                'input_b':[f'{v:06X}' for v in bb], 'shared_output':[f'{v:06X}' for v in ya]}}
    return {**base,'classification':'UNRESOLVED_SOLVER_UNKNOWN','proof_method':'SMT_BV_TIMEOUT_OR_UNKNOWN',
            'solver_reason':solver.reason_unknown(),'collision':None,
            'note':'Timeout or unknown is not evidence of injectivity.'}
