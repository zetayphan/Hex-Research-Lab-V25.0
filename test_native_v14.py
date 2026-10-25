import unittest,sys,pathlib,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from native_v14 import forward,inverse_with_known_neighbors,report
class NativeV14Tests(unittest.TestCase):
 def test_conditional_recovery(self):
  rng=random.Random(14)
  for n in (2,3,8):
   a=[rng.randrange(1<<24) for _ in range(n**3)]
   for s in (0,3,4,7,10,11):
    for flags in (0,1):
     self.assertEqual(inverse_with_known_neighbors(s,forward(s,a,n,flags),a,n,flags),a)
 def test_no_global_claim(self):
  r=report();self.assertFalse(r['global_inverse_verified']);self.assertEqual(len(r['stages']),6)
 def test_invalid_stage(self):
  with self.assertRaises(ValueError):forward(1,[0]*8,2)
if __name__=='__main__':unittest.main()
