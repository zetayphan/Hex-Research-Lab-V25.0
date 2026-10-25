import unittest
from verification_engine import reference_cycle,rank_demonstration,matrix_rank,compare_snapshots
class VerificationV3Tests(unittest.TestCase):
 def test_cycle(self):self.assertTrue(reference_cycle()['pass']);self.assertTrue(reference_cycle()['inverse_pass'])
 def test_rank(self):self.assertTrue(rank_demonstration()['rank_expands'])
 def test_rank_dependent(self):self.assertEqual(matrix_rank([[1,2],[2,4]]),1)
 def test_observation(self):
  a={'values':[0x010203,0x030201],'tick':0};b={'values':[0x030201,0x010203],'tick':1}
  x=compare_snapshots(a,b);self.assertTrue(x['rgb_conserved']);self.assertEqual(x['changed_cells'],2)
if __name__=='__main__':unittest.main()
