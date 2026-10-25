#!/usr/bin/env python3
"""Hex Studio Pro local host. Conceptual stages are documented interpretations."""
import argparse, ctypes, json, pathlib, re, socket, subprocess, threading, time, hashlib, shutil, datetime, sys, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.analysis import compare as compare_experiments
from v19_lab import fingerprint as v19_fingerprint, audit as v19_audit
from verification_v201 import evaluate_transition, coverage_report, native_state_fingerprint
ROOT=pathlib.Path(__file__).resolve().parents[1]
LIB=ROOT/'build'/'libhexstudio.so'; LIB.parent.mkdir(exist_ok=True)
if not LIB.exists() or LIB.stat().st_mtime < (ROOT/'src'/'engine.c').stat().st_mtime:
    subprocess.run(['cc','-O2','-std=c11','-shared','-fPIC',str(ROOT/'src'/'engine.c'),'-o',str(LIB)],check=True)
TERMINAL_LIB=ROOT/'build'/'libhexterminal.so'
if not TERMINAL_LIB.exists() or TERMINAL_LIB.stat().st_mtime < (ROOT/'src'/'terminal_native.c').stat().st_mtime:
    subprocess.run(['cc','-O2','-std=c11','-shared','-fPIC',str(ROOT/'src'/'terminal_native.c'),'-o',str(TERMINAL_LIB)],check=True)
terminal_native=ctypes.CDLL(str(TERMINAL_LIB))
terminal_native.hex_terminal_eval.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_int,ctypes.POINTER(ctypes.c_uint32)]
terminal_native.hex_terminal_eval.restype=ctypes.c_int
TERMINAL_OPS={'add':0,'sub':1,'mul':2,'xor':3,'and':4,'or':5,'rol':6,'ror':7,'div':8,'mod':9}

class State(ctypes.Structure):
    _fields_=[('cells',ctypes.c_uint32*32768),('stages',ctypes.c_uint32*17),('stage_changes',ctypes.c_uint32*17),('tick',ctypes.c_uint64),('checksum',ctypes.c_uint32),('flags',ctypes.c_uint32),('dimension',ctypes.c_uint32),('count',ctypes.c_uint32)]
lib=ctypes.CDLL(str(LIB))
lib.hex_init.argtypes=[ctypes.POINTER(State),ctypes.POINTER(ctypes.c_uint32),ctypes.c_size_t,ctypes.c_uint32]
class NativeTrace(ctypes.Structure):
    _fields_=[(name,ctypes.c_uint32) for name in ('stage','index','input','left','right','up','down','output')]
lib.hex_trace_config.argtypes=[ctypes.c_uint32,ctypes.c_uint32]
lib.hex_trace_count.restype=ctypes.c_uint32
lib.hex_trace_get.argtypes=[ctypes.c_uint32,ctypes.POINTER(NativeTrace)]
lib.hex_trace_get.restype=ctypes.c_int
lib.hex_trace_expression.argtypes=[ctypes.c_uint32,ctypes.c_void_p,ctypes.c_size_t]
lib.hex_trace_expression.restype=ctypes.c_int
lib.hex_multi_config.argtypes=[ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint32]
lib.hex_multi_config.restype=ctypes.c_int
lib.hex_multi_count.restype=ctypes.c_uint32
lib.hex_multi_cells.restype=ctypes.c_uint32
lib.hex_multi_get.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(NativeTrace)]
lib.hex_multi_get.restype=ctypes.c_int
lib.hex_multi_expression.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_size_t]
lib.hex_multi_expression.restype=ctypes.c_int
multi_selected=[]
def multi_payload():
    groups=[]
    for slot,cell in enumerate(multi_selected):
        records=[]
        for stage in range(int(lib.hex_multi_count())):
            rec=NativeTrace();buf=ctypes.create_string_buffer(320)
            if lib.hex_multi_get(slot,stage,ctypes.byref(rec)):
                lib.hex_multi_expression(slot,stage,buf,len(buf))
                records.append({'stage':stage+1,'name':NAMES[stage],'index':int(rec.index),'expression':buf.value.decode(),**{k:f'{getattr(rec,k):06X}' for k in ('input','left','right','up','down','output')}})
        groups.append({'cell':cell,'records':records})
    return {'schema':'hex-v20-simultaneous-native-trace','tick':int(state.tick),'cells':groups,'stage_count':int(lib.hex_multi_count()),'scope':'Captured within one native hex_step; optional post-processing is excluded.'}
def native_expression(stage):
    buf=ctypes.create_string_buffer(320)
    return buf.value.decode() if lib.hex_trace_expression(stage,buf,len(buf)) else ""
def captured_trace():
    records=[]
    for j in range(int(lib.hex_trace_count())):
        rec=NativeTrace()
        if lib.hex_trace_get(j,ctypes.byref(rec)):
            records.append({"stage":j+1,"name":NAMES[j],"index":int(rec.index),"expression":native_expression(j),**{key:f"{getattr(rec,key):06X}" for key in ("input","left","right","up","down","output")}})
    return {"schema":"hex-native-trace-v18.2","tick":int(state.tick),"cell":trace_target,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"records":records,"scope":"Selected cell, 17 native stages; post-processing is not traced."}
def save_trace():
    payload=captured_trace()
    if not payload["records"]:raise ValueError("No trace captured. Pause, trace on 0, step 1 first.")
    folder=ROOT/"research_data"/"native_traces_v182"
    folder.mkdir(parents=True,exist_ok=True)
    payload["id"]=uuid.uuid4().hex
    path=folder/(payload["id"]+".json")
    path.write_text(json.dumps(payload,indent=2)+"\n")
    return payload
trace_target=0
trace_active=False
lib.hex_step.argtypes=[ctypes.POINTER(State)]
lib.hex_enable_extension.argtypes=[ctypes.POINTER(State),ctypes.c_int]
lib.hex_bond_step.argtypes=[ctypes.POINTER(State),ctypes.c_uint32,ctypes.c_uint32]
lib.hex_bond_step.restype=ctypes.c_uint32
lib.hex_separate_conservative.argtypes=[ctypes.POINTER(State),ctypes.c_uint32]
lib.hex_separate_conservative.restype=ctypes.c_uint32
lib.hex_separate_transform.argtypes=[ctypes.POINTER(State),ctypes.c_uint32]
lib.hex_separate_transform.restype=ctypes.c_uint32
separation_changes={'conservative':0,'transformative':0}
unified_changes=0
unified_bond_rate=48
unified_flow_rate=35
separation_rate=55
lib.hex_unified_dynamics.argtypes=[ctypes.POINTER(State),ctypes.c_uint32,ctypes.c_uint32]
lib.hex_unified_dynamics.restype=ctypes.c_uint32
separation_amplitude=35
lib.hex_set_cell.argtypes=[ctypes.POINTER(State),ctypes.c_uint32,ctypes.c_uint32]
lib.hex_set_cell.restype=ctypes.c_int
NAMES=['Late Model','File Layout','Location Spec','Underlying Principle Extension','Derive Structure','Derive Operation','Derive Layout','Integrate Structure','Integrate Operation','Integrate Layout','Run Locations Through Late Model','Run Principle Through System','Run File Through System','Output Hexadecimal','Input Hexadecimal','Repeat Input Output','Save File']
state=State(); lock=threading.RLock(); running=True; interval=.4; history=[]; last_error=None; file_info=None; steps_total=0; errors_total=0; started_at=time.monotonic()
bond_enabled=False; bond_strength=48; bond_threshold=25; bond_changes=0
pair_bonds={}
# Persistent weighted graph, separate from the native 6-neighbor bonding step.
# Edges retain their strength across ticks and are applied to native RGB cells.
persistent_bonds={}
network_enabled=False
network_changes=0
MAX_NETWORK_BONDS=98304  # Maximum nearest-neighbor edges for a 32^3 open lattice

def bond_capacity():
    d=int(state.dimension)
    return min(MAX_NETWORK_BONDS,3*d*d*(d-1))
# Bounded autonomous six-neighbor discovery; avoids O(N^2) searches.
auto_enabled=False
auto_similarity=.76
auto_scan_budget=1200
auto_added=0
auto_removed=0
auto_cursor=0

