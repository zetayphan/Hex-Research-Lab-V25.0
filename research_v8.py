"""V8 reproducible exploratory reports; evidence is observational, never proof."""
import json, math, hashlib, datetime
from pathlib import Path
from hypothesis_v7 import evaluate, load

def report(folder, ids):
    base=evaluate(folder,ids)
    checks=[]
    for h in base['hypotheses']:
        n=h['validation_steps']; k=n-h['counterexamples']
        # Wilson 95% descriptive interval; steps may be correlated.
        if n:
            z=1.96;p=k/n;den=1+z*z/n
            center=(p+z*z/(2*n))/den
            margin=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
            interval=[round(max(0,center-margin),4),round(min(1,center+margin),4)]
        else:interval=None
        checks.append({**h,'observed_accuracy':round(k/n,4) if n else None,'wilson95_descriptive':interval,'assessment':('contradicted in held-out observations' if h['counterexamples'] else 'not falsified in available held-out observations' if n else 'untested')})
    sources=[]
    for rid in ids:
        path=Path(folder)/(rid+'.jsonl')
        sources.append({'run':rid,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':len(load(folder,rid))})
    return {'version':'8.0','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':sources,'discovery_run':ids[0],'validation_runs':ids[1:],'hypotheses':checks,'next_experiments':['Collect fresh runs with precommitted initial conditions and settings.','Replicate on independent seeds and compare counterexample rates.','Test full-state reversibility separately; do not infer it from RGB totals.'],'caveat':'Exploratory evidence only. Repeated steps may be correlated; Wilson intervals are descriptive, not calibrated confidence for dependent observations. Runs may differ in initial conditions. No mathematical proof or automated experimental execution is claimed.'}

def markdown(r):
    lines=['# Hex Unified Research Lab V8 — Research Report','',f"Generated UTC: {r['created_utc']}",'',f"Discovery: `{r['discovery_run']}`",f"Validation: {', '.join(r['validation_runs'])}",'','## Evidence provenance']
    for s in r['sources']:lines.append(f"- `{s['run']}`: {s['records']} records; SHA-256 `{s['sha256']}`")
    lines+=['','## Hypotheses']
    for h in r['hypotheses']:
        lines+=['',f"### {h['hypothesis']}",f"Status: {h['assessment']}",f"Validation: {h['validation_steps']} steps, {h['counterexamples']} counterexamples",f"Observed accuracy: {h['observed_accuracy']}; descriptive Wilson interval: {h['wilson95_descriptive']}"]
    lines+=['','## Suggested follow-up experiments']+['- '+x for x in r['next_experiments']]+['','## Limitations',r['caveat']]
    return '\n'.join(lines)+'\n'
