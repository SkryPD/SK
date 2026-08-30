import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.spa3d.geometry import build_model
from src.spa3d.render_guides import render_axonometric, render_interior


class SpaGuideTests(unittest.TestCase):
    def test_revised_guides_render_from_one_model(self):
        model = build_model()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            axon = folder / "spa-bright-natural-axonometric-guide.png"
            interior = folder / "spa-bright-natural-interior-guide.png"
            render_axonometric(model, axon)
            render_interior(model, interior)
            for path in (axon, interior):
                self.assertTrue(path.exists())
                with Image.open(path) as image:
                    self.assertEqual(image.size, (2048, 1152))
                    self.assertEqual(image.mode, "RGB")

    def test_revised_guides_differ_from_blank_canvas(self):
        model = build_model()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            outputs = (folder / "axon.png", folder / "interior.png")
            render_axonometric(model, outputs[0])
            render_interior(model, outputs[1])
            for path in outputs:
                with Image.open(path) as image:
                    colors = image.getcolors(maxcolors=image.width * image.height)
                    self.assertIsNotNone(colors)
                    self.assertGreater(len(colors), 8)


if __name__ == "__main__":
    unittest.main()
