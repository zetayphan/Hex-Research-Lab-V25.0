import unittest,tempfile,pathlib,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from v231_cycle import propose,submit,review
class FakeQueue:
 def __init__(self):self.jobs=[]
 def submit(self,cells,steps,repetitions):
  j={'id':'a'*32,'status':'queued','completed':0,'repetitions':repetitions};self.jobs.append(j);return j
 def list(self):return self.jobs
class TestCycle(unittest.TestCase):
 def test_requires_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):propose(d)
 def test_submit_and_review(self):
  with tempfile.TemporaryDirectory() as d:
   folder=pathlib.Path(d)/'research_data/v202/playback';folder.mkdir(parents=True)
   (folder/'discovery.json').write_text(json.dumps({'records':[{'input':4,'output':4}]}))
   q=FakeQueue();c=submit(d,q,[0,1],2,3)
   self.assertEqual(review(d,q,c['id'])['assessment'],'PENDING')
   q.jobs[0].update(status='completed',completed=3)
   self.assertEqual(review(d,q,c['id'])['assessment'],'INSUFFICIENT_LINKED_EVIDENCE')
 def test_invalid_cells(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):propose(d,[1,1])
if __name__=='__main__':unittest.main()
