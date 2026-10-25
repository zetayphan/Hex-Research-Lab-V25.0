import sys,unittest,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experimental_v5 import ExperimentRunner
class Tests(unittest.TestCase):
 def test_real_measurements_and_prediction_failures(self):
  with tempfile.TemporaryDirectory() as d:
   state={'tick':0,'values':[0x010203,0x040506]}
   def snap():return dict(state)
   def step():state['tick']+=1;state['values']=[v+1 for v in state['values']]
   r=ExperimentRunner(d,snap,step,__import__('threading').RLock(),lambda:False,lambda _:None)
   r.start(3,0);r.thread.join(5)
   self.assertEqual(r.status()['state'],'completed')
   result=r.results();self.assertEqual(result['summary']['steps_returned'],3)
   self.assertEqual(result['summary']['rgb_changed_steps'],3)
   self.assertEqual(result['records'][-1]['tick'],3)
 def test_limits(self):
  with tempfile.TemporaryDirectory() as d:
   r=ExperimentRunner(d,lambda:{},lambda:None,__import__('threading').RLock(),lambda:False,lambda _:None)
   with self.assertRaises(ValueError):r.start(10001)
   with self.assertRaises(ValueError):r.start(2,-1)
if __name__=='__main__':unittest.main()
