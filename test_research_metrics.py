import unittest
from research_metrics import summarize_state
class ResearchTests(unittest.TestCase):
    def test_totals(self):
        s=summarize_state({'values':[0x010203,0x040506],'tick':7})
        self.assertEqual(s['rgb_totals'],[5,7,9]);self.assertEqual(s['distinct_hex_values'],2)
        self.assertEqual(s['adjacent_value_transitions'],1)
    def test_empty(self):
        self.assertEqual(summarize_state({'values':[]})['rgb_totals'],[0,0,0])
if __name__=='__main__':unittest.main()
