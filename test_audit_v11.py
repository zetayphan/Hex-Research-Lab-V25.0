import unittest
from audit_v11 import audit
class AuditTests(unittest.TestCase):
 def test_conservation_recurrence_and_restore(self):
  state={'cells':[0x010203,0x040506],'tick':0}
  def capture():return {'cells':list(state['cells']),'tick':state['tick']%2}
  def restore(x):state.update(cells=list(x['cells']),tick=x['tick'])
  def step():state['cells'].reverse();state['tick']+=1
  result=audit(capture,restore,step,4)
  self.assertEqual(result['conserved_steps'],4)
  self.assertTrue(result['restored'])
  self.assertEqual(result['recurrence']['period'],2)
 def test_nonconservation(self):
  s={'cells':[0],'tick':0}
  def capture():return dict(s,cells=list(s['cells']))
  def restore(x):s.update(x)
  def step():s['cells']=[s['cells'][0]+1];s['tick']+=1
  self.assertEqual(audit(capture,restore,step,2)['nonconserved_steps'],2)
if __name__=='__main__':unittest.main()
