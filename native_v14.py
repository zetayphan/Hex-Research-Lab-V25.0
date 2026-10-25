"""V14 source-aligned neighbor-stage investigation; no unsupported global inverse claims."""
import hashlib
from native_stage_v13 import MASK, rol, SOURCE, NEIGHBOR

def neighbors(a,i,n):
 N=len(a); assert N==n**3
 left=a[i+n-1 if i%n==0 else i-1]
 right=a[i-n+1 if i%n==n-1 else i+1]
 up=a[(i+N-n*n)%N]; down=a[(i+n*n)%N]
 return left,right,up,down

def forward(stage,a,n,flags=1):
 if stage not in NEIGHBOR: raise ValueError('Only six neighbor-dependent stages supported')
 out=[]
 for i,v in enumerate(a):
  l,r,u,d=neighbors(a,i,n)
  if stage==0: w=v+rol(r,1)
  elif stage==3: w=v+((l^r)&255) if flags&1 else v
  elif stage==4: w=v+((l-r)&MASK)
  elif stage==7: w=v^rol(l,3)
  elif stage==10: w=v+rol(r^u^d,i%7+1)
  else: w=v^((l+r+u+d)&MASK)
  out.append(w&MASK)
 return out

def inverse_with_known_neighbors(stage,output,original_neighbors,n,flags=1):
 """Inverse only when original neighbor values are supplied as side information."""
 if len(output)!=len(original_neighbors):raise ValueError('length mismatch')
 result=[]
 for i,w in enumerate(output):
  l,r,u,d=neighbors(original_neighbors,i,n)
  if stage==0: v=w-rol(r,1)
  elif stage==3: v=w-((l^r)&255) if flags&1 else w
  elif stage==4: v=w-((l-r)&MASK)
  elif stage==7: v=w^rol(l,3)
  elif stage==10: v=w-rol(r^u^d,i%7+1)
  elif stage==11: v=w^((l+r+u+d)&MASK)
  else: raise ValueError('invalid stage')
  result.append(v&MASK)
 return result

def report():
 digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 rows=[]
 for s in sorted(NEIGHBOR):
  rows.append({'stage':s,'classification':'conditionally invertible with original neighbor values',
               'global_injectivity':'unresolved', 'side_information_required':True,
               'note':'The side information includes values from the input frame; it is not reconstructed from the output.'})
 return {'version':'14','source_sha256':digest,'source':'src/engine.c',
         'scope':'simultaneous neighbor-dependent stage; periodic z and y indexing as in native source',
         'stages':rows,'global_inverse_verified':False,
         'warning':'Conditional recovery using original input neighbors does not prove injectivity or reversibility of the coupled stage or full native engine.'}
