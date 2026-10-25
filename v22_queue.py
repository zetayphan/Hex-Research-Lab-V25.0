"""Durable bounded research job queue. Jobs survive process restarts."""
import json, os, pathlib, threading, time, uuid, urllib.request, urllib.error
from v232_linking import link_job_evidence

class ResearchQueue:
    def __init__(self, root, port):
        self.folder=pathlib.Path(root)/'research_data'/'v22'/'jobs'; self.folder.mkdir(parents=True,exist_ok=True)
        self.port=port; self.lock=threading.RLock(); self.stop=threading.Event()
        for path in self.folder.glob('*.json'):
            try:
                job=json.loads(path.read_text())
                if job.get('status')=='running':
                    job['status']='interrupted'; job['error']='Server stopped during execution. Requeue manually to avoid duplicate experiments.'
                    self._write(job)
            except (OSError,ValueError):pass
        self.thread=threading.Thread(target=self._worker,daemon=True);self.thread.start()
    def _write(self,job):
        p=self.folder/(job['id']+'.json'); tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(job,indent=2));os.replace(tmp,p)
    def list(self):
        with self.lock:
            out=[]
            for p in self.folder.glob('*.json'):
                try:out.append(json.loads(p.read_text()))
                except (OSError,ValueError):continue
            return sorted(out,key=lambda j:j['created'],reverse=True)[:200]
    def submit(self,cells,steps,repetitions):
        if not isinstance(cells,list) or not 1<=len(cells)<=16 or any(type(c)!=int or not 0<=c<32768 for c in cells) or len(set(cells))!=len(cells):raise ValueError('Provide 1–16 unique valid cells')
        if type(steps)!=int or not 1<=steps<=20:raise ValueError('Steps must be 1–20')
        if type(repetitions)!=int or not 1<=repetitions<=100:raise ValueError('Repetitions must be 1–100')
        job={'id':uuid.uuid4().hex,'created':time.time(),'updated':time.time(),'status':'queued','cells':cells,'steps':steps,'repetitions':repetitions,'completed':0,'results':[],'error':None}
        with self.lock:self._write(job)
        return job
    def change(self,ident,action):
        with self.lock:
            p=self.folder/(ident+'.json')
            if not p.is_file():raise ValueError('Job not found')
            j=json.loads(p.read_text())
            if action=='cancel' and j['status'] in ('queued','running','interrupted'):
                j['status']='cancelling' if j['status']=='running' else 'cancelled'
            elif action=='retry' and j['status'] in ('failed','interrupted','cancelled'):
                j['status']='queued';j['error']=None
            else:raise ValueError('Invalid action for job status')
            j['updated']=time.time();self._write(j);return j
    def _worker(self):
        while not self.stop.wait(.7):
            with self.lock:
                jobs=sorted((j for j in self.list() if j['status']=='queued'),key=lambda j:j['created'])
                if not jobs:continue
                j=jobs[0];j['status']='running';j['updated']=time.time();self._write(j)
            while True:
                with self.lock:
                    j=json.loads((self.folder/(j['id']+'.json')).read_text())
                    if j['status']=='cancelling':j['status']='cancelled';j['updated']=time.time();self._write(j);break
                    if j['completed']>=j['repetitions']:j['status']='completed';j['updated']=time.time();self._write(j);break
                try:
                    pause_body=json.dumps({'command':'pause'}).encode()
                    pause_req=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/terminal/engine',data=pause_body,headers={'Content-Type':'application/json'},method='POST')
                    with urllib.request.urlopen(pause_req,timeout=15) as pause_response:pause_response.read()
                    body=json.dumps({'cells':j['cells'],'steps':j['steps']}).encode()
                    req=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/v21/execute',data=body,headers={'Content-Type':'application/json'},method='POST')
                    with urllib.request.urlopen(req,timeout=180) as r:result=json.load(r)
                    link_job_evidence(self.folder.parent.parent.parent, j['id'], result)
                    with self.lock:
                        j=json.loads((self.folder/(j['id']+'.json')).read_text());j['results'].append({'experiment_id':result['id'],'playback_runs':result.get('playback_runs',[]),'reports':result.get('reports',[])});j['completed']+=1;j['updated']=time.time();self._write(j)
                except urllib.error.HTTPError as e:
                    try:
                        payload=json.loads(e.read().decode('utf-8','replace'))
                        detail=payload.get('error',str(e))
                    except (ValueError,OSError):detail=str(e)
                    with self.lock:
                        j=json.loads((self.folder/(j['id']+'.json')).read_text());j['status']='failed';j['error']=f'Execution HTTP {e.code}: {detail}';j['updated']=time.time();self._write(j)
                    break
                except Exception as e:
                    with self.lock:
                        j=json.loads((self.folder/(j['id']+'.json')).read_text());j['status']='failed';j['error']=str(e);j['updated']=time.time();self._write(j)
                    break
