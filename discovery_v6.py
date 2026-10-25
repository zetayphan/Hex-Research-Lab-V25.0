"""Exploratory, descriptive discovery from V5 JSONL runs; no theorem claims."""
import json, math, statistics
from pathlib import Path

def analyze(rows):
    if not rows: return {'samples':0,'findings':[],'trajectories':[]}
    rows=sorted(rows,key=lambda r:r.get('index',0))
    findings=[]
    steps=[r for r in rows if r.get('index',0)>0]
    errors=[float(r.get('prediction_error_l1') or 0) for r in steps]
    if steps:
        changed=sum(e>0 for e in errors)
        findings.append({'name':'RGB conservation hypothesis','observed':f'{len(steps)-changed}/{len(steps)} measured steps conserved RGB totals','status':'observed all steps' if changed==0 else 'counterexamples observed','evidence':{'changed_steps':changed,'total_error_l1':sum(errors)}})
    for field in ('distinct_hex_values','adjacent_value_transitions','adjacent_rgb_gradient'):
        values=[float(r[field]) for r in rows if isinstance(r.get(field),(int,float)) and math.isfinite(r[field])]
        if len(values)<2:continue
        diffs=[b-a for a,b in zip(values,values[1:])]
        findings.append({'name':field+' trajectory','observed':f'initial={values[0]:.5g}; final={values[-1]:.5g}; range=[{min(values):.5g}, {max(values):.5g}]','status':'descriptive pattern','evidence':{'net_change':values[-1]-values[0],'direction_changes':sum(a*b<0 for a,b in zip(diffs,diffs[1:])),'constant':all(v==values[0] for v in values)}})
    # Exact repeated signatures indicate recurrence only in measured projections, not complete engine state.
    seen={}; repeats=[]
    for r in rows:
        sig=tuple(r.get(k) for k in ('distinct_hex_values','adjacent_value_transitions','adjacent_rgb_gradient'))
        if None in sig:continue
        if sig in seen:repeats.append({'first':seen[sig],'again':r.get('index')})
        else:seen[sig]=r.get('index')
    if repeats:findings.append({'name':'Repeated structural signatures','observed':f'{len(repeats)} repeated metric signatures','status':'projection recurrence only','evidence':{'examples':repeats[:10]}})
    return {'samples':len(rows),'steps':len(steps),'findings':findings,'trajectories':[{k:r.get(k) for k in ('index','tick','distinct_hex_values','adjacent_value_transitions','adjacent_rgb_gradient','prediction_error_l1')} for r in rows], 'limitations':'Exploratory summaries of observed samples. Repeated metrics do not prove complete-state recurrence, causality, dimensional rank, or new mathematical laws.'}

def analyze_file(path):
    path=Path(path)
    with path.open(encoding='utf-8') as f:rows=[json.loads(line) for line in f if line.strip()]
    return analyze(rows)

def compare(folder, ids):
    folder=Path(folder)
    if not 1<=len(ids)<=8:raise ValueError('Select 1..8 run IDs')
    out=[]
    for run_id in ids:
        if not isinstance(run_id,str) or not run_id or any(c not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-' for c in run_id):raise ValueError('Invalid run ID')
        path=folder/(run_id+'.jsonl')
        if not path.is_file():raise ValueError('Run not found: '+run_id)
        report=analyze_file(path)
        out.append({'id':run_id,**report})
    return {'runs':out,'warning':'Comparisons are descriptive; runs may have different initial states and settings.'}
