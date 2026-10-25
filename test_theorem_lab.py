import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from theorem_lab import cyclic_example,compare
r=cyclic_example();assert r['verified'] and r['cycle_length']==3
s={'values':[0x010203,0x040506],'tick':0};t={'values':[0x010203,0x040506],'tick':1}
assert compare(s,t)['rgb_conserved']
t['values'][0]=0x020203
assert compare(s,t)['rgb_delta']==[1,0,0]
print('PASS: theorem cycle and RGB comparison')
