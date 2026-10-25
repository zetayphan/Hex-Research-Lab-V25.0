"""V3: distinguish exact reference proofs from observational native-engine checks."""
import math
from research_metrics import summarize_state

def reference_cycle():
    states=[]; s=(4,0,0)
    for _ in range(3):
        states.append({'state':list(s),'invariant':sum(s),'phi':s[0]+2*s[1]+3*s[2]})
        s=(s[2],s[0],s[1])
    return {'pass':s==(4,0,0) and all(v['invariant']==4 for v in states),
            'inverse_pass':all((lambda x:(x[1],x[2],x[0]))((x[2],x[0],x[1]))==x for x in [tuple(v['state']) for v in states]),
            'states':states,'scope':'exact finite permutation example, not the native engine'}

def matrix_rank(rows,tolerance=1e-8):
    if not rows:return 0
    a=[list(map(float,r)) for r in rows]; n=len(a);m=len(a[0]);rank=0
    if any(len(r)!=m for r in a):raise ValueError('ragged matrix')
    for col in range(m):
        pivot=max(range(rank,n),key=lambda i:abs(a[i][col]),default=rank)
        if rank==n:break
        if abs(a[pivot][col])<=tolerance:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        z=a[rank][col];a[rank]=[v/z for v in a[rank]]
        for i in range(n):
            if i!=rank:
                f=a[i][col];a[i]=[x-f*y for x,y in zip(a[i],a[rank])]
        rank+=1
    return rank

def structural_map(p):
    x,y,z=p
    return [x+y, y+z, x*x+z]

def jacobian(p,dimensions=3,h=1e-5):
    rows=[]
    for i in range(dimensions):
        q=list(p);r=list(p);q[i]+=h;r[i]-=h
        plus=structural_map(q);minus=structural_map(r)
        rows.append([(a-b)/(2*h) for a,b in zip(plus,minus)])
    return [list(col) for col in zip(*rows)]

def rank_demonstration(p=(1.,2.,3.)):
    j=jacobian(p); old=matrix_rank(j[:2]);new=matrix_rank(j)
    return {'point':list(p),'jacobian':j,'rank_before':old,'rank_after':new,
            'rank_expands':new==old+1,'scope':'differentiable surrogate only; not native state dimension'}

def compare_snapshots(before,after):
    a=summarize_state(before);b=summarize_state(after)
    if a['cells']!=b['cells']:raise ValueError('cell count changed')
    return {'ticks':[a['tick'],b['tick']],'changed_cells':sum(x!=y for x,y in zip(before['values'],after['values'])),
            'rgb_delta':[y-x for x,y in zip(a['rgb_totals'],b['rgb_totals'])],
            'rgb_conserved':a['rgb_totals']==b['rgb_totals'],
            'structural_delta':{'distinct_hex_values':b['distinct_hex_values']-a['distinct_hex_values'],
            'adjacent_value_transitions':b['adjacent_value_transitions']-a['adjacent_value_transitions']},
            'reversibility':'not tested: no verified complete-state inverse',
            'scope':'observational comparison of native engine states; no proof of theorem hypotheses'}

def report(snapshot=None):
    out={'reference_permutation':reference_cycle(),'structural_rank_surrogate':rank_demonstration(),
         'native_engine_claims':{'conservation':'not established for full engine',
         'reversibility':'not established for full engine',
         'dimensional_expansion':'not established for full engine'}}
    if snapshot is not None:out['live_observation']=summarize_state(snapshot)
    return out
