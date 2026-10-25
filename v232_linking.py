"""Attach verified provenance to playback created by a queued native experiment."""
import json, os, pathlib, uuid

def link_job_evidence(root, job_id, experiment):
    root=pathlib.Path(root)
    if not isinstance(job_id,str) or len(job_id)!=32:raise ValueError('Invalid job id')
    if not isinstance(experiment,dict) or not isinstance(experiment.get('id'),str):raise ValueError('Missing experiment id')
    ids=experiment.get('playback_runs',[])
    if not isinstance(ids,list) or not ids:raise ValueError('No native playback recordings')
    folder=root/'research_data/v202/playback'
    for rid in ids:
        if not isinstance(rid,str) or len(rid)!=32 or any(c not in '0123456789abcdef' for c in rid):raise ValueError('Invalid playback id')
        path=folder/(rid+'.json')
        record=json.loads(path.read_text())
        if record.get('id')!=rid:raise ValueError('Playback id mismatch')
        if record.get('job_id') not in (None,job_id):raise ValueError('Conflicting evidence linkage')
        record['job_id']=job_id
        record['experiment_id']=experiment['id']
        record['linkage_schema']='hex-v23.2-verified-job-evidence'
        temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
        temp.write_text(json.dumps(record,indent=2)+'\n')
        os.replace(temp,path)
    return ids
