"""V23.1: evidence-driven, explicitly bounded follow-up experiment plans."""
import json, pathlib, time, uuid, hashlib
from v24_discovery import analyze

PREDICATES = {
    "unchanged_cell": lambda a,b:a==b,
    "zero_output": lambda a,b:b==0,
    "low_byte_preserved": lambda a,b:(a&255)==(b&255),
    "parity_preserved": lambda a,b:(a&1)==(b&1),
}



def propose(root, cells=None, steps=3, repetitions=2, hypothesis='unchanged_cell'):
    cells=[0,1,2] if cells is None else cells
    if not isinstance(cells,list) or not 1<=len(cells)<=16 or any(type(x)!=int or x<0 or x>=32768 for x in cells) or len(set(cells))!=len(cells):
        raise ValueError('Select 1–16 distinct nonnegative cells')
    if type(steps)!=int or not 1<=steps<=20:raise ValueError('Steps must be 1–20')
    if type(repetitions)!=int or not 1<=repetitions<=100:raise ValueError('Runs must be 1–100')
    if hypothesis not in PREDICATES: raise ValueError('Unknown hypothesis: '+str(hypothesis))
    evidence=analyze(root)
    runs=evidence.get('runs',[])
    discovery=next((r for r in runs if r.get('record_count',0)>0),None)
    if discovery is None:
        raise ValueError('No usable discovery playback records. Save at least one native trace in Playback first.')
    # A hypothesis may be contradicted in discovery; that is a valid reason to test it.
    candidates=evidence.get('hypotheses',[])
    preferred=next((h for h in candidates if h['key']==hypothesis),None)
    if preferred is None:raise ValueError('No supported hypothesis definitions')
    source=discovery['id']
    return {'hypothesis':preferred['key'],'discovery_status':preferred['status'],
            'discovery_run':source,'discovery_sha256':discovery['sha256'],
            'cells':cells,'steps':steps,'repetitions':repetitions,
            'warning':'A queued run tests a selected-cell stage predicate, even if discovery contradicted it. This is not proof of global conservation or reversibility.'}


def submit(root, queue, cells=None, steps=3, repetitions=2, hypothesis='unchanged_cell'):
    plan=propose(root,cells,steps,repetitions,hypothesis)
    job=queue.submit(plan['cells'],plan['steps'],plan['repetitions'])
    folder=pathlib.Path(root)/'research_data/v231/cycles';folder.mkdir(parents=True,exist_ok=True)
    cycle={'id':uuid.uuid4().hex,'created':time.time(),'status':'queued','job_id':job['id'],'plan':plan}
    (folder/(cycle['id']+'.json')).write_text(json.dumps(cycle,indent=2))
    return cycle


def list_cycles(root):
    folder=pathlib.Path(root)/'research_data/v231/cycles'
    output=[]
    for path in sorted(folder.glob('*.json')) if folder.exists() else []:
        try:output.append(json.loads(path.read_text()))
        except (OSError,ValueError):continue
    return output


def review(root,queue,cycle_id):
    if not isinstance(cycle_id,str) or len(cycle_id)!=32 or any(c not in '0123456789abcdef' for c in cycle_id):raise ValueError('Invalid cycle ID')
    path=pathlib.Path(root)/'research_data/v231/cycles'/(cycle_id+'.json')
    if not path.is_file():raise ValueError('Cycle not found')
    cycle=json.loads(path.read_text())
    job=next((j for j in queue.list() if j['id']==cycle['job_id']),None)
    if job is None:raise ValueError('Queued job not found')
    result={'cycle_id':cycle_id,'job_id':job['id'],'job_status':job['status'],'completed_runs':job['completed'],
            'expected_runs':job['repetitions'],'assessment':'PENDING','tested_records':0,'counterexamples':0,'linked_playback_ids':[],
            'limitations':['Selected-cell predicates are observational hypotheses, not proof of conservation or reversibility.',
                           'Native state snapshots may omit auxiliary state; repeated runs may share starting conditions.']}
    if job['status']!='completed':
        if job['status'] in ('failed','cancelled','interrupted'):result['assessment']='INCOMPLETE_JOB'
        return result
    discovery=cycle['plan'].get('discovery_run')
    folder=pathlib.Path(root)/'research_data/v202/playback'
    expected={rid for item in job.get('results',[]) for rid in item.get('playback_runs',[])}
    # Backward-compatible queue entries have only experiment_id: explicitly inspect their manifests.
    for item in job.get('results',[]):
        eid=item.get('experiment_id')
        if not eid:continue
        manifest=pathlib.Path(root)/'research_data/v21/reports'/(eid+'.json')
        if manifest.is_file():
            data=json.loads(manifest.read_text())
            if data.get('id')==eid:expected.update(data.get('playback_runs',[]))
    for rid in sorted(expected):
        if rid==discovery:continue
        file=folder/(rid+'.json')
        if not file.is_file():continue
        data=json.loads(file.read_text())
        if data.get('id')!=rid or data.get('job_id')!=job['id'] or data.get('linkage_schema')!='hex-v23.2-verified-job-evidence':continue
        records=data.get('records')
        if not isinstance(records,list):
            records=[r for group in data.get('cells',[]) if isinstance(group,dict) for r in group.get('records',[])]
        from v24_discovery import num
        valid=[(num(r.get('input')),num(r.get('output'))) for r in records if isinstance(r,dict)]
        valid=[(a,b) for a,b in valid if a is not None and b is not None]
        result['tested_records']+=len(valid)
        predicate=PREDICATES.get(cycle['plan'].get('hypothesis','unchanged_cell'),PREDICATES['unchanged_cell'])
        result['counterexamples']+=sum(not predicate(a,b) for a,b in valid)
        result['linked_playback_ids'].append(rid)
    if result['tested_records']:
        result['assessment']='CONTRADICTED' if result['counterexamples'] else 'CONSISTENT_WITH_OBSERVATIONS'
    else:result['assessment']='INSUFFICIENT_LINKED_EVIDENCE'
    return result
