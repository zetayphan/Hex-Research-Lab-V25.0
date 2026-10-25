"""V5: deterministic native-cell operations, snapshots, comparisons and tracing."""
import json, pathlib, shlex, time, math

MASK=0xFFFFFF
OPS=('xor','add','and','or','rol')
def transform(value, operation, operand):
    if not 0<=value<=MASK or not 0<=operand<=MASK: raise ValueError('24-bit operands required')
    if operation=='xor': return value^operand
    if operation=='add': return (value+operand)&MASK
    if operation=='and': return value&operand
    if operation=='or': return value|operand
    if operation=='rol':
        n=operand%24
        return ((value<<n)|(value>>(24-n if n else 24)))&MASK
    raise ValueError('unknown operation: '+operation)

def metrics(a,b):
    if len(a)!=len(b): raise ValueError('different cell counts')
    n=len(a)
    if not n: raise ValueError('empty state')
    dif=[abs(x-y) for x,y in zip(a,b)]
    return {'cells':n,'changed':sum(x!=y for x,y in zip(a,b)), 'mean_absolute_difference':sum(dif)/n,
            'root_mean_square_difference':math.sqrt(sum(d*d for d in dif)/n),
            'changed_bits':sum((x^y).bit_count() for x,y in zip(a,b))}

class V5Mixin:
    def _v5_dir(self):
        p=pathlib.Path(__file__).resolve().parent/'experiments'/'v5_snapshots';p.mkdir(parents=True,exist_ok=True);return p
    def _v5_name(self,name):
        if not name or len(name)>48 or not all(c.isalnum() or c in '-_' for c in name):raise ValueError('use a simple name (letters, digits, _ or -)')
        return self._v5_dir()/(name+'.json')
    def _v5_state(self):
        s=self.safe('/api/state')
        if s is None:raise RuntimeError('native state unavailable')
        return s
    def do_snapshot(self,arg):
        "Save/list native snapshots: snapshot save NAME | snapshot list."
        try:
            p=shlex.split(arg)
            if p==['list']:
                print('\n'.join(x.stem for x in sorted(self._v5_dir().glob('*.json'))) or '(none)');return
            if len(p)!=2 or p[0]!='save':raise ValueError('usage: snapshot save NAME | snapshot list')
            s=self._v5_state();dest=self._v5_name(p[1]);data={'format':'hex-terminal-v5-snapshot','tick':s['tick'],'checksum':s['checksum'],'values':s['values']}
            dest.write_text(json.dumps(data,indent=2));print('Snapshot saved:',dest)
        except (ValueError,RuntimeError,OSError) as e:print('Snapshot error:',e)
    def do_compare(self,arg):
        "Compare snapshots or live state: compare NAME live | compare NAME NAME."
        try:
            a,b=shlex.split(arg)
            def read(n):
                if n=='live':return self._v5_state()['values']
                obj=json.loads(self._v5_name(n).read_text())
                if obj.get('format')!='hex-terminal-v5-snapshot':raise ValueError('unsupported snapshot')
                return obj['values']
            m=metrics(read(a),read(b));print(json.dumps(m,indent=2))
            self._last_comparison=m
        except (ValueError,RuntimeError,OSError,KeyError,json.JSONDecodeError) as e:print('Compare error:',e)
    def do_transform(self,arg):
        "Transform native cells: transform xor 0xFF 0 16 (OP OPERAND START COUNT)."
        try:
            p=shlex.split(arg)
            if len(p)!=4:raise ValueError('usage: transform OP OPERAND START COUNT')
            op=p[0].lower();operand=int(p[1],0);start=int(p[2],0);count=int(p[3],0)
            if op not in OPS or not 0<=operand<=MASK or not 0<=count<=512:raise ValueError('invalid operation, operand or count (max 512)')
            s=self._v5_state();values=s['values']
            if not 0<=start<len(values) or start+count>len(values):raise ValueError('cell range outside native lattice')
            if s['running']:raise ValueError('pause engine with stop before transforming')
            for i in range(start,start+count):
                v=transform(values[i],op,operand)
                if self.safe('/api/cell',{'index':i,'hex':f'{v:06X}'}) is None:raise RuntimeError('cell write failed at '+str(i))
            print(f'Applied {op} to {count} native cells. Open dashboard to see the changes.')
        except (ValueError,RuntimeError) as e:print('Transform error:',e)
    def do_auto(self,arg):
        "Run bounded automatic operations: auto CYCLES [COUNT] (paused engine)."
        try:
            p=shlex.split(arg);cycles=int(p[0]) if p else 5;count=int(p[1]) if len(p)>1 else 16
            if len(p)>2 or not 1<=cycles<=100 or not 1<=count<=128:raise ValueError('cycles 1..100; cells 1..128')
            s=self._v5_state()
            if s['running']:raise ValueError('stop engine before auto operations')
            count=min(count,len(s['values']))
            for i in range(cycles):
                op=OPS[i%len(OPS)];operand=[0x55AA33,0x010101,0xFFFF00,0x0000FF,3][i%len(OPS)]
                self.do_transform(f'{op} {operand} 0 {count}')
                s=self._v5_state();print(f'cycle {i+1}/{cycles} tick={s["tick"]} checksum={s["checksum"]}')
            print('Automatic operation batch complete.')
        except (ValueError,RuntimeError) as e:print('Auto error:',e)
        except KeyboardInterrupt:print('\nAuto interrupted.')
    def do_trace(self,arg):
        "Capture native engine evolution: trace STEPS (1..200); engine must be paused."
        try:
            n=int(arg.strip() or '10')
            if not 1<=n<=200:raise ValueError('steps 1..200')
            if self._v5_state()['running']:raise ValueError('stop engine first')
            records=[]
            for _ in range(n):
                if self.safe('/api/step',{}) is None:raise RuntimeError('native step failed')
                s=self._v5_state();records.append({'tick':s['tick'],'checksum':s['checksum'],'mean':sum(s['values'])/len(s['values'])})
            path=self._v5_dir()/'last_trace.json';path.write_text(json.dumps(records,indent=2))
            for r in records:print('tick={} checksum={} mean={:.2f}'.format(**r))
            print('Trace saved:',path)
        except (ValueError,RuntimeError,OSError) as e:print('Trace error:',e)
        except KeyboardInterrupt:print('\nTrace interrupted.')
