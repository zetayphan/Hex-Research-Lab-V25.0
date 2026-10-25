import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from report_v203 import build
class ReportTests(unittest.TestCase):
 def test_report_and_comparison(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'research_data/v202/playback';folder.mkdir(parents=True)
   a='a'*32;b='b'*32
   for rid,out in [(a,'000002'),(b,'000003')]:
    (folder/(rid+'.json')).write_text(json.dumps({'schema':'hex-v20.2-stage-playback','tick':1,'cells':[{'cell':0,'records':[{'stage':1,'input':'000001','output':out,'expression':'ADD'}]}]}))
   report=build(tmp,a,b)
   self.assertEqual(len(report['comparisons']),1)
   self.assertFalse(report['comparisons'][0]['match'])
   self.assertIn('RGB conservation cannot be established',report['markdown'])
 def test_invalid_id(self):
  with self.assertRaises(ValueError):build('/tmp','../bad')
if __name__=='__main__':unittest.main()
