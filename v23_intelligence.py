"""Read-only evidence analysis of V22 jobs and V20.2 native playback records."""
import json, pathlib, hashlib, datetime

def analyze(root):
    root=pathlib.Path(root)
    jobs_dir=root/'research_data/v22/jobs'
    playback_dir=root/'research_data/v202/playback'
    jobs=[]; evidence=[]; warnings=[]
    for p in sorted(jobs_dir.glob('*.json')) if jobs_dir.exists() else []:
        try:
            j=json.loads(p.read_text()); jobs.append(j)
        except (ValueError,OSError): warnings.append('Unreadable job: '+p.name)
    for j in jobs:
        for result in j.get('results',[]):
            rid=result.get('experiment_id')
            if not isinstance(rid,str):continue
            # Experiment IDs and playback IDs need not coincide. Search recorded reports by IDs, but never invent a match.
            for p in playback_dir.glob('*.json') if playback_dir.exists() else []:
                try:
                    data=json.loads(p.read_text())
                except (ValueError,OSError):continue
                if data.get('experiment_id')==rid or data.get('id')==rid or p.stem==rid:
                    evidence.append((j['id'],p,data))
    # Include independently saved playback recordings as separate observations, deduplicated by file path.
    seen={str(p) for _,p,_ in evidence}
    for p in sorted(playback_dir.glob('*.json')) if playback_dir.exists() else []:
        if str(p) in seen:continue
        try:evidence.append((None,p,json.loads(p.read_text())))
        except (ValueError,OSError):warnings.append('Unreadable playback: '+p.name)
    summaries=[]
    for job_id,p,data in evidence:
        records=data.get('records',data.get('trace',[]))
        if not records and isinstance(data.get('cells'),list):records=[r for group in data['cells'] if isinstance(group,dict) for r in group.get('records',[])]
        if not isinstance(records,list):records=[]
        valid=[r for r in records if isinstance(r,dict) and isinstance(r.get('input'),int) and isinstance(r.get('output'),int)]
        changed=sum(r['input']!=r['output'] for r in valid)
        summaries.append({'id':p.stem,'job_id':job_id,'records':len(valid),'changed':changed,'unchanged':len(valid)-changed,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    # Held-out evidence: compare first vs remaining recordings, never reuse discovery record as validation.
    discovery=summaries[0] if summaries else None
    validation=summaries[1:]
    hypothesis={'name':'All recorded selected-cell stage outputs equal their inputs', 'discovery_run':discovery['id'] if discovery else None,'validation_runs':[r['id'] for r in validation], 'status':'INSUFFICIENT_EVIDENCE'}
    if discovery and discovery['records']:
        hypothesis['generated']=discovery['changed']==0
        if hypothesis['generated'] and validation:
            tested=sum(r['records'] for r in validation)
            violations=sum(r['changed'] for r in validation)
            hypothesis.update({'tested_records':tested,'counterexamples':violations,'status':'CONTRADICTED' if violations else 'CONSISTENT_WITH_OBSERVATIONS' if tested else 'INSUFFICIENT_EVIDENCE'})
        elif not hypothesis['generated']:hypothesis['status']='NOT_PROPOSED_DISCOVERY_COUNTEREXAMPLE'
    return {'version':'23.0','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':{'total':len(jobs),'completed':sum(j.get('status')=='completed' for j in jobs),'failed':sum(j.get('status')=='failed' for j in jobs)},'playback_evidence':summaries,'hypotheses':[hypothesis],'warnings':warnings,'limitations':['Stage input/output equality is a narrow descriptive hypothesis, not a conservation law.','Playback data may be correlated or have different initial conditions.','No conclusion about full native state reversibility or global injectivity.','Unmatched job experiment IDs are not treated as matched evidence.']}

def save_report(root):
    report=analyze(root);folder=pathlib.Path(root)/'research_data/v23/reports';folder.mkdir(parents=True,exist_ok=True)
    path=folder/('intelligence_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
    path.write_text(json.dumps(report,indent=2));return {'path':str(path.relative_to(root)),'report':report}
