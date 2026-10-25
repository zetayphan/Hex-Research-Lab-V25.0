import unittest,tempfile,json
from pathlib import Path
from design_v9 import plan,compare
class DesignV9Tests(unittest.TestCase):
 def test_plan_deterministic_and_bounded(self):
  self.assertEqual(plan()['plan_sha256'],plan()['plan_sha256'])
  with self.assertRaises(ValueError):plan(replicates=1)
 def test_compare_runs(self):
  with tempfile.TemporaryDirectory() as tmp:
   for rid,errors in [('one',[0,0]),('two',[0,2])]:
    with (Path(tmp)/(rid+'.jsonl')).open('w') as f:
     for i,e in enumerate([None]+errors):f.write(json.dumps({'index':i,'prediction_error_l1':e,'delta_structure':{'distinct':1,'transitions':0,'gradient':0}})+'\n')
   r=compare(tmp,['one','two'])
   self.assertEqual(r['conservation_fraction_range'],[0.5,1.0])
   self.assertTrue(r['step_counts_matched'])
 def test_duplicate_runs_rejected(self):
  with self.assertRaises(ValueError):compare('.',['x','x'])
if __name__=='__main__':unittest.main()
