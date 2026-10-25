#!/usr/bin/env python3
"""CLI verification; --live advances the native engine when --steps > 0."""
import argparse,json,urllib.request
from verification_engine import report,compare_snapshots
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--steps',type=int,default=0);p.add_argument('--port',type=int,default=8141);a=p.parse_args()
if not 0<=a.steps<=100: p.error('steps must be 0..100')
def call(path,post=False):
 req=urllib.request.Request(f'http://127.0.0.1:{a.port}'+path,data=b'{}' if post else None,headers={'Content-Type':'application/json'} if post else {})
 with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)
if a.steps and not a.live:p.error('--steps requires --live')
if a.live:
 before=call('/api/state')
 for _ in range(a.steps):call('/api/step',True)
 after=call('/api/state');result=report(after);result['comparison']=compare_snapshots(before,after)
else:result=report()
print(json.dumps(result,indent=2))
