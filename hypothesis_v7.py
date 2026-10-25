"""V7: exploratory hypotheses with held-out run validation, not mathematical proof."""
import json, math
from pathlib import Path
from discovery_v6 import compare
FIELDS=('distinct_hex_values','adjacent_value_transitions','adjacent_rgb_gradient')
def load(folder, run_id):
    return [json.loads(x) for x in (Path(folder)/(run_id+'.jsonl')).read_text().splitlines() if x.strip()]
def evaluate(folder, ids):
    if len(ids)<2 or len(ids)>8: raise ValueError('Select 2..8 runs: first for discovery, remaining for independent validation')
    compare(folder,ids)  # validates IDs and file existence
    train=load(folder,ids[0]); tests=[load(folder,x) for x in ids[1:]]
    def steps(rows):
        return [r for r in rows if isinstance(r.get('index'),int) and r['index']>0]
    hypotheses=[]
    trainsteps=steps(train)
    if not trainsteps:raise ValueError('Discovery run has no measured steps')
    # Candidate conservation only if all observed training steps conserve.
    if all(r.get('prediction_error_l1')==0 for r in trainsteps):
        hypotheses.append(('RGB total conservation',lambda r:r.get('prediction_error_l1')==0,'All RGB totals remain constant at each recorded step'))
    for field in FIELDS:
        pairs=[(a.get(field),b.get(field)) for a,b in zip(train,train[1:])]
        if pairs and all(isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isfinite(a) and math.isfinite(b) for a,b in pairs):
            if all(b==a for a,b in pairs):hypotheses.append((field+' remains constant',lambda r,f=field:r.get('delta_structure',{}).get({'distinct_hex_values':'distinct','adjacent_value_transitions':'transitions','adjacent_rgb_gradient':'gradient'}[f])==0,'Structural measurement does not change between steps'))
            elif all(b>=a for a,b in pairs):hypotheses.append((field+' is nondecreasing',lambda r,f=field:r.get('delta_structure',{}).get({'distinct_hex_values':'distinct','adjacent_value_transitions':'transitions','adjacent_rgb_gradient':'gradient'}[f],float('-inf'))>=0,'Structural measurement never decreases'))
            elif all(b<=a for a,b in pairs):hypotheses.append((field+' is nonincreasing',lambda r,f=field:r.get('delta_structure',{}).get({'distinct_hex_values':'distinct','adjacent_value_transitions':'transitions','adjacent_rgb_gradient':'gradient'}[f],float('inf'))<=0,'Structural measurement never increases'))
    reports=[]
    for name,pred,description in hypotheses:
        per=[]
        for rid,rows in zip(ids[1:],tests):
            sample=steps(rows); passed=sum(bool(pred(r)) for r in sample)
            per.append({'id':rid,'tested':len(sample),'passed':passed,'counterexamples':len(sample)-passed})
        n=sum(x['tested'] for x in per); failures=sum(x['counterexamples'] for x in per)
        reports.append({'hypothesis':name,'description':description,'status':'counterexample observed' if failures else ('held-out observations consistent' if n else 'insufficient validation data'),'validation_steps':n,'counterexamples':failures,'runs':per})
    return {'discovery_run':ids[0],'validation_runs':ids[1:],'discovery_steps':len(trainsteps),'hypotheses':reports,'limitations':'Exploratory selection on first run; later runs are held-out only if their generation was independent of hypothesis selection. Zero counterexamples is not a mathematical proof. Different initial conditions and engine settings may confound results. No native reversibility or Jacobian rank claim.'}
