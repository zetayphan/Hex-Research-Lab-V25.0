import unittest,tempfile,pathlib,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from v231_cycle import propose,submit,review,PREDICATES
class Queue:
 def __init__(self):self.jobs=[]
 def submit(self,cells,steps,repetitions):
  j={'id':'a'*32,'status':'queued','completed':0,'repetitions':repetitions};self.jobs.append(j);return j
 def list(self):return self.jobs
class TestV243(unittest.TestCase):
 def test_four_candidates_from_changed_data(self):
  with tempfile.TemporaryDirectory() as d:
   f=pathlib.Path(d)/'research_data/v202/playback';f.mkdir(parents=True)
   (f/'discovery.json').write_text(json.dumps({'records':[{'stage':1,'cell':0,'input':1,'output':2}]}))
   for key in PREDICATES:
    plan=propose(d,[0],1,1,key)
    self.assertEqual(plan['hypothesis'],key)
    self.assertEqual(plan['discovery_run'],'discovery')
   q=Queue();cycle=submit(d,q,[0],1,1,'parity_preserved')
   self.assertEqual(cycle['plan']['hypothesis'],'parity_preserved')
 def test_invalid_hypothesis(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'Unknown hypothesis'):propose(d,hypothesis='bogus')
 def test_hex_encoded_linked_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);f=root/'research_data/v202/playback';f.mkdir(parents=True)
   (f/'discovery.json').write_text(json.dumps({'records':[{'input':1,'output':2}]}))
   q=Queue();cycle=submit(d,q,[0],1,1,'parity_preserved')
   rid='b'*32
   (f/(rid+'.json')).write_text(json.dumps({'id':rid,'job_id':'a'*32,'linkage_schema':'hex-v23.2-verified-job-evidence','records':[{'input':'0x01','output':'0x03'},{'input':'0x01','output':'0x02'}]}))
   q.jobs[0].update(status='completed',completed=1,results=[{'playback_runs':[rid]}])
   result=review(d,q,cycle['id'])
   self.assertEqual(result['tested_records'],2)
   self.assertEqual(result['counterexamples'],1)
   self.assertEqual(result['assessment'],'CONTRADICTED')
if __name__=='__main__':unittest.main()
