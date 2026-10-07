import importlib.util,unittest
from pathlib import Path
script=Path(__file__).resolve().parents[1]/'master_audio.py'
spec=importlib.util.spec_from_file_location('master_audio',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Contract(unittest.TestCase):
 def test_already_retimed_audio_not_sped_twice(self):
  self.assertEqual(m.tempo_ratio(1.15,1.15),1)
  self.assertAlmostEqual(m.tempo_ratio(1,1.15),1.15)
 def test_speed_validation(self):
  for x in [0,-1,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):m.tempo_ratio(x,1.15)
 def test_nonfinite_ratio_is_rejected(self):
  with self.assertRaises(ValueError):m.tempo_ratio(1e-320,1e300)
 def test_subtitle_times_text_and_bounds(self):
  s='1\n00:00:01,150 --> 00:00:02,300\n完全保留，Jun。\n'
  t=m.retime_srt(s,1.15)
  self.assertIn('00:00:01,000 --> 00:00:02,000',t);self.assertIn('完全保留，Jun。',t)
 def test_measurement_is_not_listening(self):
  self.assertEqual(m.completion_status(True,False),'technical_passed_listening_pending')
  self.assertEqual(m.completion_status(False,True),'technical_failed')
 def test_timestamp_in_caption_is_not_rewritten(self):
  s='1\n00:00:01,150 --> 00:00:02,300\n示例时间是00:01:00,000。\n'
  self.assertIn('示例时间是00:01:00,000。',m.retime_srt(s,1.15))
 def test_zero_duration_after_rounding_rejected(self):
  with self.assertRaises(ValueError):m.retime_srt('1\n00:00:00,000 --> 00:00:00,001\n字\n',10)
 def test_subtitles_beyond_picture_rejected(self):
  with self.assertRaises(ValueError):m.retime_srt('1\n00:00:01,000 --> 00:00:02,000\n字\n',1,duration=1)
if __name__=='__main__':unittest.main()
