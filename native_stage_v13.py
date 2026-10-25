"""V13 source-specific stage reversibility classification for src/engine.c.
Proofs apply to a single stage with fixed parameters, not the coupled engine.
"""
import hashlib, pathlib, re
MASK=(1<<24)-1
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/'src'/'engine.c'
# Reviewed against the switch(stage) in the bundled C source.
NAMES=['late model','layout','location','extension','derive structure','operation control','derived coordinates','left XOR','operation integration','layout integration','neighbor sum','neighbor XOR','file processing','output delta','input XOR','rotate feedback','persistence']
IDENTITY={1,5,6,8,9,12,16}
POINTWISE={2,13,14,15}
NEIGHBOR={0,3,4,7,10,11}

def rol(v,n):
 n%=24
 return ((v<<n)|(v>>(24-n)))&MASK if n else v&MASK

def ror(v,n):return rol(v,24-n)

def forward(stage,values):
 if stage not in IDENTITY|POINTWISE:raise ValueError('No verified independent stage implementation')
 out=[]
 for i,v in enumerate(values):
  if stage==2:v^=(i*0x10101)&MASK
  elif stage==13:v=(v+0x45C881)&MASK
  elif stage==14:v^=0x4BF981
  elif stage==15:v=rol(v,1)
  out.append(v)
 return out

def inverse(stage,values):
 if stage not in IDENTITY|POINTWISE:raise ValueError('Inverse unestablished for coupled stage')
 out=[]
 for i,v in enumerate(values):
  if stage==2:v^=(i*0x10101)&MASK
  elif stage==13:v=(v-0x45C881)&MASK
  elif stage==14:v^=0x4BF981
  elif stage==15:v=ror(v,1)
  out.append(v)
 return out

def report():
 source=SOURCE.read_text()
 # Fail closed if audited source changes: review required rather than carrying over assertions.
 signature=hashlib.sha256(source.encode()).hexdigest()
 rows=[]
 for stage,name in enumerate(NAMES):
  status='proved for isolated stage' if stage in IDENTITY|POINTWISE else 'unresolved coupled-neighbor mapping'
  rows.append({'stage':stage,'name':name,'classification':status,'inverse_available':stage in IDENTITY|POINTWISE})
 return {'source':'src/engine.c','source_sha256':signature,'scope':'isolated 24-bit stage on fixed-size cell array; parameters fixed',
         'stages':rows,'proven_isolated':len(IDENTITY|POINTWISE),'unresolved':len(NEIGHBOR),
         'native_full_inverse_verified':False,'note':'No noninjectivity claimed for unresolved stages; complete tick, checksum, stage traces and auxiliary state are not inverted.'}
