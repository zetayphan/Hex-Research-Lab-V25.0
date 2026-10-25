import tempfile,unittest
from pathlib import Path
from threading import RLock
from autonomous_v4 import Recorder
class RecorderTests(unittest.TestCase):
 def test_record_and_reload(self):
  with tempfile.TemporaryDirectory() as t:
   def snap():return {'values':[0x112233,0x112234],'tick':3,'cell_count':2}
   r=Recorder(Path(t)/'research_data'/'observations.jsonl',snap,RLock())
   r.sample_once();self.assertEqual(len(r.history()),1)
   self.assertEqual(r.history()[0]['tick'],3)
   self.assertEqual(len(Recorder(r.path,snap,RLock()).history()),1)
 def test_configuration(self):
  with tempfile.TemporaryDirectory() as t:
   r=Recorder(Path(t)/'r.jsonl',lambda:{},RLock())
   self.assertTrue(r.configure(True,1)['enabled'])
   self.assertEqual(r.configure(False,3)['sample_seconds'],3)
if __name__=='__main__':unittest.main()
