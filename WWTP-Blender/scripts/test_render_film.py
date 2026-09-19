"""Run without Blender: python -B -m unittest discover -s scripts -p test_render_film.py."""
from itertools import groupby
from types import SimpleNamespace
import unittest

import render_film as film
from render_film_pipeline import verify_video


class FilmSelectionTests(unittest.TestCase):
    def args(self, **overrides):
        values = dict(qa=False, shot=None, start=1, end=6480, frame_step=1)
        return SimpleNamespace(**(values | overrides))

    def test_default_preserves_full_original_sequence(self):
        self.assertEqual(film.selected(self.args()), list(range(1, 6481)))

    def test_fast_profile_preserves_cuts_and_fills_output(self):
        args = self.args(frame_step=2)
        actual = film.selected(args)
        self.assertEqual(len(actual), 3257)
        self.assertEqual(film.output_frames(args), list(range(1, 6481)))
        for shot in film.D['shots']:
            self.assertIn(shot['start'], actual)
            self.assertIn(shot['end'], actual)
            frames = [f for f in actual if shot['start'] <= f <= shot['end']]
            self.assertTrue(all(0 < b-a <= 2 for a, b in zip(frames, frames[1:])))

    def test_resume_batches_do_not_render_completed_frames(self):
        args = self.args(frame_step=2)
        pending = [f for f in film.selected(args) if f % 11]
        rebuilt = []
        for shot in film.D['shots']:
            frames = [f for f in pending if shot['start'] <= f <= shot['end']]
            for _, group in groupby(enumerate(frames), lambda p: p[1]-p[0]*args.frame_step):
                batch = [f for _, f in group]
                rebuilt.extend(range(batch[0], batch[-1]+1, args.frame_step))
        self.assertEqual(rebuilt, pending)

    def test_cut_boundary_and_partial_interval(self):
        args = self.args(frame_step=2, start=429, end=436)
        self.assertEqual(film.selected(args), [429, 431, 432, 433, 435, 436])
        self.assertEqual(film.output_frames(args), list(range(429, 437)))

    def test_qa_keeps_34_preview_frames(self):
        args = self.args(qa=True, frame_step=2)
        self.assertEqual(len(film.selected(args)), 34)
        self.assertEqual(film.selected(args), film.output_frames(args))


class VideoValidationTests(unittest.TestCase):
    def info(self):
        return {'streams': [{'width': 1920, 'height': 1080, 'r_frame_rate': '24/1',
                             'nb_read_frames': '6480', 'codec_name': 'h264'}],
                'format': {'duration': '270.000000'}}

    def test_complete_video_passes(self):
        verify_video(self.info())

    def test_truncated_wrong_size_and_wrong_fps_fail(self):
        for field, value in [('width', 1280), ('r_frame_rate', '12/1'), ('nb_read_frames', '6479')]:
            info = self.info()
            info['streams'][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                verify_video(info)
        info = self.info()
        info['format']['duration'] = '269'
        with self.assertRaises(RuntimeError):
            verify_video(info)


if __name__ == '__main__':
    unittest.main()
