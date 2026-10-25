"""HEX language V3: bounded, non-Python mathematical scripts."""
import ast, operator, re
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.BitXor:operator.xor,ast.LShift:operator.lshift,ast.RShift:operator.rshift}
class HexLanguageError(ValueError):pass
class Interpreter:
 def __init__(self, shell):self.shell=shell;self.vars={};self.budget=2000
 def eval(self,expr):
  if len(expr)>512:raise HexLanguageError('expression too long')
  def walk(n,depth=0):
   if depth>24:raise HexLanguageError('expression too deep')
   if isinstance(n,ast.Constant) and type(n.value)==int:v=n.value
   elif isinstance(n,ast.Name) and n.id in self.vars:v=self.vars[n.id]
   elif isinstance(n,ast.UnaryOp) and type(n.op) in (ast.UAdd,ast.USub,ast.Invert):
    a=walk(n.operand,depth+1);v={ast.UAdd:lambda x:+x,ast.USub:lambda x:-x,ast.Invert:lambda x:~x}[type(n.op)](a)
   elif isinstance(n,ast.BinOp) and type(n.op) in OPS:
    a=walk(n.left,depth+1);b=walk(n.right,depth+1)
    if isinstance(n.op,(ast.LShift,ast.RShift)) and not 0<=b<=256:raise HexLanguageError('invalid shift')
    v=OPS[type(n.op)](a,b)
   else:raise HexLanguageError('unsupported expression or unknown variable')
   if v.bit_length()>256:raise HexLanguageError('256-bit limit exceeded')
   return v
  try:return walk(ast.parse(expr,mode='eval').body)
  except (SyntaxError,ZeroDivisionError,OverflowError) as e:raise HexLanguageError(str(e)) from e
 def execute(self,source):
  lines=source.splitlines()
  if len(lines)>500:raise HexLanguageError('500-line limit')
  def block(start,end):
   i=start
   while i<end:
    line=lines[i].strip();i+=1
    if not line or line.startswith('#'):continue
    self.budget-=1
    if self.budget<0:raise HexLanguageError('execution budget exceeded')
    match=re.fullmatch(r'REPEAT\s+(.+)',line,re.I)
    if match:
     count=self.eval(match.group(1))
     if not 0<=count<=100:raise HexLanguageError('repeat count must be 0..100')
     depth=1;j=i
     while j<end and depth:
      token=lines[j].strip().split(maxsplit=1)[0].upper() if lines[j].strip() else ''
      if token=='REPEAT':depth+=1
      if token=='END':depth-=1
      j+=1
     if depth:raise HexLanguageError('missing END')
     for _ in range(count):block(i,j-1)
     i=j;continue
    if line.upper()=='END':raise HexLanguageError('unexpected END')
    match=re.fullmatch(r'LET\s+([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(.+)',line,re.I)
    if match:self.vars[match.group(1)]=self.eval(match.group(2));continue
    match=re.fullmatch(r'PRINT\s+(.+)',line,re.I)
    if match:
     v=self.eval(match.group(1));print(f'{v} (0x{v:X})' if v>=0 else f'{v} (-0x{-v:X})');continue
    match=re.fullmatch(r'ASSERT\s+(.+?)\s*(==|!=|<=|>=|<|>)\s*(.+)',line,re.I)
    if match:
     a=self.eval(match.group(1));b=self.eval(match.group(3));op=match.group(2)
     if not {'==':operator.eq,'!=':operator.ne,'<':operator.lt,'>':operator.gt,'<=':operator.le,'>=':operator.ge}[op](a,b):raise HexLanguageError(f'assertion failed: {line}')
     continue
    # V4 native writes operate on actual engine cells through the existing HTTP API.
    match=re.fullmatch(r'CELL\s+(.+?)\s*=\s*(.+)',line,re.I)
    if match:
     index=self.eval(match.group(1));value=self.eval(match.group(2))
     if not 0<=value<=0xFFFFFF:raise HexLanguageError('cell value must be 0x000000..0xFFFFFF')
     state=self.shell.safe('/api/state')
     if state is None:raise HexLanguageError('native state unavailable')
     if not 0<=index<state['cell_count']:raise HexLanguageError('cell index out of range')
     if self.shell.safe('/api/cell',{'index':index,'hex':f'{value:06X}'}) is None:raise HexLanguageError('native cell write failed')
     print(f'cell {index} <- 0x{value:06X}');continue
    match=re.fullmatch(r'READ\s+([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(.+)',line,re.I)
    if match:
     index=self.eval(match.group(2));state=self.shell.safe('/api/state')
     if state is None:raise HexLanguageError('native state unavailable')
     if not 0<=index<len(state['values']):raise HexLanguageError('cell index out of range')
     self.vars[match.group(1)]=state['values'][index];continue
    match=re.fullmatch(r'TRANSFORM\s+(.+?)\s+(.+)',line,re.I)
    if match:
     # Transform a native cell with a bounded expression using variable VALUE.
     index=self.eval(match.group(1));state=self.shell.safe('/api/state')
     if state is None:raise HexLanguageError('native state unavailable')
     if not 0<=index<len(state['values']):raise HexLanguageError('cell index out of range')
     old=self.vars.get('VALUE');had='VALUE' in self.vars
     try:
      self.vars['VALUE']=state['values'][index]
      value=self.eval(match.group(2))
     finally:
      if had:self.vars['VALUE']=old
      else:self.vars.pop('VALUE',None)
     if not 0<=value<=0xFFFFFF:raise HexLanguageError('transform must produce 24-bit RGB value')
     if self.shell.safe('/api/cell',{'index':index,'hex':f'{value:06X}'}) is None:raise HexLanguageError('native transform failed')
     print(f'cell {index}: 0x{state["values"][index]:06X} -> 0x{value:06X}');continue
    match=re.fullmatch(r'NATIVE\s+(status|hex|rgb|step|engines|diagnostics|state)(?:\s+(.*))?',line,re.I)
    if match:
     command=match.group(1).lower();arg=match.group(2) or ''
     if command in ('step',) and self.budget<1:raise HexLanguageError('budget exceeded')
     getattr(self.shell,'do_'+command)(arg);continue
    raise HexLanguageError(f'unknown instruction: {line}')
  block(0,len(lines))
