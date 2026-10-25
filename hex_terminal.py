#!/usr/bin/env python3
"""Hex Terminal Pro X: interactive shell backed by the original native engine HTTP API."""
import hexlang
from v5_features import V5Mixin
import cmd, json, os, pathlib, shlex, subprocess, sys, time, urllib.request, urllib.error, webbrowser, ast, operator
ROOT=pathlib.Path(__file__).resolve().parent
PORT=int(os.environ.get('HEX_STUDIO_PORT','8141'))
BASE=f'http://127.0.0.1:{PORT}'

def request(path, data=None):
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(BASE+path, data=body, headers={'Content-Type':'application/json'} if body else {},method='POST' if body else 'GET')
    try:
        with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
    except urllib.error.HTTPError as e:
        try:detail=json.load(e).get('error',e.reason)
        except Exception:detail=e.reason
        raise RuntimeError(f'API error: {detail}') from e

def ensure_server():
    try:request('/api/health');return None
    except Exception:pass
    proc=subprocess.Popen(['sh',str(ROOT/'start.sh')],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for _ in range(60):
        if proc.poll() is not None:
            msg=proc.stderr.read().decode(errors='replace')
            raise RuntimeError('Engine server failed to start: '+msg[-1500:])
        try:request('/api/health');return proc
        except Exception:time.sleep(.15)
    proc.terminate();raise RuntimeError('Engine server did not become ready; check port '+str(PORT))

class Shell(V5Mixin, cmd.Cmd):
    intro='HEX TERMINAL PRO X V5 | native C engine | type help for commands'
    prompt='hex@pro-x:~$ '
    def safe(self, path, data=None):
        try:return request(path,data)
        except Exception as e:print('Error:',e);return None
    def do_compute(self,arg):
        "Evaluate integer arithmetic (hex/decimal): compute 0xA3 + 0x7F."
        ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
             ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,
             ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.BitXor:operator.xor,
             ast.LShift:operator.lshift,ast.RShift:operator.rshift}
        def calc(node,depth=0):
            if depth>24:raise ValueError('expression too complex')
            if isinstance(node,ast.Constant) and type(node.value) is int:
                if node.value.bit_length()>256:raise ValueError('integer too large')
                return node.value
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub,ast.Invert)):
                v=calc(node.operand,depth+1)
                return +v if isinstance(node.op,ast.UAdd) else -v if isinstance(node.op,ast.USub) else ~v
            if isinstance(node,ast.BinOp) and type(node.op) in ops:
                a,b=calc(node.left,depth+1),calc(node.right,depth+1)
                if isinstance(node.op,(ast.LShift,ast.RShift)) and not 0<=b<=256:raise ValueError('shift out of range')
                v=ops[type(node.op)](a,b)
                if v.bit_length()>256:raise ValueError('result too large')
                return v
            raise ValueError('unsupported expression')
        try:
            if len(arg)>512:raise ValueError('expression too long')
            v=calc(ast.parse(arg,mode='eval').body)
            print(f'{v}  ({"-0x"+format(-v,"X") if v<0 else "0x"+format(v,"X")})')
        except (ValueError,SyntaxError,ZeroDivisionError,OverflowError) as e:print('Compute error:',e)
    def do_engine(self,arg):
        "Engine subcommands: engine status | engine list | engine start | engine stop."
        commands={'status':self.do_status,'list':self.do_engines,'start':self.do_start,'stop':self.do_stop}
        cmdname=arg.strip().lower()
        if cmdname in commands:commands[cmdname]('')
        else:print('Usage: engine status|list|start|stop')
    def do_watch(self,arg):
        "Live status updates; watch [seconds] [count]. Ctrl+C to stop."
        try:
            parts=shlex.split(arg);interval=float(parts[0]) if parts else 1.0
            count=int(parts[1]) if len(parts)>1 else 0
            if not 0.2<=interval<=60 or not 0<=count<=10000 or len(parts)>2:raise ValueError()
        except ValueError:print('Usage: watch [interval 0.2-60] [count 0-10000; 0=until Ctrl+C]');return
        n=0
        try:
            while not count or n<count:
                s=self.safe('/api/state')
                if s is None:break
                print(f"tick={s['tick']} checksum=0x{s['checksum']} running={s['running']}",flush=True)
                n+=1
                if not count or n<count:time.sleep(interval)
        except KeyboardInterrupt:print('\nWatch stopped.')
    def do_script(self,arg):
        "Run a local .hex command script: script run experiments/demo.hex."
        try:parts=shlex.split(arg)
        except ValueError:print('Usage: script run FILE.hex');return
        if len(parts)!=2 or parts[0]!='run':print('Usage: script run FILE.hex');return
        target=(ROOT/parts[1]).resolve()
        if target.suffix.lower()!='.hex' or not target.is_relative_to(ROOT):print('Scripts must be .hex files inside the project.');return
        if getattr(self,'_script_running',False):print('Nested scripts are disabled.');return
        try:
            lines=target.read_text(encoding='utf-8').splitlines()
            if len(lines)>500:raise ValueError('script exceeds 500 lines')
            self._script_running=True
            for lineno,line in enumerate(lines,1):
                line=line.strip()
                if not line or line.startswith('#'):continue
                if line.split()[0] in ('exit','quit','EOF','script','watch'):raise ValueError(f'line {lineno}: command disallowed in scripts')
                print(f'[{lineno}] {line}')
                self.onecmd(line)
            print('Script complete.')
        except (OSError,UnicodeError,ValueError) as e:print('Script error:',e)
        finally:self._script_running=False
    def do_program(self,arg):
        "Run V3 language: program run experiments/v3_demo.hex | program eval EXPRESSION."
        try:parts=shlex.split(arg)
        except ValueError:print('Usage: program run FILE.hex | program eval EXPR');return
        if not parts:print('Usage: program run FILE.hex | program eval EXPR');return
        interpreter=getattr(self,'_hexlang',None)
        if interpreter is None:interpreter=self._hexlang=hexlang.Interpreter(self)
        try:
            if parts[0]=='eval' and len(parts)>1:
                v=interpreter.eval(' '.join(parts[1:]));print(f'{v} (0x{v:X})');return
            if parts[0]=='run' and len(parts)==2:
                target=(ROOT/parts[1]).resolve()
                if target.suffix.lower()!='.hex' or not target.is_relative_to(ROOT):raise ValueError('use a .hex file inside the project')
                interpreter.budget=2000
                interpreter.execute(target.read_text(encoding='utf-8'))
                print('Program complete.');return
            print('Usage: program run FILE.hex | program eval EXPR')
        except (OSError,ValueError,hexlang.HexLanguageError) as e:print('Program error:',e)
    def do_hexlang(self,arg):
        "Enter interactive HEX language mode (type exit to return)."
        interpreter=getattr(self,'_hexlang',None)
        if interpreter is None:interpreter=self._hexlang=hexlang.Interpreter(self)
        print('HEX language V4 | LET, PRINT, READ, CELL, TRANSFORM, ASSERT, NATIVE | exit to return')
        lines=[];depth=0
        while True:
            try:line=input('hex... ' if depth else 'hex>>> ')
            except (EOFError,KeyboardInterrupt):print();return
            if line.strip().lower() in ('exit','quit') and not depth:return
            if line.strip().upper().startswith('REPEAT '):depth+=1
            if line.strip().upper()=='END':depth-=1
            lines.append(line)
            if depth>0:continue
            if depth<0:print('Unexpected END');lines=[];depth=0;continue
            try:interpreter.budget=2000;interpreter.execute('\n'.join(lines))
            except (ValueError,hexlang.HexLanguageError) as e:print('Program error:',e)
            lines=[]
    def default(self,line):
        "Recognize HEX language instructions directly in the shell."
        if line.strip().split(maxsplit=1)[0].upper() in ('LET','PRINT','ASSERT','READ','CELL','TRANSFORM','NATIVE'):
            interpreter=getattr(self,'_hexlang',None)
            if interpreter is None:interpreter=self._hexlang=hexlang.Interpreter(self)
            try:interpreter.budget=2000;interpreter.execute(line)
            except (ValueError,hexlang.HexLanguageError) as e:print('Program error:',e)
        else:print('Unknown command. Type help.')
    def do_history(self,arg):
        "Display commands entered in this terminal session."
        for i,line in enumerate(getattr(self,'_history',[]),1):print(f'{i:4}  {line}')
    def precmd(self,line):
        if line.strip() and not getattr(self,'_script_running',False):
            self._history=(getattr(self,'_history',[])+[line])[-200:]
        return line
    def do_status(self,arg):
        "Show engine running state, tick, checksum and diagnostics."
        s=self.safe('/api/state')
        if s:
            d=s['diagnostics'];print(f"Engine: {'RUNNING' if s['running'] else 'PAUSED'} | tick {s['tick']} | checksum 0x{s['checksum']}")
            print(f"Native cells: {s['cell_count']} | lattice: {s['dimension']}³ | stages: {len(s['stages'])}")
            print(f"Steps: {d['steps_total']} | errors: {d['errors_total']} | interval: {s['interval_ms']} ms")
            if s['error']:print('Last error:',s['error'])
    def do_engines(self,arg):
        "List all 17 native mathematical processing stages."
        s=self.safe('/api/state')
        if s:
            for i,stage in enumerate(s['stages'],1):print(f"{i:02}  {stage['name']:<35} {stage['status']:<9}  0x{stage['checksum']}  changed={stage['changed_cells']}")
    def do_start(self,arg):
        "Resume continuous mathematical processing."
        if self.safe('/api/control',{'running':True}) is not None:print('Engine running.')
    def do_stop(self,arg):
        "Pause continuous mathematical processing."
        if self.safe('/api/control',{'running':False}) is not None:print('Engine paused.')
    def do_reset(self,arg):
        "Reset the native state (leaves engine paused)."
        if self.safe('/api/reset',{}) is not None:print('Native state reset. Type start to resume.')
    def do_step(self,arg):
        "Execute one mathematical processing step."
        if self.safe('/api/step',{}) is not None:self.do_hex('')
    def do_hex(self,arg):
        "Show native checksum and sample hexadecimal cells; optional number (1-64)."
        s=self.safe('/api/state')
        if s:
            try:n=max(1,min(64,int(arg or '12')))
            except ValueError:print('Usage: hex [1-64]');return
            print(f"Tick {s['tick']} | checksum 0x{s['checksum']}")
            for i in range(0,n,4):print('  '+'  '.join(f'{j:04}:0x{s["hex"][j]}' for j in range(i,min(i+4,n,len(s['hex'])))))
    def do_rgb(self,arg):
        "Show real RGB channels from native state cells."
        s=self.safe('/api/state')
        if s:
            for i,value in enumerate(s['values'][:8]):print(f"cell {i:03}: R={(value>>16)&255:3} G={(value>>8)&255:3} B={value&255:3}  #{value:06X}")
            print('Bonding:',s['bonding']['enabled'],'| separation:',s['separation']['mode'])
            if arg.strip()=='analyze':
                vals=s['values'];n=len(vals)
                if n:
                    avg=[sum((v>>shift)&255 for v in vals)/n for shift in (16,8,0)]
                    print('Channel means: R={:.2f} G={:.2f} B={:.2f} ({} native cells)'.format(*avg,n))
            elif arg.strip():print('Usage: rgb [analyze]')
    def do_state(self,arg):
        "Show native state summary."
        s=self.safe('/api/state')
        if s:
            for k in ('version','tick','checksum','dimension','cell_count','running','extension','interval_ms'):print(f'{k}: {s[k]}')
    def do_diagnostics(self,arg):
        "Show actual native engine diagnostics."
        s=self.safe('/api/state')
        if s:
            for k,v in s['diagnostics'].items():print(f'{k}: {v}')
    def do_visualize(self,arg):
        "Render an 8x8 ASCII brightness map of a native lattice slice."
        s=self.safe('/api/state')
        if s:
            d=s['dimension'];chars=' .:-=+*#%@';vals=s['values'];print(f'Native lattice z=0, {d}x{d} (sampled to 8x8):')
            for y in range(8):
                row=''
                for x in range(8):
                    v=vals[min(d-1,y*d//8)*d+min(d-1,x*d//8)]
                    lum=(((v>>16)&255)+((v>>8)&255)+(v&255))//3
                    row+=chars[min(len(chars)-1,lum*len(chars)//256)]*2
                print(row)
    def do_input(self,arg):
        "Initialize from hex blocks: input 0xFF0000 00FF00 0000FF"
        if not arg.strip():print('Usage: input HEX [HEX ...]');return
        if self.safe('/api/input',{'hex':arg}) is not None:print('Input applied to native state.')
    def do_cell(self,arg):
        "Set native cell: cell INDEX HEXVALUE"
        try:i,v=shlex.split(arg);i=int(i)
        except ValueError:print('Usage: cell INDEX HEXVALUE');return
        if self.safe('/api/cell',{'index':i,'hex':v}) is not None:print('Cell updated.')
    def do_speed(self,arg):
        "Set update interval in milliseconds (50-5000): speed 400"
        try:ms=int(arg);assert 50<=ms<=5000
        except (ValueError,AssertionError):print('Usage: speed MILLISECONDS (50-5000)');return
        if self.safe('/api/control',{'interval_ms':ms}) is not None:print('Interval set:',ms,'ms')
    def do_save(self,arg):
        "Save current native state to saved/state.json."
        s=self.safe('/api/save',{})
        if s:print('Saved:',s['saved'])
    def do_dashboard(self,arg):
        "Print dashboard URL (optionally: dashboard open)."
        print(BASE+'/')
        if arg.strip()=='open':webbrowser.open(BASE+'/')
    def do_clear(self,arg):
        "Clear terminal screen."
        print('\033[2J\033[H',end='')
    def do_exit(self,arg):
        "Leave terminal; engine server continues running."
        return True
    do_quit=do_exit
    def do_EOF(self,arg):print();return True
    def emptyline(self):pass

if __name__=='__main__':
    try:
        ensure_server();Shell().cmdloop()
    except (KeyboardInterrupt,EOFError):print('\nExiting Hex Terminal.')
    except Exception as e:print('Startup error:',e,file=sys.stderr);sys.exit(1)
