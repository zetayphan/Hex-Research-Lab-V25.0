import unittest,random
from native_stage_v13 import report,forward,inverse,IDENTITY,POINTWISE,NEIGHBOR
class TestV13(unittest.TestCase):
 def test_all_stage_classified(self):
  r=report();self.assertEqual(len(r['stages']),17);self.assertEqual(r['proven_isolated'],11);self.assertEqual(r['unresolved'],6)
 def test_roundtrip(self):
  rng=random.Random(13)
  for n in (1,2,8,64):
   values=[rng.randrange(1<<24) for _ in range(n)]
   for stage in IDENTITY|POINTWISE:
    with self.subTest(n=n,stage=stage):self.assertEqual(inverse(stage,forward(stage,values)),values)
 def test_unresolved_not_assumed_invertible(self):
  for stage in NEIGHBOR:
   with self.assertRaises(ValueError):inverse(stage,[1,2,3])
if __name__=='__main__':unittest.main()
