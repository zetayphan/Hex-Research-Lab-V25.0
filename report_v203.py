"""Read-only evidence reports for V20.2 stage playback records."""
import hashlib, json, re
from pathlib import Path

ID=re.compile(r'^[0-9a-f]{32}$')

def load_run(root, run_id):
    if not isinstance(run_id,str) or not ID.fullmatch(run_id):
        raise ValueError('Invalid run identifier')
    path=Path(root)/'research_data'/'v202'/'playback'/(run_id+'.json')
    if not path.is_file():raise ValueError('Playback run not found')
    raw=path.read_bytes()
    if len(raw)>5_000_000:raise ValueError('Playback record exceeds size limit')
    obj=json.loads(raw)
    if not isinstance(obj,dict) or obj.get('schema')!='hex-v20.2-stage-playback':raise ValueError('Unsupported playback schema')
    return obj,hashlib.sha256(raw).hexdigest()

def summarize(run):
    cells=run.get('cells',[])
    if not isinstance(cells,list):raise ValueError('Invalid cells')
    summaries=[]
    for group in cells:
        records=group.get('records',[])
        if not isinstance(records,list):raise ValueError('Invalid records')
        changes=[]; discontinuities=[]
        for j,rec in enumerate(records):
            a=int(rec['input'],16);b=int(rec['output'],16)
            changes.append({'stage':rec['stage'],'input':rec['input'],'output':rec['output'],'delta_mod24':f'{(b-a)&0xffffff:06X}','xor':f'{a^b:06X}','expression':rec.get('expression','')})
            if j and records[j-1]['output']!=rec['input']:
                discontinuities.append(rec['stage'])
        summaries.append({'cell':group['cell'],'stages':len(records),'changed_stages':sum(x['input']!=x['output'] for x in changes),'stage_transitions':changes,'discontinuities':discontinuities})
    return summaries

def build(root, run_a, run_b=None):
    a,sha_a=load_run(root,run_a)
    sa=summarize(a)
    b=sha_b=sb=None
    if run_b:
        b,sha_b=load_run(root,run_b);sb=summarize(b)
    comparisons=[]
    if sb is not None:
        bmap={(g['cell'],r['stage']):r for g in sb for r in g['stage_transitions']}
        for g in sa:
            for r in g['stage_transitions']:
                other=bmap.get((g['cell'],r['stage']))
                comparisons.append({'cell':g['cell'],'stage':r['stage'],'a':r['output'],'b':other['output'] if other else None,'match':other is not None and r['output']==other['output']})
    lines=['# Hex Unified Research Lab V20.3 — Evidence Report','','## Evidence','',f'- Run A: `{run_a}`',f'- SHA-256 A: `{sha_a}`',f'- Tick A: {a.get("tick")}',f'- Captured A: {a.get("created_at", "unknown")}']
    if b:lines += [f'- Run B: `{run_b}`',f'- SHA-256 B: `{sha_b}`',f'- Tick B: {b.get("tick")}',f'- Captured B: {b.get("created_at", "unknown")}']
    lines += ['','## Recorded transformation summary','']
    for g in sa:
        lines += [f'### Cell {g["cell"]}',f'- Stages recorded: {g["stages"]}',f'- Stages with changed value: {g["changed_stages"]}',f'- Adjacent stage discontinuities: {len(g["discontinuities"])}','', '| Stage | Input | Output | Modular delta | XOR | Expression |','|---:|---|---|---|---|---|']
        for r in g['stage_transitions']:
            expr=str(r['expression']).replace('|','\\|').replace('\n',' ')
            lines.append(f'| {r["stage"]} | `{r["input"]}` | `{r["output"]}` | `{r["delta_mod24"]}` | `{r["xor"]}` | {expr} |')
        lines.append('')
    if b:
        matched=sum(x['match'] for x in comparisons)
        lines += ['## Recorded stage comparison','',f'- Matching outputs: {matched}/{len(comparisons)}','', '| Cell | Stage | A output | B output | Match |','|---:|---:|---|---|---|']
        for r in comparisons:lines.append(f'| {r["cell"]} | {r["stage"]} | `{r["a"]}` | `{r["b"] or "missing"}` | {"Yes" if r["match"] else "No"} |')
    lines += ['','## Interpretation and limitations','', '- Results describe saved, selected-cell stage records; they are not complete lattice snapshots.', '- Stage-local input/output deltas and XORs are not global conservation invariants.', '- RGB conservation cannot be established from these selected-cell traces alone; use a native-state verification audit for that claim.', '- No inverse or complete-state recurrence proof follows from matching recorded outputs.', '- Evidence hashes identify the exact saved JSON bytes at report generation time.', '- This report does not advance or modify the native engine.','']
    return {'run_a':run_a,'run_b':run_b,'sha256_a':sha_a,'sha256_b':sha_b,'cells':sa,'comparisons':comparisons,'limitations':lines[-6:-1],'markdown':'\n'.join(lines)}
