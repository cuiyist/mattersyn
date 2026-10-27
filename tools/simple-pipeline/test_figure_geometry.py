"""Invented page geometry only; never open a PDF, render a crop or call a model."""
import importlib.util
from pathlib import Path
import re
import unittest
from unittest import mock

try:
    import pymupdf as fitz
except ImportError:
    import fitz

HERE = Path(__file__).resolve().parent
TARGET = HERE / 'mattersyn_simple.py'
spec = importlib.util.spec_from_file_location('private_geometry_only', TARGET)
simple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple)


def block(rect, text, number=0):
    return (*rect, text, number, 0)


def physical(rect, text, number=0):
    return {'type': 0, 'number': number, 'bbox': rect,
            'lines': [{'bbox': rect, 'spans': [{'text': text}]}]}


class Page:
    def __init__(self, blocks, images=(), physical_blocks=None, drawings=(), size=(600, 800)):
        self.rect = fitz.Rect(0, 0, *size)
        self.number = 0
        self.blocks = blocks
        self.images = images
        self.drawings = drawings
        self.physical = physical_blocks if physical_blocks is not None else [
            physical(b[:4], b[4], b[5]) for b in blocks]

    def get_text(self, kind):
        return self.blocks if kind == 'blocks' else {'blocks': self.physical}

    def get_image_info(self):
        return [{'bbox': r} for r in self.images]

    def get_drawings(self):
        return [{'rect': r} for r in self.drawings]


def found(page):
    document = mock.MagicMock()
    document.__enter__.return_value = [page]
    with mock.patch.object(fitz, 'open', return_value=document) as opening:
        result = list(simple.find_figures('NOT_A_REAL_INPUT'))
    opening.assert_called_once_with('NOT_A_REAL_INPUT')
    return result


