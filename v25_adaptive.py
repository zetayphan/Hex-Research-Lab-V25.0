"""V25: descriptive, bounded adaptive experiment strategy ranking."""
import json, pathlib, collections, hashlib
from v231_cycle import PREDICATES, submit as submit_cycle
from v24_discovery import num


def strategies(root):
    folder=pathlib.Path(root)/'research_data/v202/playback'
    runs=[]
    for p in sorted(folder.glob('*.json')) if folder.exists() else []:
        try:
            raw=p.read_bytes(); obj=json.loads(raw)
            records=obj.get('records',[])
            if not isinstance(records,list):records=[]
            for g in obj.get('cells',[]):
                if isinstance(g,dict):records.extend(g.get('records',[]))
            valid=[]
            for r in records:
                if not isinstance(r,dict):continue
                a,b=num(r.get('input')),num(r.get('output'))
                if a is not None and b is not None:valid.append((a,b))
            if valid:runs.append({'id':p.stem,'sha256':hashlib.sha256(raw).hexdigest(),'pairs':valid})
        except (OSError,ValueError,TypeError,KeyError):continue
    if not runs:return {'status':'NO_EVIDENCE','message':'Save a native playback recording first.','strategies':[],'runs':0}
    # Each strategy targets a different testable predicate. Rank by disagreement
    # among recordings, then by scarcity of independent recordings.
    results=[]
    for key,pred in PREDICATES.items():
        per_run=[sum(pred(a,b) for a,b in r['pairs'])/len(r['pairs']) for r in runs]
        overall=sum(per_run)/len(per_run)
        spread=max(per_run)-min(per_run)
        # A balanced result is more discriminating than a near-universal pass/fail.
        balance=1-abs(2*overall-1)
        score=round(0.6*spread+0.4*balance,4)
        results.append({'hypothesis':key,'score':score,'observed_pass_fraction':round(overall,4),
                        'between_run_spread':round(spread,4),'run_count':len(runs),
                        'suggested_cells':[0,1,2],'steps':3,'repetitions':2,
                        'reason':'Prioritizes disagreement between recorded runs and mixed outcomes; descriptive heuristic only.'})
    results.sort(key=lambda r:(-r['score'],r['hypothesis']))
    return {'status':'STRATEGIES_AVAILABLE','runs':len(runs),'strategies':results,
            'recommended':results[0], 'evidence':[{'id':r['id'],'sha256':r['sha256']} for r in runs],
            'limitations':['Scores are not probabilities, significance tests, or proof.',
                           'Repeated trajectories may not be independent.',
                           'Selection cannot control native initial state or guarantee a discriminating next run.']}


def queue_strategy(root,queue,request):
    key=request.get('hypothesis')
    if key not in PREDICATES:raise ValueError('Unknown hypothesis')
    # Reuse the existing validated, evidence-linked V23.1 submission pipeline.
    result=submit_cycle(root,queue,request.get('cells',[0,1,2]),
                        request.get('steps',3),request.get('repetitions',2),key)
    result['v25_strategy']=key
    return result
