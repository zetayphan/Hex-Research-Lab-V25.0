"""Finite-state theorem demonstrations and empirical checks (not proofs of engine reversibility)."""
import argparse,json,urllib.request,math

def cyclic_example():
    s=(4,0,0); orbit=[]
    for _ in range(4):
        orbit.append({'state':list(s),'invariant':sum(s),'structural_measure':s[0]+2*s[1]+3*s[2]})
        s=(s[2],s[0],s[1])
    assert orbit[0]==orbit[-1]
    assert len({v['structural_measure'] for v in orbit})==3
    assert all(v['invariant']==4 for v in orbit)
    return {'example':'three-coordinate permutation','cycle_length':3,'orbit':orbit,'verified':True}

def compare(a,b):
    x=a['values'];y=b['values']
    if len(x)!=len(y):raise ValueError('Different cell counts')
    sums=lambda v:[sum((z>>shift)&255 for z in v) for shift in (16,8,0)]
    ra,rb=sums(x),sums(y)
    return {'ticks':[a['tick'],b['tick']],'cells':len(x),'changed_cells':sum(i!=j for i,j in zip(x,y)), 'rgb_totals_before':ra,'rgb_totals_after':rb,'rgb_delta':[j-i for i,j in zip(ra,rb)],'rgb_conserved':ra==rb,'note':'The full Studio step includes nonconservative transforms; a failed conservation check does not refute the conditional theorem. Neither this comparison nor checksum equality establishes reversibility.'}

def request(port,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers={'Content-Type':'application/json'} if data else {},method='POST' if data else 'GET')
    with urllib.request.urlopen(req,timeout=10) as r:return json.load(r)

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8141);p.add_argument('--steps',type=int,default=1);p.add_argument('--example-only',action='store_true');a=p.parse_args()
    result={'mathematical_example':cyclic_example()}
    if not a.example_only:
        if not 1<=a.steps<=100: p.error('--steps must be between 1 and 100')
        before=request(a.port,'/api/state')
        for _ in range(a.steps):request(a.port,'/api/step',{})
        after=request(a.port,'/api/state')
        result['live_engine_observation']=compare(before,after)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
