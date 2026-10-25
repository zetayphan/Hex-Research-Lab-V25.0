import unittest, tempfile, pathlib, json, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from v232_linking import link_job_evidence
from v231_cycle import review
class LinkTests(unittest.TestCase):
 def test_link_and_assess(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);rid='a'*32;jobid='b'*32;eid='c'*32;cid='d'*32
   folder=root/'research_data/v202/playback';folder.mkdir(parents=True)
   (folder/(rid+'.json')).write_text(json.dumps({'id':rid,'cells':[{'records':[{'input':1,'output':1},{'input':2,'output':3}]}]}))
   link_job_evidence(root,jobid,{'id':eid,'playback_runs':[rid]})
   self.assertEqual(json.loads((folder/(rid+'.json')).read_text())['job_id'],jobid)
   cycles=root/'research_data/v231/cycles';cycles.mkdir(parents=True)
   (cycles/(cid+'.json')).write_text(json.dumps({'job_id':jobid,'plan':{'discovery_run':'z'*32}}))
   reports=root/'research_data/v21/reports';reports.mkdir(parents=True)
   (reports/(eid+'.json')).write_text(json.dumps({'id':eid,'playback_runs':[rid]}))
   class Q:
    def list(self):return [{'id':jobid,'status':'completed','completed':1,'repetitions':1,'results':[{'experiment_id':eid}]}]
   r=review(root,Q(),cid)
   self.assertEqual((r['assessment'],r['tested_records'],r['counterexamples']),('CONTRADICTED',2,1))
