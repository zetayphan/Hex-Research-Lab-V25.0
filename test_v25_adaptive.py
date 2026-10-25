import unittest,tempfile,pathlib,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from v25_adaptive import strategies,queue_strategy
class TestAdaptive(unittest.TestCase):
 def test_empty(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(strategies(d)['status'],'NO_EVIDENCE')
 def test_rank(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'research_data/v202/playback';p.mkdir(parents=True)
   (p/'a.json').write_text(json.dumps({'records':[{'input':'000001','output':'000001'}]}))
   (p/'b.json').write_text(json.dumps({'records':[{'input':'000001','output':'000002'}]}))
   out=strategies(d);self.assertEqual(out['runs'],2);self.assertEqual(len(out['strategies']),4)
   self.assertEqual(out['strategies'][0]['score'],1)
 def test_invalid_hypothesis(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):queue_strategy(d,None,{'hypothesis':'unknown'})
if __name__=='__main__':unittest.main()
