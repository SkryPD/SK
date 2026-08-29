import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.spa3d.geometry import build_model
from src.spa3d.render_guides import render_axonometric, render_interior


class SpaGuideTests(unittest.TestCase):
    def test_both_guides_render_from_one_model(self):
        model = build_model()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            axon = folder / "axon.png"
            interior = folder / "interior.png"
            render_axonometric(model, axon)
            render_interior(model, interior)
            for path in (axon, interior):
                self.assertTrue(path.exists())
                with Image.open(path) as image:
                    self.assertEqual(image.size, (2048, 1152))
                    self.assertEqual(image.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
