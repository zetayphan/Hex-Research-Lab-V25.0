"""Browser-independent, bounded, append-only observational recorder."""
import json,os,threading,time,datetime
from collections import deque
from pathlib import Path
from research_metrics import summarize_state
class Recorder:
    def __init__(self,path,snapshot,engine_lock,clock=time.monotonic):
        self.path=Path(path);self.snapshot=snapshot;self.engine_lock=engine_lock
        self.clock=clock;self.guard=threading.RLock();self.enabled=False
        self.sample_seconds=2.0;self.samples=0;self.last_error=None;self.last_sample=None
        self.cache=deque(maxlen=1000);self.stop_event=threading.Event();self.thread=None
    def start(self):
        if self.thread is None:
            self.thread=threading.Thread(target=self._loop,daemon=True,name='v4-recorder');self.thread.start()
    def configure(self,enabled=None,sample_seconds=None):
        with self.guard:
            if enabled is not None:self.enabled=enabled
            if sample_seconds is not None:self.sample_seconds=float(sample_seconds)
        return self.status()
    def status(self):
        with self.guard:return {'enabled':self.enabled,'sample_seconds':self.sample_seconds,'samples_this_process':self.samples,'last_sample':self.last_sample,'last_error':self.last_error,'file':str(self.path.relative_to(self.path.parent.parent)),'scope':'native observational metrics, not proof of reversibility or conservation'}
    def sample_once(self):
        with self.engine_lock:snap=self.snapshot()
        m=summarize_state(snap)
        record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**m}
        with self.guard:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open('a',encoding='utf-8') as f:
                f.write(json.dumps(record,separators=(',',':'))+'\n');f.flush()
            self.cache.append(record);self.samples+=1;self.last_sample=record['utc'];self.last_error=None
        return record
    def history(self,limit=150):
        # Read the tail of the persistent file so history survives server restarts.
        from collections import deque as tail
        if not self.path.exists():return []
        with self.guard:
            with self.path.open(encoding='utf-8') as f:
                lines=tail(f,maxlen=limit)
            out=[]
            for line in lines:
                try:out.append(json.loads(line))
                except ValueError:continue
            return out
    def _loop(self):
        while not self.stop_event.is_set():
            with self.guard:enabled=self.enabled;interval=self.sample_seconds
            if enabled:
                try:self.sample_once()
                except Exception as e:
                    with self.guard:self.last_error=str(e)
            self.stop_event.wait(interval if enabled else 0.25)
