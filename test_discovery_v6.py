import unittest,tempfile,json
from pathlib import Path
from discovery_v6 import analyze,compare
class DiscoveryTests(unittest.TestCase):
 def test_patterns(self):
  rows=[{'index':i,'distinct_hex_values':i%2,'adjacent_value_transitions':i,'adjacent_rgb_gradient':1,'prediction_error_l1':i%2} for i in range(4)]
  result=analyze(rows);self.assertEqual(result['steps'],3);self.assertTrue(any(f['status']=='counterexamples observed' for f in result['findings']))
 def test_compare_and_reject_path(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run1.jsonl';p.write_text(json.dumps({'index':0})+'\n');self.assertEqual(compare(d,['run1'])['runs'][0]['samples'],1)
   with self.assertRaises(ValueError):compare(d,['../bad'])
 def test_empty(self):self.assertEqual(analyze([])['samples'],0)
if __name__=='__main__':unittest.main()
