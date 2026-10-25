"""Bounded, browser-independent controlled experiments against actual native steps."""
import datetime,json,threading,time,uuid
from pathlib import Path
from research_metrics import summarize_state

class ExperimentRunner:
    def __init__(self, folder, snapshot, step, engine_lock, pause, resume):
        self.folder=Path(folder);self.snapshot=snapshot;self.step=step
        self.engine_lock=engine_lock;self.pause=pause;self.resume=resume
        self.guard=threading.RLock();self.thread=None;self.status_data={'state':'idle','completed':0,'requested':0,'id':None,'error':None}
    def status(self):
        with self.guard:return dict(self.status_data)
    def start(self, steps=20, delay=0.1):
        if type(steps)!=int or not 1<=steps<=10000:raise ValueError('steps must be 1..10000')
        if type(delay) not in (float,int) or not 0<=delay<=10:raise ValueError('delay must be 0..10')
        with self.guard:
            if self.thread and self.thread.is_alive():raise ValueError('Experiment already running')
            run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
            self.status_data={'state':'running','completed':0,'requested':steps,'id':run_id,'error':None}
            self.thread=threading.Thread(target=self._run,args=(run_id,steps,delay),daemon=True)
            self.thread.start()
        return self.status()
    def _run(self,run_id,steps,delay):
        path=self.folder/(run_id+'.jsonl');previous=None;was_running=None
        try:
            self.folder.mkdir(parents=True,exist_ok=True)
            with self.engine_lock:was_running=self.pause()
            with path.open('w',encoding='utf-8') as f:
                for i in range(steps+1):
                    with self.engine_lock:
                        if i:self.step()
                        metrics=summarize_state(self.snapshot())
                    if previous is None:
                        diff=[0,0,0];struct={'distinct':0,'transitions':0,'gradient':0}
                    else:
                        diff=[a-b for a,b in zip(metrics['rgb_totals'],previous['rgb_totals'])]
                        struct={'distinct':metrics['distinct_hex_values']-previous['distinct_hex_values'],'transitions':metrics['adjacent_value_transitions']-previous['adjacent_value_transitions'],'gradient':metrics['adjacent_rgb_gradient']-previous['adjacent_rgb_gradient']}
                    row={'index':i,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**metrics,'delta_rgb':diff,'delta_structure':struct,'conserved_rgb_this_step':all(d==0 for d in diff) if i else None,'prediction':'RGB unchanged under full native step (hypothesis, not guaranteed)','prediction_error_l1':sum(map(abs,diff)) if i else None,'reversibility':'not tested: full native inverse unavailable','structural_rank':'not tested: discrete proxies are not a Jacobian'}
                    f.write(json.dumps(row,separators=(',',':'))+'\n');f.flush()
                    previous=metrics
                    with self.guard:self.status_data['completed']=i
                    if i<steps and delay:time.sleep(delay)
            with self.guard:self.status_data['state']='completed'
        except Exception as exc:
            with self.guard:self.status_data.update(state='failed',error=str(exc))
        finally:
            if was_running is not None:
                with self.engine_lock:self.resume(was_running)
    def results(self,run_id=None,limit=500):
        if run_id is None:run_id=self.status()['id']
        if not run_id or not isinstance(run_id,str) or not all(c.isalnum() or c=='-' for c in run_id):raise ValueError('Invalid experiment ID')
        path=self.folder/(run_id+'.jsonl')
        if not path.is_file():raise ValueError('Experiment not found')
        from collections import deque
        with path.open(encoding='utf-8') as f:rows=[json.loads(line) for line in deque(f,maxlen=max(1,min(1000,limit)))]
        steps=[r for r in rows if r['index']>0]
        return {'id':run_id,'records':rows,'summary':{'samples_returned':len(rows),'steps_returned':len(steps),'rgb_conserved_steps':sum(r['conserved_rgb_this_step'] for r in steps),'rgb_changed_steps':sum(not r['conserved_rgb_this_step'] for r in steps),'total_prediction_error_l1':sum(r['prediction_error_l1'] for r in steps),'note':'Full-engine conservation is a tested hypothesis, not assumed; no inverse or Jacobian claim.'}}
    def list_runs(self):
        if not self.folder.exists():return []
        return [{'id':p.stem,'bytes':p.stat().st_size} for p in sorted(self.folder.glob('*.jsonl'),reverse=True)[:100]]
