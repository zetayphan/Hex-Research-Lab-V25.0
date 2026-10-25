import unittest,tempfile,json
from pathlib import Path
from hypothesis_v7 import evaluate
class HypothesisTests(unittest.TestCase):
 def test_holdout_counterexample(self):
  with tempfile.TemporaryDirectory() as d:
   for name,err in [('train',0),('test',2)]:
    rows=[{'index':0,'distinct_hex_values':2,'adjacent_value_transitions':3,'adjacent_rgb_gradient':4},{'index':1,'prediction_error_l1':err,'distinct_hex_values':2,'adjacent_value_transitions':3,'adjacent_rgb_gradient':4,'delta_structure':{'distinct':0,'transitions':0,'gradient':0}}]
    (Path(d)/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
   out=evaluate(d,['train','test']);self.assertEqual(out['hypotheses'][0]['counterexamples'],1)
 def test_requires_holdout(self):
  with self.assertRaises(ValueError):evaluate('.', ['one'])
if __name__=='__main__':unittest.main()
