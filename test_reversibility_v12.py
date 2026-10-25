import unittest
from reversibility_v12 import forward_reference,inverse_reference,investigate
class V12Tests(unittest.TestCase):
 def test_reference_inverse(self):
  for a in ([1],[1,2,3],[0,0xffffff,22]):self.assertEqual(inverse_reference(forward_reference(a)),a)
 def test_repeatable(self):
  state={'cells':[1,2,3],'tick':0}
  def capture():return {'cells':state['cells'][:],'tick':state['tick']}
  def restore(s):state.update(cells=s['cells'][:],tick=s['tick'])
  def step():state['cells']=forward_reference(state['cells']);state['tick']+=1
  r=investigate(capture,restore,step,4)
  self.assertTrue(r['serialized_repeatability']);self.assertTrue(r['final_restoration']);self.assertFalse(r['native_inverse_verified'])
 def test_hidden_state_detectable_by_nonrepeatability(self):
  state={'cells':[1,2],'tick':0}; hidden=[0]
  def capture():return dict(state,cells=state['cells'][:])
  def restore(s):state.update(cells=s['cells'][:],tick=s['tick'])
  def step():hidden[0]+=1;state['cells'][0]=hidden[0];state['tick']+=1
  self.assertFalse(investigate(capture,restore,step,2)['serialized_repeatability'])
if __name__=='__main__':unittest.main()
