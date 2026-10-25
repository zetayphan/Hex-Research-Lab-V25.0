import unittest
from collision_v192 import analyze
class AlgebraicTests(unittest.TestCase):
    def test_xor_stage_exact(self):
        r=analyze(7,random_trials=0)
        self.assertIn(r['classification'],('INJECTIVE_PROVEN','NON_INJECTIVE_WITNESS'))
        self.assertTrue(r['proof_method'].startswith('exact_GF2'))
        if r['collision']: self.assertTrue(r['witness_verified'])
    def test_identity_proof(self):
        r=analyze(3,flags=0,random_trials=0)
        self.assertEqual(r['classification'],'INJECTIVE_PROVEN')
    def test_bounded_unresolved(self):
        r=analyze(0,random_trials=0)
        self.assertIn(r['classification'],('UNRESOLVED_NO_COLLISION_FOUND','NON_INJECTIVE_WITNESS'))
    def test_bad_inputs(self):
        with self.assertRaises(ValueError): analyze(2)
if __name__=='__main__': unittest.main()
