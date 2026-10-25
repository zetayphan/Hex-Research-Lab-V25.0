import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from controlled_v10 import trial
class TestControlled(unittest.TestCase):
 def test_repeated(self):
  s={'tick':0}
  def capture():return dict(s)
  def restore(f):s.update(f)
  def step():s['tick']+=1
  r=trial(capture,restore,step,3,5)
  self.assertTrue(r['repeatable']);self.assertTrue(r['restored_initial_state']);self.assertEqual(s['tick'],0)
 def test_reject(self):
  with self.assertRaises(ValueError):trial(lambda:{},lambda x:None,lambda:None,1,5)
if __name__=='__main__':unittest.main()
