import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_v8 import report,markdown
class ResearchV8Tests(unittest.TestCase):
 def test_counterexample_and_provenance(self):
  with tempfile.TemporaryDirectory() as d:
   base={'index':0,'distinct_hex_values':1,'adjacent_value_transitions':2,'adjacent_rgb_gradient':3}
   def record(i,error):return {**base,'index':i,'prediction_error_l1':error,'delta_structure':{'distinct':0,'transitions':0,'gradient':0}}
   for name,err in [('train',0),('test',2)]:
    (Path(d)/(name+'.jsonl')).write_text('\n'.join(json.dumps(x) for x in [base,record(1,err)])+'\n')
   r=report(d,['train','test']);self.assertEqual(len(r['sources']),2)
   self.assertEqual(len(r['sources'][0]['sha256']),64)
   h=next(x for x in r['hypotheses'] if x['hypothesis']=='RGB total conservation')
   self.assertEqual(h['counterexamples'],1)
   self.assertIn('contradicted',h['assessment']);self.assertIn('SHA-256',markdown(r))
 def test_requires_independent_run(self):
  with self.assertRaises(ValueError):report('.', ['only'])
if __name__=='__main__':unittest.main()
