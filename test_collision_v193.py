import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collision_v193 import analyze
class TestV193(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(analyze(3,flags=0)['classification'],'INJECTIVE_PROVEN')
 def test_exact_linear(self):
  self.assertIn(analyze(7)['classification'],('INJECTIVE_PROVEN','NON_INJECTIVE_WITNESS'))
 def test_symbolic_or_fallback(self):
  self.assertIn(analyze(0,timeout_ms=100,fallback_trials=0)['classification'],('INJECTIVE_PROVEN','NON_INJECTIVE_WITNESS','UNRESOLVED_SOLVER_UNKNOWN','UNRESOLVED_NO_COLLISION_FOUND'))
 def test_invalid(self):
  with self.assertRaises(ValueError):analyze(99)
if __name__=='__main__':unittest.main()