def auto_discover():
    global auto_added,auto_removed,auto_cursor
    auto_added=auto_removed=0
    if not auto_enabled or not network_enabled:return
    n=int(state.count);d=int(state.dimension)
    if n<2:return
    # Visit successive lattice cells in a deterministic round-robin order.
    # Consider only +X,+Y,+Z edges; each undirected edge is visited once.
    budget=min(n,max(1,auto_scan_budget))
    for offset in range(budget):
        i=(auto_cursor+offset)%n
        x=i%d;y=(i//d)%d;z=i//(d*d)
        candidates=[]
        if x+1<d:candidates.append(i+1)
        if y+1<d:candidates.append(i+d)
        if z+1<d:candidates.append(i+d*d)
        for j in candidates:
            edge=(i,j)
            sim=bond_similarity(int(state.cells[i]),int(state.cells[j]))
            if edge in persistent_bonds:
                # Network evolution handles normal weakening; allow early break on divergence.
                if sim<max(0,auto_similarity-.42):
                    del persistent_bonds[edge];auto_removed+=1
            elif sim>=auto_similarity and len(persistent_bonds)<bond_capacity():
                add_persistent_bond(i,j,max(10,min(90,round(sim*75))))
                auto_added+=1
    auto_cursor=(auto_cursor+budget)%n


def bond_similarity(a,b):
    return 1-sum(abs(((a>>shift)&255)-((b>>shift)&255)) for shift in (0,8,16))/765

def network_step():
    global network_changes
    if not network_enabled or not persistent_bonds:
        network_changes=0;return
    original={i:int(state.cells[i]) for edge in persistent_bonds for i in edge}
    totals={};weights={};expired=[]
    for edge,record in list(persistent_bonds.items()):
        a,b=edge;similarity=bond_similarity(original[a],original[b])
        # Existing bonds survive, strengthen with similarity and weaken with divergence.
        record['strength']=max(0,min(100,record['strength']+(2 if similarity>=.65 else -3)))
        record['age']+=1
        if record['strength']==0:expired.append(edge);continue
        w=record['strength']/100
        for i,j in ((a,b),(b,a)):
            totals[i]=totals.get(i,0)+w*original[j];weights[i]=weights.get(i,0)+w
    for edge in expired:del persistent_bonds[edge]
    changed=0
    for i,weight in weights.items():
        own=original[i];neighbors=[]
        for shift in (0,8,16):
            # Calculate channel-specific weighted mean, never mix packed integers.
            weighted=sum((rec['strength']/100)*((original[b if a==i else a]>>shift)&255) for (a,b),rec in persistent_bonds.items() if i in (a,b))
            mean=weighted/weight
            val=max(0,min(255,round(.88*((own>>shift)&255)+.12*mean)))
            neighbors.append(val)
        out=(neighbors[2]<<16)|(neighbors[1]<<8)|neighbors[0]
        if out!=own:lib.hex_set_cell(ctypes.byref(state),i,out);changed+=1
    network_changes=changed

def add_persistent_bond(a,b,strength=50):
    if not (0<=a<state.count and 0<=b<state.count and a!=b):raise ValueError('Invalid bond endpoints')
    key=tuple(sorted((a,b)))
    if key not in persistent_bonds and len(persistent_bonds)>=bond_capacity():raise ValueError('Network bond limit reached')
    persistent_bonds[key]={'strength':max(1,min(100,int(strength))),'age':0}

SAVE=ROOT/'saved'/'state.json'
def initialize(values,dimension=None):
    global history
    pair_bonds.clear();persistent_bonds.clear()
    a=(ctypes.c_uint32*len(values))(*values)
    lib.hex_init(ctypes.byref(state),a,len(values),dimension or (int(state.dimension) if state.dimension else 8));history=[]
def step():
    global steps_total,bond_changes,unified_changes
    lib.hex_step(ctypes.byref(state))
    # V7 C: coordinate A and B after the existing 17-stage pipeline.
    # A is exactly conservative; B is intentionally nonconservative.
    separation_changes['conservative']=int(lib.hex_separate_conservative(ctypes.byref(state),separation_rate))
    separation_changes['transformative']=int(lib.hex_separate_transform(ctypes.byref(state),separation_amplitude))
    unified_changes=int(lib.hex_unified_dynamics(ctypes.byref(state),unified_bond_rate,unified_flow_rate))
    bond_changes=0
    steps_total+=1
    history.append({'tick':int(state.tick),'value':int(state.checksum),'mean':sum(state.cells[:state.count])//state.count})
    if len(history)>500:del history[:-500]
def snapshot():
    return {'version':'10.3','tick':int(state.tick),'state_version':int(state.tick),'checksum':f'{state.checksum:06X}', 'hex':[f'{v:06X}' for v in state.cells[:state.count]], 'values':list(state.cells[:state.count]),'dimension':int(state.dimension),'cell_count':int(state.count),'cycle':{'feedback':True,'processing':'17 stages → conservative separation → transformative separation → local bonding + nodal transport → feedback'},'unified_dynamics':{'bonding':'local symmetric RGB flux','transport':'conservative directed nodal flux','bond_rate':unified_bond_rate,'flow_rate':unified_flow_rate,'changed_cells':unified_changes,'fluid_model':'discrete transport (not Navier-Stokes)','webgl_driver':'native RGB spatial gradients'},'separation':{'mode':'A+B coordinated by C','conservative_changed':separation_changes['conservative'],'transformative_changed':separation_changes['transformative'],'rate':separation_rate,'amplitude':separation_amplitude,'channel_conservation':'exact during A'},'persistent_network':{'autonomous':{'enabled':auto_enabled,'similarity':auto_similarity,'scan_budget':auto_scan_budget,'added':auto_added,'removed':auto_removed},'enabled':network_enabled,'bond_count':len(persistent_bonds),'possible_neighbor_edges':3*int(state.dimension)**2*(int(state.dimension)-1),'bond_capacity':bond_capacity(),'scanned_cells_per_tick':min(int(state.count),max(1,auto_scan_budget)),'changed_cells':network_changes,'bonds':[{'a':a,'b':b,**rec} for (a,b),rec in list(persistent_bonds.items())[:min(2048,len(persistent_bonds))]]},'bonding':{'enabled':bond_enabled,'strength':bond_strength,'threshold':bond_threshold,'changed_cells':bond_changes,'pair_count':len(pair_bonds),'pairs':[list(k) for k in list(pair_bonds)[:100] ]}, 'stages':[{'name':n,'checksum':f'{state.stages[i]:06X}','status':'executed' if state.tick else 'ready','changed_cells':int(state.stage_changes[i]),'kind':'transformation' if i in (0,2,3,4,7,10,11,13,14,15) else 'structural/management'} for i,n in enumerate(NAMES)],'history':list(history[-100:]),'file':file_info,'running':running,'interval_ms':round(interval*1000),'extension':bool(state.flags&1),'error':last_error,'diagnostics':{'steps_total':steps_total,'errors_total':errors_total,'uptime_seconds':round(time.monotonic()-started_at,1),'engine':f'native C / {state.count} x 24-bit cells','visualization':f'native {state.dimension}x{state.dimension}x{state.dimension} lattice','stage_count':17,'stage_changes_verified_range':int(state.count),'native_architecture':__import__('platform').machine(),'independent_3d_simulation':True}}
def controlled_frame():
    """Serialize engine and configured dynamics for controlled V10 trials."""
    return {'format':'hex-studio-v4-state-1','cells':list(state.cells[:state.count]),'stages':list(state.stages),'stage_changes':list(state.stage_changes),'tick':int(state.tick),'checksum':int(state.checksum),'flags':int(state.flags),'interval':interval,'running':False,'history':list(history),'separation':{'rate':separation_rate,'amplitude':separation_amplitude},'unified_dynamics':{'bond_rate':unified_bond_rate,'flow_rate':unified_flow_rate},'persistent_network':{'enabled':network_enabled,'bonds':[{'a':a,'b':b,**rec} for (a,b),rec in persistent_bonds.items()],'autonomous':{'enabled':auto_enabled,'similarity':auto_similarity,'scan_budget':auto_scan_budget}},'bonding':{'enabled':bond_enabled,'strength':bond_strength,'threshold':bond_threshold}}

def restore(obj):
    global running,interval,history,bond_enabled,bond_strength,bond_threshold,bond_changes,network_enabled,network_changes,auto_enabled,auto_similarity,auto_scan_budget,auto_cursor
    if obj.get('format') not in ('hex-studio-v4-state-1','hex-studio-v3-state-1','hex-studio-v2-state-1'):raise ValueError('Invalid save format')
    vals=obj['cells']; stages=obj['stages']; tick=obj['tick']
    if len(vals)==24 and obj.get('format')=='hex-studio-v2-state-1':
        vals=[(vals[i%24] ^ (i*0x9E3779B9)) & 0xFFFFFF for i in range(512)]
    if len(vals) not in (512,1728,4096,13824,32768) or len(stages)!=17 or any(type(x)!=int or x<0 or x>0xffffff for x in vals+stages) or type(tick)!=int or tick<0:raise ValueError('Invalid saved state')
    state.dimension=round(len(vals)**(1/3));state.count=len(vals)
    for i,v in enumerate(vals):state.cells[i]=v
    changes=obj.get('stage_changes',[0]*17)
    if not isinstance(changes,list) or len(changes)!=17 or any(type(v)!=int or v<0 or v>len(vals) for v in changes):raise ValueError('Invalid stage change counts')
    for i,v in enumerate(changes):state.stage_changes[i]=v
    for i,v in enumerate(stages):state.stages[i]=v
    state.tick=tick;state.checksum=int(obj['checksum']);state.flags=int(obj['flags'])&1
    if not 0<=int(state.checksum)<=0xffffff:raise ValueError('Invalid checksum')
    interval=max(.05,min(5,float(obj.get('interval',.25))))
    loaded_history=obj.get('history',[])
    if not isinstance(loaded_history,list):raise ValueError('Invalid history')
    history=loaded_history[-500:];running=bool(obj.get('running',False))
    persistent_bonds.clear();net={} # V7 no persistent bond network
    if isinstance(net,dict):
        network_enabled=False
        edges=net.get('bonds',[])
        if not isinstance(edges,list) or len(edges)>bond_capacity():raise ValueError('Invalid persistent network')
        for rec in edges:
            a=int(rec['a']);b=int(rec['b']);add_persistent_bond(a,b,rec['strength'])
            persistent_bonds[tuple(sorted((a,b)))]['age']=max(0,int(rec.get('age',0)))
    autonomous=net.get('autonomous',{}) if isinstance(net,dict) else {}
    if isinstance(autonomous,dict):
        auto_enabled=False
        auto_similarity=max(0,min(1,float(autonomous.get('similarity',.76))))
        auto_scan_budget=max(1,min(32768,int(autonomous.get('scan_budget',1200))))
    auto_cursor=0
    network_changes=0
    globals()['separation_rate']=max(0,min(100,int(obj.get('separation',{}).get('rate',55))))
    globals()['separation_amplitude']=max(0,min(100,int(obj.get('separation',{}).get('amplitude',35))))
    global unified_bond_rate,unified_flow_rate
    dyn=obj.get('unified_dynamics',{})
    unified_bond_rate=max(0,min(100,int(dyn.get('bond_rate',48))))
    unified_flow_rate=max(0,min(100,int(dyn.get('flow_rate',35))))
    bond=obj.get('bonding',{});bond_enabled=False;bond_strength=max(0,min(100,int(bond.get('strength',35))));bond_threshold=max(0,min(100,int(bond.get('threshold',45))));bond_changes=0
initialize([0x071EB8,0xDB10BC,0xEB1078,0x0B1DBC])
def worker():
    global last_error,errors_total,running
    while True:
        with lock:
            if running:
                try:step();last_error=None
                except Exception as e:last_error=str(e);errors_total+=1;running=False
            delay=interval
        time.sleep(delay)
threading.Thread(target=worker,daemon=True).start()
EXPERIMENTS=ROOT/'experiments'/'records'
def experiment_folder(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name):raise ValueError('Invalid experiment name')
    return EXPERIMENTS/name
def experiment_data(name):
    folder=experiment_folder(name)
    return json.loads((folder/'state.json').read_text())
def experiment_manifest(name):
    return json.loads((experiment_folder(name)/'manifest.json').read_text())
def write_atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(path)
# V4 recorder samples native states independently of browser connections.
from autonomous_v4 import Recorder
recorder=Recorder(ROOT/'research_data'/'observations.jsonl', snapshot, lock)
recorder.start()
# V5 bounded native experimental verification (pauses ordinary stepping during a run).
from experimental_v5 import ExperimentRunner
def v5_pause():
    global running
    old=running;running=False;return old
def v5_resume(previous):
    global running
    running=previous
v5_runner=ExperimentRunner(ROOT/'research_data'/'experiments_v5',snapshot,step,lock,v5_pause,v5_resume)
from discovery_v6 import compare as compare_discovery
class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):print('[HTTP]',fmt%args,flush=True)
    def respond(self,code,data):
        raw=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def serve_lab_page(self,name):
        raw=(ROOT/'web'/name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path in ('/discovery-v24','/discovery-v24/'):
            return self.serve_lab_page('discovery_v24.html')
        if self.path=='/api/v24/analysis':
            from v24_discovery import analyze
            return self.respond(200,analyze(ROOT))
        if self.path in ('/adaptive-v25','/adaptive-v25/'):
            return self.serve_lab_page('adaptive_v25.html')
        if self.path=='/api/v25/strategies':
            from v25_adaptive import strategies
            return self.respond(200,strategies(ROOT))
        if self.path in ('/cycle-v231','/cycle-v231/'):
            return self.serve_lab_page('cycle_v231.html')
        if self.path=='/api/v231/cycles':
            from v231_cycle import list_cycles
            return self.respond(200,{'cycles':list_cycles(ROOT)})
        if self.path in ('/intelligence-v23','/intelligence-v23/'):
            return self.serve_lab_page('intelligence_v23.html')
        if self.path=='/api/v23/analysis':
            from v23_intelligence import analyze
            return self.respond(200,analyze(ROOT))
        if self.path in ('/queue-v22','/queue-v22/'):
            return self.serve_lab_page('queue_v22.html')
        if self.path=='/api/v244/recommend':
            from v244_selection import recommend
            return self.respond(200,recommend(ROOT))
        if self.path=='/api/v22/jobs':
            return self.respond(200,{'jobs':research_queue.list()})
        if self.path in ('/automation-v21','/automation-v21/'):
            return self.serve_lab_page('automation_v21.html')
        if self.path in ('/reports-v203','/reports-v203/'):
            return self.serve_lab_page('reports_v203.html')
        if self.path in ('/playback-v202','/playback-v202/'):
            return self.serve_lab_page('playback_v202.html')
        if self.path=='/api/v202/runs':
            folder=ROOT/'research_data'/'v202'/'playback'
            runs=[]
            for f in sorted(folder.glob('*.json'),reverse=True)[:100] if folder.exists() else []:
                try:
                    data=json.loads(f.read_text())
                    runs.append({'id':f.stem,'tick':data['tick'],'cells':data['selected_cells'],'created_at':data['created_at'],'record_count':data['record_count']})
                except (ValueError,KeyError,OSError):pass
            return self.respond(200,{'runs':runs})
        if self.path.startswith('/api/v202/run/'):
            rid=self.path.rsplit('/',1)[-1]
            if not re.fullmatch(r'[a-f0-9]{32}',rid):return self.respond(400,{'error':'Invalid run ID'})
            path=ROOT/'research_data'/'v202'/'playback'/(rid+'.json')
            if not path.is_file():return self.respond(404,{'error':'Run not found'})
            return self.respond(200,json.loads(path.read_text()))
        if self.path in ('/verification-v201','/verification-v201/'):
            return self.serve_lab_page('verification_v201.html')
        if self.path in ('/collision-v193','/collision-v193/'):
            return self.serve_lab_page('collision_v193.html')
        if self.path in ('/collision-v192','/collision-v192/'):
            return self.serve_lab_page('collision_v192.html')
        if self.path in ('/collision-v191','/collision-v191/'):
            return self.serve_lab_page('collision_v191.html')
        if self.path in ('/lab-v19','/lab-v19/'):
            return self.serve_lab_page('lab_v19.html')
        if self.path in ('/home','/home/'):
            return self.serve_lab_page('home.html')
        if self.path in ('/terminal','/terminal/'):
            return self.serve_lab_page('terminal_lab.html')
        if self.path in ('/visualization','/visualization/'):
            return self.serve_lab_page('visual_lab.html')
        if self.path in ('/stage-lab','/stage-lab/'):
            return self.serve_lab_page('stage_lab_v181.html')
        if self.path=='/api/v20/trace':
            with lock:return self.respond(200,{**multi_payload(),'running':running})
        if self.path in ('/trace-v20','/trace-v20/'):
            return self.serve_lab_page('trace_v20.html')
        if self.path=='/api/v181/stage-trace':
            with lock:
                payload=captured_trace()
                self.respond(200,{**payload,'running':running,'cell_count':int(state.count),'selected_cell':trace_target,'trace_enabled':trace_active,'note':'Expressions captured in native C for one selected cell per stage. Post-processing is not traced.'})
            return
        if self.path=='/api/v182/history':
            folder=ROOT/'research_data'/'native_traces_v182'
            runs=sorted(folder.glob('*.json'),key=lambda x:x.stat().st_mtime,reverse=True)[:100] if folder.exists() else []
            return self.respond(200,{'runs':[{'id':p.stem,'bytes':p.stat().st_size} for p in runs]})
        if self.path=='/api/lab/trace':
            with lock:
                self.respond(200,{'tick':int(state.tick),'running':running,'count':int(state.count),'hex':[f'{int(v):06X}' for v in state.cells[:min(128,state.count)]],'stages':[{'name':name,'checksum':f'{int(state.stages[i]):06X}','changed':int(state.stage_changes[i])} for i,name in enumerate(NAMES)]})
            return
        if self.path in ('/native-v14','/native-v14/'):
            raw=(ROOT/'web'/'native_v14.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/v14/stages':
            from native_v14 import report
            self.respond(200,report());return
        if self.path in ('/native-v13','/native-v13/'):
            raw=(ROOT/'web'/'native_v13.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/v13/stages':
            from native_stage_v13 import report
            self.respond(200,report());return
        if self.path in ('/reversibility-v12','/reversibility-v12/'):
            raw=(ROOT/'web'/'reversibility_v12.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path in ('/audit-v11','/audit-v11/'):
            raw=(ROOT/'web'/'audit_v11.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path in ('/controlled-v10','/controlled-v10/'):
            raw=(ROOT/'web'/'controlled_v10.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path in ('/design-v9','/design-v9/'):
            raw=(ROOT/'web'/'design_v9.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path.startswith('/api/v9/'):
            from urllib.parse import urlsplit,parse_qs
            from design_v9 import plan,compare
            try:
                q=parse_qs(urlsplit(self.path).query)
                if urlsplit(self.path).path=='/api/v9/plan':
                    self.respond(200,plan(int(q.get('steps',['100'])[0]),int(q.get('replicates',['3'])[0]),float(q.get('delay',['0.1'])[0]),q.get('initial_state',['unspecified'])[0]))
                elif urlsplit(self.path).path=='/api/v9/compare':
                    self.respond(200,compare(ROOT/'research_data'/'experiments_v5',q.get('id',[])))
                else:self.respond(404,{'error':'Unknown V9 endpoint'})
            except (ValueError,OSError,json.JSONDecodeError,KeyError,TypeError) as e:self.respond(400,{'error':str(e)})
            return
        if self.path in ('/research-v8','/research-v8/'):
            raw=(ROOT/'web'/'research_v8.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path.startswith('/api/v8/report'):
            from urllib.parse import urlsplit,parse_qs
            from research_v8 import report,markdown
            try:
                q=parse_qs(urlsplit(self.path).query);ids=q.get('id',[])
                result=report(ROOT/'research_data'/'experiments_v5',ids)
                if q.get('format',['json'])[0]=='md':
                    raw=markdown(result).encode()
                    self.send_response(200);self.send_header('Content-Type','text/markdown; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="hex_v8_report.md"');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                else:self.respond(200,result)
            except (ValueError,OSError,json.JSONDecodeError,KeyError) as e:self.respond(400,{'error':str(e)})
            return
        if self.path in ('/hypotheses-v7','/hypotheses-v7/'):
            raw=(ROOT/'web'/'hypotheses_v7.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path.startswith('/api/v7/hypotheses'):
            from urllib.parse import urlsplit,parse_qs
            from hypothesis_v7 import evaluate
            try:
                ids=parse_qs(urlsplit(self.path).query).get('id',[])
                self.respond(200,evaluate(ROOT/'research_data'/'experiments_v5',ids))
            except (ValueError,OSError,json.JSONDecodeError) as e:self.respond(400,{'error':str(e)})
            return
        if self.path in ('/discovery-v6','/discovery-v6/'):
            raw=(ROOT/'web'/'discovery_v6.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path.startswith('/api/v6/discovery'):
            from urllib.parse import urlsplit,parse_qs
            q=parse_qs(urlsplit(self.path).query)
            try:
                ids=q.get('id',[])
                if not ids:ids=[r['id'] for r in v5_runner.list_runs()[:1]]
                self.respond(200,compare_discovery(ROOT/'research_data'/'experiments_v5',ids))
            except (ValueError,OSError,json.JSONDecodeError) as e:self.respond(400,{'error':str(e)})
            return
        if self.path=='/api/v5/status':self.respond(200,v5_runner.status());return
        if self.path=='/api/v5/runs':self.respond(200,{'runs':v5_runner.list_runs()});return
        if self.path.startswith('/api/v5/results'):
            from urllib.parse import urlsplit,parse_qs
            q=parse_qs(urlsplit(self.path).query)
            try:self.respond(200,v5_runner.results(q.get('id',[None])[0],int(q.get('limit',['500'])[0])))
            except (ValueError,TypeError) as e:self.respond(400,{'error':str(e)})
            return
        if self.path in ('/experiments-v5','/experiments-v5/'):
            raw=(ROOT/'web'/'experiments_v5.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path in ('/api/state','/api/health'):
            with lock:self.respond(200,snapshot() if self.path=='/api/state' else {'ok':True,'version':'10.3','tick':int(state.tick)})
            return
        if self.path=='/api/research/observation':
            with lock:
                snap=snapshot()
            from research_metrics import summarize_state
            self.respond(200,summarize_state(snap));return
        if self.path=='/api/autonomous/status':
            self.respond(200,recorder.status());return
        if self.path.startswith('/api/autonomous/history'):
            from urllib.parse import urlsplit,parse_qs
            q=parse_qs(urlsplit(self.path).query)
            try:limit=max(1,min(1000,int(q.get('limit',['150'])[0])))
            except ValueError:limit=150
            self.respond(200,{'records':recorder.history(limit)});return
        if self.path in ('/autonomous','/autonomous/'):
            raw=(ROOT/'web'/'autonomous.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/verification':
            from verification_engine import report
            with lock: snap=snapshot()
            self.respond(200,report(snap));return
        if self.path in ('/verification','/verification/'):
            raw=(ROOT/'web'/'verification.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw);return
        if self.path in ('/research','/research/'):
            raw=(ROOT/'web'/'research.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/experiments':
            EXPERIMENTS.mkdir(parents=True,exist_ok=True)
            records=[]
            for folder in sorted(EXPERIMENTS.iterdir()):
                if folder.is_dir() and (folder/'state.json').is_file():
                    try:
                        manifest=json.loads((folder/'manifest.json').read_text())
                        data=json.loads((folder/'state.json').read_text())
                        records.append({'name':folder.name,'created':manifest.get('created_utc',''),'tick':data.get('tick'),'cells':len(data.get('cells',[])),'actions':len(manifest.get('actions',[]))})
                    except (ValueError,OSError):continue
            self.respond(200,{'experiments':records});return
        if self.path in ('/','/index.html'):
            raw=(ROOT/'web'/'home.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        self.respond(404,{'error':'Unknown route','dashboard':'/'})
    def do_POST(self):
        global trace_target,trace_active,multi_selected
        global separation_rate,separation_amplitude,running,interval,bond_enabled,bond_strength,bond_threshold,bond_changes,network_enabled,network_changes,auto_enabled,auto_similarity,auto_scan_budget
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<0 or n>2200000:raise ValueError('Invalid request size')
            if self.headers.get('Origin') and not re.fullmatch(r'https?://(localhost|127\.0\.0\.1)(:\d+)?',self.headers['Origin']):raise ValueError('Cross-origin requests forbidden')
            obj=json.loads(self.rfile.read(n) or b'{}')
            if not isinstance(obj,dict):raise ValueError('Expected JSON object')
            if self.path=='/api/v25/queue':
                from v25_adaptive import queue_strategy
                return self.respond(200,queue_strategy(ROOT,research_queue,obj))
            if self.path=='/api/v231/submit':
                from v231_cycle import submit
                return self.respond(200,submit(ROOT,research_queue,obj.get('cells',[0,1,2]),obj.get('steps',3),obj.get('repetitions',2),obj.get('hypothesis','unchanged_cell')))
            if self.path=='/api/v231/review':
                from v231_cycle import review
                return self.respond(200,review(ROOT,research_queue,obj.get('cycle_id','')))
            if self.path=='/api/v24/save':
                from v24_discovery import save
                return self.respond(200,save(ROOT))
            if self.path=='/api/v23/save':
                from v23_intelligence import save_report
                return self.respond(200,save_report(ROOT))
            if self.path=='/api/v22/submit':
                return self.respond(200,research_queue.submit(obj.get('cells',[0,1,2]),obj.get('steps',3),obj.get('repetitions',1)))
            if self.path=='/api/v22/action':
                ident=obj.get('id','')
                if not isinstance(ident,str) or not re.fullmatch('[0-9a-f]{32}',ident):raise ValueError('Invalid job ID')
                return self.respond(200,research_queue.change(ident,obj.get('action')))
            if self.path=='/api/v21/execute':
                from report_v203 import build
                from verification_v201 import evaluate_transition, native_state_fingerprint
                cells=obj.get('cells',[0,1,2]); count=obj.get('steps',1)
                if type(count)!=int or not 1<=count<=20:raise ValueError('Steps must be 1..20')
                if not isinstance(cells,list) or not 1<=len(cells)<=16 or len(set(map(str,cells)))!=len(cells) or any(type(x)!=int for x in cells):raise ValueError('Select 1..16 unique integer cells')
                with lock:
                    if running:raise ValueError('Pause the native engine before automation')
                    if any(x<0 or x>=int(state.count) for x in cells):raise ValueError('Cell out of range')
                    initial=controlled_frame()
                    raw=ctypes.string_at(ctypes.byref(state),ctypes.sizeof(state))
                    initial_sha=native_state_fingerprint(raw)
                    old_selected=list(multi_selected)
                    old_trace_active=trace_active
                    old_trace_target=trace_target
                    records=[]; observations=[]; run_ids=[]
                    try:
                        arr=(ctypes.c_uint32*len(cells))(*cells)
                        if not lib.hex_multi_config(arr,len(cells)):raise ValueError('Native multi trace configuration failed')
                        multi_selected=list(cells)
                        for nstep in range(count):
                            before=controlled_frame()
                            step()
                            after=controlled_frame()
                            observations.append(evaluate_transition(before,after))
                            captured=multi_payload()
                            groups=[g for g in captured['cells'] if len(g['records'])==17]
                            if len(groups)!=len(cells):raise ValueError('Incomplete native trace; aborted')
                            run_id=uuid.uuid4().hex
                            playback={'schema':'hex-v20.2-stage-playback','id':run_id,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tick':captured['tick'],'selected_cells':cells,'record_count':sum(len(g['records']) for g in groups),'cells':groups,'scope':'Native 17-stage selected-cell traces from one step; not full-lattice stage snapshots.'}
                            records.append(playback);run_ids.append(run_id)
                    finally:
                        ctypes.memmove(ctypes.byref(state),raw,len(raw))
                        restore(initial)
                        running=False
                        if old_selected:
                            arr=(ctypes.c_uint32*len(old_selected))(*old_selected)
                            lib.hex_multi_config(arr,len(old_selected))
                        else:
                            lib.hex_multi_config((ctypes.c_uint32*1)(),0)
                        multi_selected=old_selected
                        lib.hex_trace_config(int(old_trace_target),int(old_trace_active))
                    restored_sha=native_state_fingerprint(ctypes.string_at(ctypes.byref(state),ctypes.sizeof(state)))
                    if restored_sha!=initial_sha:raise ValueError('Native byte restoration mismatch; no experiment saved')
                    folder=ROOT/'research_data'/'v202'/'playback';folder.mkdir(parents=True,exist_ok=True)
                    for rec in records:(folder/(rec['id']+'.json')).write_text(json.dumps(rec,indent=2)+'\n')
                    reports=[]
                    outdir=ROOT/'research_data'/'v21'/'reports';outdir.mkdir(parents=True,exist_ok=True)
                    for rid in run_ids:
                        rep=build(ROOT,rid)
                        (outdir/(rid+'.md')).write_text(rep['markdown'],encoding='utf-8')
                        reports.append({'run_id':rid,'report':str((outdir/(rid+'.md')).relative_to(ROOT))})
                    experiment={'schema':'hex-v21-automated-research','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cells':cells,'steps':count,'playback_runs':run_ids,'reports':reports,'observations':observations,'native_state_initial_sha256':initial_sha,'native_state_restored_sha256':restored_sha,'native_bytes_restored':True,'reversibility':'UNRESOLVED_NO_NATIVE_INVERSE','limitations':['Selected-cell traces are not complete-state stage snapshots','Native byte restoration does not establish full auxiliary-state restoration','Observed conservation is not a universal theorem','Native C step includes post-stage dynamics not represented in the stage traces']}
                    eid=uuid.uuid4().hex;experiment['id']=eid
                    (outdir/(eid+'.json')).write_text(json.dumps(experiment,indent=2)+'\n')
                    return self.respond(200,experiment)
            if self.path=='/api/v203/report':
                from report_v203 import build
                report=build(ROOT,obj.get('run_a'),obj.get('run_b') or None)
                folder=ROOT/'research_data'/'v203'/'reports';folder.mkdir(parents=True,exist_ok=True)
                report_id=uuid.uuid4().hex
                (folder/(report_id+'.md')).write_text(report['markdown'],encoding='utf-8')
                return self.respond(200,{'id':report_id,'markdown':report['markdown'],'sha256_a':report['sha256_a'],'sha256_b':report['sha256_b'],'comparison_count':len(report['comparisons'])})
            if self.path=='/api/v202/capture':
                with lock:
                    if running:raise ValueError('Pause engine before capturing a trace')
                    cells=obj.get('cells',[0,1,2])
                    if not isinstance(cells,list) or not 1<=len(cells)<=16 or any(type(x)!=int or x<0 or x>=int(state.count) for x in cells) or len(cells)!=len(set(cells)):
                        raise ValueError('Provide 1–16 distinct valid cell indices')
                    # Do not advance engine: save most recent simultaneous trace only.
                    captured=multi_payload()
                    actual=[g for g in captured['cells'] if g['cell'] in cells and len(g['records'])==17]
                    if len(actual)!=len(cells):raise ValueError('Arm these cells in V20 trace, step once, then capture before another step')
                    payload={'schema':'hex-v20.2-stage-playback','id':uuid.uuid4().hex,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tick':captured['tick'],'selected_cells':cells,'record_count':sum(len(g['records']) for g in actual),'cells':actual,'scope':'Recorded per-cell native stage operands and outputs from the most recent step. This is not a complete lattice snapshot at each stage; playback does not alter engine state.'}
                    folder=ROOT/'research_data'/'v202'/'playback';folder.mkdir(parents=True,exist_ok=True)
                    (folder/(payload['id']+'.json')).write_text(json.dumps(payload,indent=2)+'\n')
                    return self.respond(200,payload)
            if self.path=='/api/v193/analyze':
                from collision_v193 import analyze
                result=analyze(stage=obj.get('stage',0),flags=obj.get('flags',1),
                    timeout_ms=obj.get('timeout_ms',5000),fallback_trials=obj.get('fallback_trials',1000),seed=obj.get('seed',19))
                folder=ROOT/'research_data'/'v193'/'symbolic_audits'
                folder.mkdir(parents=True,exist_ok=True)
                result['id']=uuid.uuid4().hex
                (folder/(result['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                return self.respond(200,result)
            if self.path=='/api/v192/analyze':
                from collision_v192 import analyze
                result=analyze(stage=obj.get('stage',7),flags=obj.get('flags',1),
                    alphabet=obj.get('alphabet',[0,1]),random_trials=obj.get('random_trials',2000),seed=obj.get('seed',19))
                folder=ROOT/'research_data'/'v192'/'algebraic_audits'
                folder.mkdir(parents=True,exist_ok=True)
                result['id']=uuid.uuid4().hex
                (folder/(result['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                return self.respond(200,result)
            if self.path=='/api/v191/collision':
                from collision_v191 import investigate
                # Operates on a standalone, source-aligned model; never mutates live engine state.
                result=investigate(stage=obj.get('stage',0),dimension=2,
                    alphabet=obj.get('alphabet',[0,1]),random_trials=obj.get('random_trials',2000),
                    seed=obj.get('seed',19),flags=obj.get('flags',1))
                folder=ROOT/'research_data'/'v191'/'collision_audits'
                folder.mkdir(parents=True,exist_ok=True)
                result['id']=uuid.uuid4().hex
                (folder/(result['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                return self.respond(200,result)
            if self.path=='/api/v201/verify':
                with lock:
                    if running:raise ValueError('Pause the engine before a verification trial')
                    count=obj.get('steps',1)
                    if type(count)!=int or not 1<=count<=20:raise ValueError('steps must be 1..20')
                    baseline=controlled_frame()
                    raw_before=ctypes.string_at(ctypes.byref(state),ctypes.sizeof(state))
                    coverage=coverage_report(baseline,ctypes.sizeof(state))
                    initial_fp=native_state_fingerprint(raw_before)
                    trials=[]
                    try:
                        for _ in range(count):
                            before=controlled_frame()
                            step()
                            after=controlled_frame()
                            trials.append(evaluate_transition(before,after))
                        final_fp=native_state_fingerprint(ctypes.string_at(ctypes.byref(state),ctypes.sizeof(state)))
                        trace=multi_payload()
                    finally:
                        ctypes.memmove(ctypes.byref(state),raw_before,len(raw_before))
                        restore(baseline)
                        running=False
                    restored_fp=native_state_fingerprint(ctypes.string_at(ctypes.byref(state),ctypes.sizeof(state)))
                    result={'schema':'hex-v20.1-verification','steps':count,'coverage':coverage,'initial_native_fingerprint':initial_fp,'final_native_fingerprint':final_fp,'restored_native_fingerprint':restored_fp,'native_bytes_restored':initial_fp==restored_fp,'observations':trials,'last_trace':trace,'reversibility':'UNRESOLVED_NO_NATIVE_INVERSE','scope':'Observed RGB conservation and structure for sampled steps; native bytes restored, not proven full auxiliary-state restoration. No global injectivity claim.'}
                    folder=ROOT/'research_data'/'v201'/'verification';folder.mkdir(parents=True,exist_ok=True)
                    result['id']=uuid.uuid4().hex
                    (folder/(result['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                    return self.respond(200,result)
            if self.path=='/api/v20/trace':
                with lock:
                    if running:raise ValueError('Pause the engine before configuring a trace')
                    cells=obj.get('cells',[])
                    if not isinstance(cells,list) or len(cells)>16 or any(type(x)!=int or x<0 or x>=int(state.count) for x in cells) or len(cells)!=len(set(cells)):
                        raise ValueError('Select up to 16 distinct valid cell indices')
                    values=(ctypes.c_uint32*len(cells))(*cells)
                    if not lib.hex_multi_config(values,len(cells)):raise ValueError('Native trace configuration failed')
                    multi_selected=list(cells)
                    return self.respond(200,{'configured':cells,'message':'Step the engine once, then GET /api/v20/trace'})
            if self.path=='/api/v19/experiment':
                # globals declared at start of do_POST
                with lock:
                    if running:raise ValueError('Pause the engine before a V19 experiment')
                    cells=obj.get('cells',[0,1,2])
                    if not isinstance(cells,list) or not 1<=len(cells)<=16 or any(type(i)!=int or not 0<=i<int(state.count) for i in cells) or len(set(cells))!=len(cells):
                        raise ValueError('Select 1–16 distinct valid cell indices')
                    initial=controlled_frame()
                    old_target,old_active=trace_target,trace_active
                    outcomes=[]
                    try:
                        for cell in cells:
                            restore(initial);running=False
                            trace_target=cell;trace_active=True;lib.hex_trace_config(1,cell)
                            step()
                            final=controlled_frame()
                            outcomes.append({'cell':cell,'audit':v19_audit(initial,final),'trace':captured_trace()['records']})
                    finally:
                        restore(initial);running=False
                        trace_target=old_target;trace_active=old_active
                        lib.hex_trace_config(int(old_active),int(old_target))
                    fingerprints=[o['audit']['after_fingerprint'] for o in outcomes]
                    result={'schema':'hex-v19-controlled-traces','initial_fingerprint':v19_fingerprint(initial),'cells':cells,'outcomes':outcomes,'replicated_recorded_state':len(set(fingerprints))==1,'scope':'One cell traced per replay from the same serialized starting frame. Does not prove full hidden-state restoration or simultaneous tracing.'}
                    folder=ROOT/'research_data'/'v19';folder.mkdir(parents=True,exist_ok=True)
                    result['id']=uuid.uuid4().hex
                    (folder/(result['id']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                    self.respond(200,result)
                return
            if self.path=='/api/v19/snapshot':
                with lock:
                    if running:raise ValueError('Pause before snapshot')
                    frame=controlled_frame()
                    folder=ROOT/'research_data'/'v19'/'snapshots';folder.mkdir(parents=True,exist_ok=True)
                    ident=uuid.uuid4().hex
                    (folder/(ident+'.json')).write_text(json.dumps(frame)+'\n')
                    self.respond(200,{'id':ident,'fingerprint':v19_fingerprint(frame),'coverage':'Serialized V10 frame only; native and Python hidden state may remain uncaptured.'})
                return
            if self.path=='/api/v19/restore':
                with lock:
                    if running:raise ValueError('Pause before restore')
                    ident=str(obj.get('id',''))
                    if not re.fullmatch('[0-9a-f]{32}',ident):raise ValueError('Invalid snapshot ID')
                    path=ROOT/'research_data'/'v19'/'snapshots'/(ident+'.json')
                    if not path.is_file():raise ValueError('Snapshot not found')
                    restore(json.loads(path.read_text()));running=False
                    self.respond(200,{'restored':True,'fingerprint':v19_fingerprint(controlled_frame())})
                return
            if self.path=='/api/v182/save-trace':
                with lock:self.respond(200,{'ok':True,'saved':save_trace()})
                return
            if self.path=='/api/v181/trace-control':
                with lock:
                    cell=int(obj.get('cell',0))
                    if cell<0 or cell>=state.count:raise ValueError('Cell index out of range')
                    trace_target=cell
                    trace_active=True
                    lib.hex_trace_config(1,cell)
                    self.respond(200,{'ok':True,'selected_cell':cell,'message':'Tracing armed; advance the engine to capture the selected cell.'})
                return
            if self.path=='/api/terminal/engine':
                command=str(obj.get('command','')).strip()
                parts=command.split()
                if not parts:raise ValueError('Enter a command; type help')
                verb=parts[0].lower()
                with lock:
                    if verb=='help':
                        lines=['Native 17-stage C engine commands:','help','status','run','pause','step [count 1..100]','read <index>','set <index> <hex24>','stages','cells [start] [count]','trace on [cell]','trace off','trace show','trace detail','trace save','Note: step executes the complete native 17-stage pipeline plus configured post-processing.']
                    elif verb=='status':
                        lines=[f'TICK={state.tick} RUNNING={running} CELLS={state.count} CHECKSUM={state.checksum:06X}']
                    elif verb in ('run','pause'):
                        running=(verb=='run');lines=[f'ENGINE {"RUNNING" if running else "PAUSED"}']
                    elif verb=='step':
                        if running:raise ValueError('Pause before manual stepping')
                        count=int(parts[1]) if len(parts)>1 else 1
                        if count<1 or count>100:raise ValueError('Step count must be 1..100')
                        for _ in range(count):step()
                        lines=[f'EXECUTED {count} FULL ENGINE STEP(S); TICK={state.tick}; CHECKSUM={state.checksum:06X}']
                    elif verb=='read':
                        if len(parts)!=2:raise ValueError('Usage: read <index>')
                        i=int(parts[1]);
                        if i<0 or i>=state.count:raise ValueError('Cell index out of range')
                        lines=[f'CELL[{i}] = 0x{state.cells[i]:06X} ({state.cells[i]})']
                    elif verb=='set':
                        if len(parts)!=3:raise ValueError('Usage: set <index> <hex24>')
                        if running:raise ValueError('Pause engine before modifying cells')
                        i=int(parts[1]); raw=parts[2]
                        if not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{1,6}',raw):raise ValueError('Expected 1-6 hex digits')
                        v=int(raw,16)
                        if i<0 or i>=state.count:raise ValueError('Cell index out of range')
                        before=int(state.cells[i]);lib.hex_set_cell(ctypes.byref(state),i,v)
                        lines=[f'CELL[{i}] 0x{before:06X} -> 0x{v:06X}; CHECKSUM={state.checksum:06X}']
                    elif verb=='trace':
                        sub=parts[1].lower() if len(parts)>1 else 'show'
                        if sub=='on':
                            trace_target=int(parts[2]) if len(parts)>2 else 0
                            if trace_target<0 or trace_target>=state.count:raise ValueError('Cell index out of range')
                            trace_active=True
                            lib.hex_trace_config(1,trace_target)
                            lines=[f'NATIVE TRACE ON for cell {trace_target}. Run step 1, then trace show.']
                        elif sub=='save':
                            saved=save_trace();lines=[f"Saved {len(saved['records'])} native stage records as {saved['id']}.json"]
                        elif sub=='detail':
                            lines=[f"{j+1:02d} {native_expression(j)}" for j in range(int(lib.hex_trace_count()))] or ['No trace captured.']
                        elif sub=='off':
                            trace_active=False;lib.hex_trace_config(0,0);lines=['NATIVE TRACE OFF']
                        elif sub=='show':
                            rows=[]
                            for j in range(int(lib.hex_trace_count())):
                                rec=NativeTrace()
                                if lib.hex_trace_get(j,ctypes.byref(rec)):
                                    rows.append(f'{j+1:02d} {NAMES[j]} | in={rec.input:06X} L={rec.left:06X} R={rec.right:06X} U={rec.up:06X} D={rec.down:06X} => out={rec.output:06X}')
                            lines=rows or ['No trace yet. Enter trace on 0, pause, step 1, trace show.']
                        else:raise ValueError('Usage: trace on [cell] | trace off | trace show | trace detail | trace save')
                    elif verb=='stages':
                        lines=[f'{i+1:02d} {NAMES[i]}: CHECKSUM={state.stages[i]:06X} CHANGED={state.stage_changes[i]}' for i in range(17)]
                    elif verb=='cells':
                        start=int(parts[1]) if len(parts)>1 else 0
                        count=int(parts[2]) if len(parts)>2 else 16
                        if start<0 or start>=state.count or count<1 or count>128:raise ValueError('Invalid cell range (count 1..128)')
                        lines=[f'[{i:05d}] 0x{state.cells[i]:06X}' for i in range(start,min(state.count,start+count))]
                    else:raise ValueError('Unknown engine command; type help')
                self.respond(200,{'lines':lines,'tick':int(state.tick),'running':running,'engine':'src/engine.c native C shared simulation'});return
            if self.path=='/api/terminal/native':
                op=str(obj.get('op','')).lower()
                if op not in TERMINAL_OPS:raise ValueError('Unsupported native operation')
                def word(key):
                    raw=obj.get(key)
                    if not isinstance(raw,str) or not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{1,6}',raw):raise ValueError('Expected 1-6 hexadecimal digits for '+key)
                    return int(raw,16)
                a,b=word('a'),word('b')
                result=ctypes.c_uint32()
                rc=terminal_native.hex_terminal_eval(a,b,TERMINAL_OPS[op],ctypes.byref(result))
                if rc:raise ValueError('Native arithmetic failed (division by zero or invalid operation)')
                self.respond(200,{'engine':'native C / 24-bit','op':op,'a':f'{a:06X}','b':f'{b:06X}','result':f'{result.value:06X}','decimal':result.value,'tick':int(state.tick)})
                return
            if self.path=='/api/v12/investigate':
                from reversibility_v12 import investigate
                with lock:
                    if running or network_enabled or auto_enabled or bond_enabled or persistent_bonds:raise ValueError('Pause engine and disable bonding/network modes')
                    if v5_runner.status()['state']=='running' or recorder.status().get('enabled',False):raise ValueError('Stop experiments and recorder first')
                    self.respond(200,investigate(controlled_frame,restore,step,obj.get('steps',12)))
                return
            if self.path=='/api/v11/audit':
                from audit_v11 import audit
                with lock:
                    if running:raise ValueError('Pause engine before V11 audit')
                    if network_enabled or auto_enabled or bond_enabled or persistent_bonds:raise ValueError('Disable network and bonding modes')
                    if v5_runner.status()['state']=='running':raise ValueError('Stop V5 experiments first')
                    if recorder.status().get('enabled',False):raise ValueError('Stop autonomous recorder first')
                    self.respond(200,audit(controlled_frame,restore,step,obj.get('steps',20)))
                return
            if self.path=='/api/v10/trial':
                from controlled_v10 import trial
                with lock:
                    if running:raise ValueError('Pause the engine before a controlled trial')
                    if network_enabled or auto_enabled or bond_enabled or persistent_bonds:raise ValueError('Disable bonding and persistent networks for repeatability trials')
                    if v5_runner.status()['state']=='running':raise ValueError('Wait for V5 experiment to finish')
                    if recorder.status().get('enabled',False):raise ValueError('Stop autonomous recording before trials')
                    result=trial(controlled_frame,restore,step,obj.get('replicates',3),obj.get('steps',10))
                    self.respond(200,result)
                return
            if self.path=='/api/v5/start':
                self.respond(200,v5_runner.start(obj.get('steps',20),obj.get('delay',0.1)));return
            if self.path=='/api/autonomous/config':
                enabled=obj.get('enabled')
                seconds=obj.get('sample_seconds')
                if enabled is not None and type(enabled) is not bool:raise ValueError('enabled must be boolean')
                if seconds is not None and (type(seconds) not in (int,float) or not 0.2<=seconds<=3600):raise ValueError('sample_seconds must be between 0.2 and 3600')
                self.respond(200,recorder.configure(enabled,seconds));return
            with lock:
                if self.path=='/api/experiments/save':
                    name=obj.get('name');folder=experiment_folder(name)
                    if folder.exists():raise ValueError('Experiment name already exists')
                    if not SAVE.exists():raise ValueError('Save the current engine state before creating an experiment')
                    data=json.loads(SAVE.read_text())
                    write_atomic(folder/'state.json',data)
                    write_atomic(folder/'manifest.json',{'name':name,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actions':[]})
                    self.respond(200,{'saved':name});return
                elif self.path=='/api/experiments/timeline/capture':
                    name=obj.get('name');folder=experiment_folder(name)
                    if not (folder/'manifest.json').exists():raise ValueError('Experiment not found')
                    frames=folder/'timeline';frames.mkdir(exist_ok=True)
                    existing=sorted(frames.glob('frame_*.json'))
                    if len(existing)>=250:raise ValueError('Timeline limit: 250 frames per experiment')
                    frame={'format':'hex-studio-v4-state-1','cells':list(state.cells[:state.count]),'stages':list(state.stages),'stage_changes':list(state.stage_changes),'tick':int(state.tick),'checksum':int(state.checksum),'flags':int(state.flags),'interval':interval,'running':False,'history':list(history[-500:])}
                    index=len(existing);write_atomic(frames/f'frame_{index:04d}.json',frame)
                    self.respond(200,{'frame':index,'tick':frame['tick'],'checksum':frame['checksum']});return
                elif self.path=='/api/experiments/timeline/list':
                    folder=experiment_folder(obj.get('name'))/'timeline';result=[]
                    for f in sorted(folder.glob('frame_*.json')) if folder.exists() else []:
                        data=json.loads(f.read_text());result.append({'frame':int(f.stem.split('_')[1]),'tick':data['tick'],'checksum':f"{data['checksum']:06X}",'mean':round(sum(data['cells'])/max(1,len(data['cells'])),1)})
                    self.respond(200,{'frames':result});return
                elif self.path=='/api/experiments/timeline/frame':
                    frame=int(obj.get('frame',-1))
                    if not 0<=frame<250:raise ValueError('Invalid frame')
                    path=experiment_folder(obj.get('name'))/'timeline'/f'frame_{frame:04d}.json'
                    data=json.loads(path.read_text())
                    self.respond(200,{'frame':frame,'tick':data['tick'],'checksum':f"{data['checksum']:06X}",'values':data['cells'],'dimension':round(len(data['cells'])**(1/3))});return
                elif self.path=='/api/experiments/timeline/restore':
                    if running:raise ValueError('Pause engine before restoring timeline frames')
                    frame=int(obj.get('frame',-1))
                    if frame<0 or frame>=250:raise ValueError('Invalid frame')
                    path=experiment_folder(obj.get('name'))/'timeline'/f'frame_{frame:04d}.json'
                    data=json.loads(path.read_text());restore(data);running=False
                    self.respond(200,{'restored_frame':frame,'tick':int(state.tick)});return
                elif self.path=='/api/experiments/restore':
                    if running:raise ValueError('Pause engine before restoring an experiment')
                    data=experiment_data(obj.get('name'))
                    if SAVE.exists():shutil.copy2(SAVE,SAVE.with_name('state.before_experiment_restore.json'))
                    write_atomic(SAVE,data);restore(data)
                    self.respond(200,snapshot());return
                elif self.path=='/api/experiments/compare':
                    a=experiment_data(obj.get('first'));b=experiment_data(obj.get('second'))
                    self.respond(200,compare_experiments(a,b,experiment_manifest(obj.get('first')),experiment_manifest(obj.get('second'))));return
                elif self.path=='/api/experiments/details':
                    name=obj.get('name');self.respond(200,{'name':name,'manifest':experiment_manifest(name),'state':{'tick':experiment_data(name).get('tick'),'cells':len(experiment_data(name).get('cells',[]))}});return
                elif self.path=='/api/experiments/record':
                    name=obj.get('name');action=obj.get('action');manifest=experiment_manifest(name)
                    if not isinstance(action,dict) or action.get('operation') not in ('xor','add','and','or','rotate_left'):raise ValueError('Invalid transform record')
                    manifest.setdefault('actions',[]).append({k:action[k] for k in ('operation','operand','start','count')})
                    write_atomic(experiment_folder(name)/'manifest.json',manifest)
                    self.respond(200,{'recorded':len(manifest['actions'])});return
                elif self.path=='/api/file':
                    global file_info
                    raw=bytes.fromhex(obj.get('bytes',''))
                    if not 1<=len(raw)<=1048576:raise ValueError('Upload 1 to 1048576 bytes')
                    vals=[int.from_bytes(raw[i:i+3].ljust(3,b'\0'),'big') for i in range(0,min(len(raw),1536),3)]
                    initialize(vals)
                    file_info={'name':str(obj.get('name','uploaded.bin'))[:128],'size':len(raw)}
                    running=True
                elif self.path=='/api/control':
                    if 'running' in obj:running=bool(obj['running'])
                    if 'interval_ms' in obj:interval=max(.05,min(5,float(obj['interval_ms'])/1000))
                    if 'extension' in obj:lib.hex_enable_extension(ctypes.byref(state),int(bool(obj['extension'])))
                elif self.path=='/api/separation':
                    if 'rate' in obj:separation_rate=max(0,min(100,int(obj['rate'])))
                    if 'amplitude' in obj:separation_amplitude=max(0,min(100,int(obj['amplitude'])))
                elif self.path=='/api/bonding':
                    if 'enabled' in obj:bond_enabled=bool(obj['enabled'])
                    if 'strength' in obj:bond_strength=max(0,min(100,int(obj['strength'])))
                    if 'threshold' in obj:bond_threshold=max(0,min(100,int(obj['threshold'])))
                    if obj.get('apply_now'):
                        bond_changes=int(lib.hex_bond_step(ctypes.byref(state),bond_strength,bond_threshold))
                        history.append({'tick':int(state.tick),'value':int(state.checksum),'mean':sum(state.cells[:state.count])//state.count})
                        if len(history)>500:del history[:-500]
                elif self.path=='/api/network':
                    action=obj.get('action','add')
                    if action=='enable':network_enabled=True
                    elif action=='auto':
                        if 'enabled' in obj:auto_enabled=bool(obj['enabled'])
                        if 'similarity' in obj:auto_similarity=max(0,min(1,float(obj['similarity'])))
                        if 'scan_budget' in obj:auto_scan_budget=max(1,min(32768,int(obj['scan_budget'])))
                    elif action=='clear':persistent_bonds.clear();network_changes=0
                    elif action in ('add','remove'):
                        a=int(obj.get('a',-1));b=int(obj.get('b',-1))
                        if not (0<=a<state.count and 0<=b<state.count and a!=b):raise ValueError('Invalid cell indices')
                        if action=='add':add_persistent_bond(a,b,obj.get('strength',50))
                        else:persistent_bonds.pop(tuple(sorted((a,b))),None)
                    else:raise ValueError('Unknown network action')
                elif self.path=='/api/pair_bond':
                    a=int(obj.get('a',-1));b=int(obj.get('b',-1))
                    if not (0<=a<state.count and 0<=b<state.count and a!=b):raise ValueError('Select two different valid native cells')
                    key=tuple(sorted((a,b)))
                    action=obj.get('action','bond')
                    if action=='bond':
                        if key in pair_bonds:raise ValueError('Pair already bonded; break it before rebonding')
                        strength=max(0,min(100,int(obj.get('strength',50))))
                        old_a=int(state.cells[a]);old_b=int(state.cells[b]);new=[]
                        for source,target in ((old_a,old_b),(old_b,old_a)):
                            value=0
                            for shift in (0,8,16):
                                c=(source>>shift)&255;d=(target>>shift)&255
                                value|=(round((c*(100-strength)+d*strength)/100)&255)<<shift
                            new.append(value)
                        lib.hex_set_cell(ctypes.byref(state),a,new[0]);lib.hex_set_cell(ctypes.byref(state),b,new[1])
                        pair_bonds[key]=(old_a,old_b,new[0],new[1])
                    elif action=='break':
                        if key not in pair_bonds:raise ValueError('No stored bond for this pair')
                        old_a,old_b,applied_a,applied_b=pair_bonds[key]
                        # Only restore if the values have not changed since bonding.
                        if int(state.cells[a])!=applied_a or int(state.cells[b])!=applied_b:
                            raise ValueError('Cells changed since bonding; cannot safely restore previous values')
                        lib.hex_set_cell(ctypes.byref(state),a,old_a);lib.hex_set_cell(ctypes.byref(state),b,old_b)
                        del pair_bonds[key]
                    else:raise ValueError('Action must be bond or break')
                    history.append({'tick':int(state.tick),'value':int(state.checksum),'mean':sum(state.cells[:state.count])//state.count})
                    if len(history)>500:del history[:-500]
                elif self.path=='/api/transform':
                    # Explicit, bounded, deterministic native cell transforms.
                    # Validate every argument before touching the C state.
                    if running:raise ValueError('Pause engine before applying transformations')
                    op=obj.get('operation')
                    if op not in ('xor','add','and','or','rotate_left'):raise ValueError('Unsupported transform operation')
                    start=int(obj.get('start',0));count=int(obj.get('count',1));operand=int(str(obj.get('operand','0')),0)
                    if not (0<=start<state.count and 1<=count<=4096 and start+count<=state.count):raise ValueError('Invalid cell range')
                    if not (0<=operand<=0xFFFFFF):raise ValueError('Operand must fit in 24 bits')
                    original=[int(state.cells[i]) for i in range(start,start+count)]
                    def transform(value):
                        if op=='xor':return value^operand
                        if op=='add':return (value+operand)&0xFFFFFF
                        if op=='and':return value&operand
                        if op=='or':return value|operand
                        n=operand%24
                        return ((value<<n)|(value>>(24-n if n else 24)))&0xFFFFFF
                    updated=[transform(v) for v in original]
                    for offset,value in enumerate(updated):
                        if not lib.hex_set_cell(ctypes.byref(state),start+offset,value):raise RuntimeError('Native cell write failed')
                    history.append({'tick':int(state.tick),'value':int(state.checksum),'mean':sum(state.cells[:state.count])//state.count})
                    if len(history)>500:del history[:-500]
                elif self.path=='/api/cell':
                    index=int(obj['index']);value=obj['hex']
                    if not isinstance(value,str) or not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{1,6}',value):raise ValueError('Cell value must be 1–6 hexadecimal digits')
                    if not lib.hex_set_cell(ctypes.byref(state),index,int(value.removeprefix('0x').removeprefix('0X'),16)):raise ValueError('Invalid cell index or value')
                    history.append({'tick':int(state.tick),'value':int(state.checksum),'mean':sum(state.cells[:state.count])//state.count})
                    if len(history)>500:del history[:-500]
                elif self.path=='/api/input':
                    source=obj.get('hex','')
                    if not isinstance(source,str) or not re.fullmatch(r'[\s,0-9a-fA-FxX]+',source):raise ValueError('Use hexadecimal blocks separated by spaces or commas')
                    tokens=source.replace(',',' ').split()
                    if not 1<=len(tokens)<=10000 or any(not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{1,6}',t) for t in tokens):raise ValueError('Provide 1–10000 hex blocks, 1–6 digits each')
                    initialize([int(t.removeprefix('0x').removeprefix('0X'),16) for t in tokens])
                elif self.path=='/api/dimension':
                    dim=int(obj.get('dimension',8))
                    if dim not in (8,12,16,24,32):raise ValueError('Dimension must be 8, 12, 16, 24, or 32')
                    running=False;initialize([0x071EB8,0xDB10BC,0xEB1078,0x0B1DBC],dim)
                elif self.path=='/api/reset':
                    running=False;initialize([0x071EB8,0xDB10BC,0xEB1078,0x0B1DBC])
                elif self.path=='/api/step':step()
                elif self.path=='/api/save':
                    SAVE.parent.mkdir(exist_ok=True)
                    data={'format':'hex-studio-v4-state-1','cells':list(state.cells[:state.count]),'stages':list(state.stages),'stage_changes':list(state.stage_changes),'tick':int(state.tick),'checksum':int(state.checksum),'flags':int(state.flags),'interval':interval,'running':running,'history':history,'persistent_network':{'autonomous':{'enabled':auto_enabled,'similarity':auto_similarity,'scan_budget':auto_scan_budget},'enabled':network_enabled,'bonds':[]},'bonding':{'enabled':False,'strength':0,'threshold':0},'separation':{'rate':separation_rate,'amplitude':separation_amplitude},'unified_dynamics':{'bond_rate':unified_bond_rate,'flow_rate':unified_flow_rate}}
                    temp=SAVE.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(SAVE)
                    self.respond(200,{'saved':str(SAVE),'tick':int(state.tick)});return
                elif self.path=='/api/load':restore(json.loads(SAVE.read_text()))
                else:self.respond(404,{'error':'Unknown endpoint'});return
                self.respond(200,snapshot())
        except (ValueError,TypeError,KeyError,FileNotFoundError,json.JSONDecodeError) as e:self.respond(400,{'error':str(e)})
        except Exception as e:self.respond(500,{'error':str(e)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8097);args=p.parse_args()
    server=None
    for port in [args.port]:
        try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
        except OSError:continue
    if server is None:raise SystemExit(f'Cannot bind to 127.0.0.1:{args.port}; stop the old server or set HEX_STUDIO_PORT to another port')
    from v22_queue import ResearchQueue
    research_queue=ResearchQueue(ROOT,server.server_port)
    print(f'Hex Studio Pro: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