class GeometryTests(unittest.TestCase):
    def test_saved_kti_numeric_geometry_recovers_five_distinct_regions(self):
        # Numeric diagnostics only. Text is invented and no paper is opened.
        pages = [
            ([(58.048, 564.264, 298.048, 729.264), (315.479, 465.984, 555.479, 729.264)],
             [172, 275],
             [(115.906, 734.120, 245.674, 743.585), (315.479, 734.120, 554.966, 743.585)], [1, 2]),
            ([(58.048, 602.064, 298.048, 729.264), (350.135, 87.680, 520.535, 501.440),
              (334.774, 578.464, 535.894, 729.264)],
             [500, 1386, 600],
             [(61.532, 734.120, 294.072, 743.585), (315.479, 506.297, 554.986, 535.726),
              (354.793, 734.120, 515.661, 743.585)], [3, 4, 5]),
        ]
        recovered = []
        for images, counts, caps, labels in pages:
            strips = []
            for r, count in zip(images, counts):
                x0, y0, x1, y1 = r
                strips.extend((x0, y0 + (y1 - y0) * n / count, x1, y0 + (y1 - y0) * (n + 1) / count)
                              for n in range(count))
            physicals = [physical(c, f'FIGURE {n}. Synthetic diffraction caption.', n) for c, n in zip(caps, labels)]
            if labels == [1, 2]:
                blocks = [block((115.906, 734.120, 554.966, 743.585),
                                '\n'.join(p['lines'][0]['spans'][0]['text'] for p in physicals))]
            else:
                blocks = [block(c, p['lines'][0]['spans'][0]['text']) for c, p in zip(caps, physicals)]
            result = found(Page(blocks, strips, physicals, size=(612, 792)))
            self.assertEqual([r[1] for r in result], ['Figure ' + str(n) for n in labels])
            for row, image in zip(result, images):
                self.assertEqual(tuple(round(v, 3) for v in row[3]),
                                 tuple(round(v, 3) for v in (image[0] - 4, image[1] - 4, image[2] + 4, image[3] + 4)))
            recovered.extend(result)
        self.assertEqual(len(recovered), 5)

    def test_saved_ni_numeric_side_geometries(self):
        for label, image, cap in (
            (1, (59.700, 428.180, 245.705, 618.140), (259.427, 585.126, 430.722, 603.293)),
            (2, (51.180, 67.940, 167.560, 184.220), (182.891, 67.180, 339.125, 76.327)),
            (3, (51.180, 459.380, 278.145, 616.700), (293.499, 554.965, 422.222, 592.294)),
        ):
            rows = found(Page([block(cap, f'Figure {label}. Synthetic diffraction caption.')], [image], size=(482, 680)))
            self.assertEqual([r[1] for r in rows], ['Figure ' + str(label)])
            self.assertEqual(tuple(round(v, 3) for v in rows[0][3]),
                             tuple(round(v, 3) for v in (image[0] - 4, image[1] - 4, image[2] + 4, image[3] + 4)))

    def test_contiguous_strips_coalesce_before_size_filter(self):
        strips = [fitz.Rect(40, 100 + n * .5, 240, 100 + (n + 1) * .5) for n in range(400)]
        groups = simple.coalesce_image_strips(strips)
        self.assertEqual([tuple(r) for r in groups], [(40.0, 100.0, 240.0, 300.0)])
        result = found(Page([block((40, 310, 250, 340), 'Figure 1. Synthetic TEM caption.')], strips))
        self.assertEqual([(x[0], x[1]) for x in result], [(1, 'Figure 1')])
        self.assertEqual(tuple(result[0][3]), (36.0, 96.0, 244.0, 304.0))

    def test_strip_gaps_and_different_columns_remain_separate(self):
        rects = [fitz.Rect(40, 10, 240, 11), fitz.Rect(40, 13, 240, 14),
                 fitz.Rect(300, 10, 500, 11), fitz.Rect(300, 11, 500, 12)]
        self.assertEqual(sorted(tuple(r) for r in simple.coalesce_image_strips(rects)),
                         [(40.0, 10.0, 240.0, 11.0), (40.0, 13.0, 240.0, 14.0),
                          (300.0, 10.0, 500.0, 12.0)])

    def test_normal_images_not_unioned_and_vectors_unchanged(self):
        rects = [fitz.Rect(40, 10, 240, 90), fitz.Rect(40, 90, 240, 170)]
        self.assertEqual([tuple(r) for r in simple.coalesce_image_strips(rects)], [tuple(r) for r in rects])
        result = found(Page([block((40, 310, 250, 340), 'Figure 1. Synthetic TEM caption.')],
                            drawings=[(40, 100, 240, 300)]))
        self.assertEqual(len(result), 1)

    def test_merged_api_block_preserves_two_physical_captions(self):
        a, b = (40, 300, 250, 330), (40, 600, 250, 630)
        text_a, text_b = 'Figure 1. Synthetic TEM example.', 'Figure 2. Synthetic XRD example.'
        page = Page([block((40, 300, 250, 630), text_a + '\n' + text_b)],
                    [(40, 100, 240, 280), (40, 400, 240, 580)],
                    [physical(a, text_a), physical(b, text_b, 1)])
        self.assertEqual([(x[:4], x[4]) for x in simple.figure_text_blocks(page)], [(a, text_a), (b, text_b)])
        self.assertEqual([x[1] for x in found(page)], ['Figure 1', 'Figure 2'])

    def test_single_physical_caption_does_not_split_body(self):
        original = block((40, 300, 250, 370), 'Figure 1. Synthetic TEM example.\nBody wording.')
        page = Page([original], physical_blocks=[physical((40, 300, 250, 330), original[4].splitlines()[0]),
                                                physical((40, 340, 250, 370), 'Body wording.', 1)])
        self.assertEqual(simple.figure_text_blocks(page), [original])

    def test_unique_close_left_image_with_vertical_overlap(self):
        page = Page([block((330, 140, 560, 200), 'Figure 3. Synthetic diffraction example.')],
                    [(100, 100, 315, 260)])
        result = found(page)
        self.assertEqual([x[1] for x in result], ['Figure 3'])
        self.assertEqual(tuple(result[0][3]), (96.0, 96.0, 319.0, 264.0))

    def test_left_match_rejects_gap_and_vertical_half_boundary(self):
        cap = fitz.Rect(330, 140, 560, 200)
        for image in ((100, 100, 311, 260), (100, 170, 315, 300), (340, 100, 550, 260)):
            self.assertIsNone(simple.left_caption_image(cap, [fitz.Rect(image)], 600))

    def test_ambiguous_left_images_rejected(self):
        cap = fitz.Rect(330, 140, 560, 240)
        images = [fitz.Rect(100, 100, 315, 220), fitz.Rect(100, 160, 315, 300)]
        self.assertIsNone(simple.left_caption_image(cap, images, 600))
        self.assertEqual(found(Page([block(tuple(cap), 'Figure 3. Synthetic diffraction example.')], images)), [])

    def test_original_half_graphic_coverage_and_minimum_size_still_hold(self):
        caption = block((10, 250, 250, 280), 'Figure 1. Synthetic TEM example.')
        self.assertEqual(found(Page([caption], [(-100, 100, 100, 200)])), [])
        self.assertEqual(found(Page([caption], [(30, 160, 70, 200)])), [])

    def test_inline_references_are_not_side_captions(self):
        for text in ('Figure 3 shows a synthetic plot.', 'Figure II Synthetic plot.'):
            self.assertEqual(found(Page([block((330, 140, 560, 200), text)], [(100, 100, 315, 260)])), [])



if __name__ == '__main__':
    unittest.main(verbosity=2)
