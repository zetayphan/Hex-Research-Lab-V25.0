import sys, pathlib, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from v5_features import transform,metrics
class V5MathTests(unittest.TestCase):
 def test_xor(self):self.assertEqual(transform(0xABCDEF,'xor',0xFFFFFF),0x543210)
 def test_add_wrap(self):self.assertEqual(transform(0xFFFFFF,'add',1),0)
 def test_and_or(self):
  self.assertEqual(transform(0xABCD00,'and',0xFF),0)
  self.assertEqual(transform(0xABCD00,'or',0xFF),0xABCDFF)
 def test_rotate(self):
  self.assertEqual(transform(0x800000,'rol',1),1)
  self.assertEqual(transform(0x123456,'rol',24),0x123456)
 def test_metrics(self):
  x=metrics([0,255],[255,255]);self.assertEqual(x['changed'],1);self.assertEqual(x['changed_bits'],8)
 def test_invalid(self):
  with self.assertRaises(ValueError):transform(0,'nope',1)
  with self.assertRaises(ValueError):metrics([1],[1,2])
if __name__=='__main__':unittest.main()
