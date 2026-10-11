import importlib.util, pathlib, unittest
HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('caption_fix',HERE/'mattersyn_simple.py'); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Page:
 def __init__(self,text,label='Figure 1',x=10,y=10,labels=1):
  self.block=(10,10,200,100,text,0,0)
  self.d={'blocks':[{'type':0,'bbox':self.block[:4],'lines':[{'bbox':(x,y,x+40,y+10),'spans':[{'text':label}]}]*labels}]}
 def get_text(self,kind):return [self.block] if kind=='blocks' else self.d
class CaptionDetection(unittest.TestCase):
 def test_uppercase_plain_label(self):self.assertIsNotNone(module.CAPTION_PLAIN.match('FIGURE 1 Example synthetic display.'))
 def test_mixedcase_plain_label(self):self.assertIsNotNone(module.CAPTION_PLAIN.match('Figure 1 Example synthetic display.'))
 def test_lowercase_body_guard(self):self.assertIsNone(module.CAPTION_PLAIN.match('FIGURE 1 shows an example.'))
 def test_uppercase_roman_body_guard(self):self.assertIsNone(module.CAPTION_PLAIN.match('Figure II Example.'))
 def test_punctuated_unchanged(self):self.assertIsNotNone(module.CAPTION.match('FIGURE 1. Example.'))
 def test_top_left_reorders(self):self.assertTrue(module.figure_text_blocks(Page('Synthetic title\nFigure 1\nSynthetic caption.'))[0][4].startswith('Figure 1\n'))
 def test_geometry_preserved(self):
  page=Page('Synthetic title\nFigure 1\nSynthetic caption.');self.assertEqual(module.figure_text_blocks(page)[0][:4],page.block[:4])
 def test_text_lines_preserved(self):
  page=Page('Synthetic title\nFigure 1\nSynthetic caption.');self.assertEqual(sorted(module.figure_text_blocks(page)[0][4].splitlines()),sorted(page.block[4].splitlines()))
 def test_mid_block_label_rejected(self):
  page=Page('Synthetic body\nFigure 1\nSynthetic body.',y=50);self.assertEqual(module.figure_text_blocks(page)[0],page.block)
 def test_right_edge_label_rejected(self):
  page=Page('Synthetic body\nFigure 1\nSynthetic body.',x=80);self.assertEqual(module.figure_text_blocks(page)[0],page.block)
 def test_multiple_geometry_labels_rejected(self):
  page=Page('Synthetic title\nFigure 1\nSynthetic caption.',labels=2);self.assertEqual(module.figure_text_blocks(page)[0],page.block)
 def test_already_ordered_unchanged(self):
  page=Page('Figure 1\nSynthetic title\nSynthetic caption.');self.assertEqual(module.figure_text_blocks(page)[0],page.block)
 def test_repeated_text_label_rejected(self):
  page=Page('Synthetic title\nFigure 1\nSynthetic caption.\nFigure 1');self.assertEqual(module.figure_text_blocks(page)[0],page.block)
 def test_two_lines_only_rejected(self):
  page=Page('Synthetic title\nFigure 1');self.assertEqual(module.figure_text_blocks(page)[0],page.block)
if __name__=='__main__':unittest.main()
