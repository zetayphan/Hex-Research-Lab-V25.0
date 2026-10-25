"""V9 pre-registered experimental plans and honest cross-run comparisons."""
import json, hashlib, datetime, math
from pathlib import Path
from hypothesis_v7 import load

def plan(steps=100,replicates=3,delay=0.1,seed_label='unspecified'):
    if type(steps)!=int or not 2<=steps<=10000: raise ValueError('steps must be 2..10000')
    if type(replicates)!=int or not 2<=replicates<=20: raise ValueError('replicates must be 2..20')
    if not isinstance(delay,(int,float)) or not math.isfinite(delay) or not 0<=delay<=10:raise ValueError('delay must be 0..10')
    if not isinstance(seed_label,str) or len(seed_label)>100:raise ValueError('invalid initial-state label')
    design={'version':'9.0','steps_per_run':steps,'replicates':replicates,'delay_seconds':delay,'initial_state_label':seed_label,'primary_outcome':'fraction of native steps preserving all three RGB totals','secondary_outcomes':['mean L1 RGB conservation error','mean absolute structural change'],'protocol':['Record the complete initial state or a validated reset procedure before each run.','Run the same number of steps for each replicate.','Do not treat successive steps as independent samples.','Reserve at least one run for held-out validation.'],'limitations':'This plan does not reset or seed the native engine. Replicates created sequentially can have different starting states. Independence and matched conditions must be established separately.'}
    design['plan_sha256']=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest()
    return design

def compare(folder,ids):
    if not 2<=len(ids)<=20 or len(set(ids))!=len(ids):raise ValueError('select 2..20 distinct runs')
    result=[]
    for rid in ids:
        rows=load(folder,rid)
        steps=[r for r in rows if r.get('index',0)>0]
        if not steps:raise ValueError('run has no measured steps: '+rid)
        errors=[float(r['prediction_error_l1']) for r in steps]
        if any(not math.isfinite(e) for e in errors):raise ValueError('non-finite error')
        changes=[r.get('delta_structure',{}) for r in steps]
        struct=[sum(abs(float(d.get(k,0))) for k in ('distinct','transitions','gradient')) for d in changes]
        result.append({'id':rid,'steps':len(steps),'rgb_conservation_fraction':sum(e==0 for e in errors)/len(errors),'mean_rgb_error_l1':sum(errors)/len(errors),'mean_structural_change_l1':sum(struct)/len(struct),'initial_tick':rows[0].get('tick'),'initial_state_hash':'unavailable: full state not recorded'})
    return {'version':'9.0','runs':result,'step_counts_matched':len(set(r['steps'] for r in result))==1,'conservation_fraction_range':[min(r['rgb_conservation_fraction'] for r in result),max(r['rgb_conservation_fraction'] for r in result)],'interpretation':'Descriptive run-level comparisons only. Initial states are not proven identical; these are not independent randomized replicates. No causal inference or mathematical proof.'}
