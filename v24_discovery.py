"""V24 evidence-grounded candidate discovery; never equates traces with complete-state proof."""
import pathlib,json,hashlib,datetime,collections

def num(v):
    if isinstance(v,int): return v
    if isinstance(v,str):
        try:return int(v,16)
        except ValueError:return None
    return None

def analyze(root):
    folder=pathlib.Path(root)/'research_data/v202/playback'
    runs=[];warnings=[]
    for p in sorted(folder.glob('*.json')) if folder.exists() else []:
        try:
            raw=p.read_bytes();data=json.loads(raw)
            groups=data.get('cells',[])
            records=data.get('records',data.get('trace',[]))
            if not isinstance(records,list):records=[]
            if isinstance(groups,list):
                records+= [r for g in groups if isinstance(g,dict) for r in g.get('records',[]) if isinstance(r,dict)]
            cleaned=[]
            for r in records:
                if not isinstance(r,dict):continue
                a,b=num(r.get('input')),num(r.get('output'))
                if a is None or b is None:continue
                cleaned.append({'stage':r.get('stage'),'cell':r.get('index',r.get('cell')),'input':a,'output':b})
            runs.append({'id':p.stem,'sha256':hashlib.sha256(raw).hexdigest(),'records':cleaned})
        except (OSError,ValueError,TypeError) as e:warnings.append(f'{p.name}: {type(e).__name__}')
    discovery=runs[0] if runs else None
    validation=runs[1:]
    specs=[('unchanged_cell','Stage output equals stage input',lambda r:r['input']==r['output']),('zero_output','Stage output is zero',lambda r:r['output']==0),('low_byte_preserved','Low 8 bits preserved',lambda r:(r['input']&255)==(r['output']&255)),('parity_preserved','Least-significant bit preserved',lambda r:(r['input']&1)==(r['output']&1))]
    hypotheses=[]
    for key,label,test in specs:
        d=discovery['records'] if discovery else []
        proposed=bool(d) and all(test(r) for r in d)
        held=[r for run in validation for r in run['records']]
        fails=sum(not test(r) for r in held) if proposed else 0
        status=('INSUFFICIENT_DISCOVERY' if not d else 'NOT_PROPOSED' if not proposed else 'INSUFFICIENT_VALIDATION' if not held else 'CONTRADICTED' if fails else 'CONSISTENT_WITH_OBSERVATIONS')
        hypotheses.append({'key':key,'description':label,'discovery_run':discovery['id'] if discovery else None,'discovery_records':len(d),'validation_runs':[r['id'] for r in validation],'validation_records':len(held) if proposed else 0,'counterexamples':fails,'status':status})
    # Repeat signatures are stage-local observations, not complete-state recurrence.
    recurrence=[]
    for run in runs:
        by_stage=collections.defaultdict(list)
        for r in run['records']:by_stage[str(r['stage'])].append((str(r['cell']),r['input'],r['output']))
        recurrence.append({'run':run['id'],'repeated_record_signatures':sum(len(v)-len(set(v)) for v in by_stage.values()),'scope':'Selected cell/stage signatures only'})
    return {'version':'24.0','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':[{'id':r['id'],'sha256':r['sha256'],'record_count':len(r['records'])} for r in runs],'hypotheses':hypotheses,'recurrence':recurrence,'warnings':warnings,'limitations':['Only saved selected-cell stage traces are evaluated; global RGB totals and complete-state recurrence cannot be inferred.','Collision/injectivity claims require distinct complete inputs and identical complete outputs; this report makes no such claim.','Held-out recordings may not be statistically independent.','Hypotheses are candidate patterns, not mathematical proofs.']}

def save(root):
    result=analyze(root)
    folder=pathlib.Path(root)/'research_data/v24/reports';folder.mkdir(parents=True,exist_ok=True)
    name='discovery_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'
    (folder/name).write_text(json.dumps(result,indent=2)+'\n')
    return {'path':str((folder/name).relative_to(root)),'report':result}
