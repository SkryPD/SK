import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.spa3d.contact_sheet import build_contact_sheet


class SpaContactSheetTests(unittest.TestCase):
    def test_two_landscape_images_are_fitted_without_stretching(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            left = folder / "left.png"
            right = folder / "right.png"
            output = folder / "contact.png"
            Image.new("RGB", (1600, 900), (180, 190, 200)).save(left)
            Image.new("RGB", (2048, 1152), (210, 205, 195)).save(right)
            build_contact_sheet(left, right, output, "轴测", "室内")
            with Image.open(output) as image:
                self.assertEqual(image.mode, "RGB")
                self.assertEqual(image.size, (2000, 667))


if __name__ == "__main__":
    unittest.main()
