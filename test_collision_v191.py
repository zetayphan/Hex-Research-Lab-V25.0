import unittest
from collision_v191 import investigate
from native_v14 import forward
class CollisionTests(unittest.TestCase):
 def test_witness_if_present(self):
  for stage in (0,3,4,7,10,11):
   r=investigate(stage,random_trials=0)
   if r['collision']:
    w=r['collision'];a=[int(x,16) for x in w['input_a']];b=[int(x,16) for x in w['input_b']]
    self.assertNotEqual(a,b)
    self.assertEqual(forward(stage,a,2),forward(stage,b,2))
 def test_no_witness_is_unresolved(self):
  r=investigate(0,alphabet=[0],random_trials=0)
  self.assertEqual(r['classification'],'UNRESOLVED_NO_COLLISION_FOUND')
 def test_reject_bad_inputs(self):
  with self.assertRaises(ValueError):investigate(1)
  with self.assertRaises(ValueError):investigate(0,random_trials=100001)
