import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.spa3d.geometry import build_model
from src.spa3d.render_guides import (
    SOLID_DOOR,
    WOOD,
    _camera_project,
    _iso,
    render_axonometric,
    render_interior,
)


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

    def test_axonometric_furniture_symbols_are_high_contrast(self):
        model = build_model()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "axon.png"
            render_axonometric(model, output)
            with Image.open(output) as image:
                for zone in ("male", "female"):
                    table = model[f"{zone}_table"]
                    table_center = tuple(round(value) for value in _iso(table.x, table.y, 740))
                    self.assertEqual(image.getpixel(table_center), (166, 151, 136))
                    for chair in model[f"{zone}_chairs"]:
                        chair_center = tuple(
                            round(value)
                            for value in _iso(
                                chair.x + chair.width / 2,
                                chair.y + chair.height / 2,
                                460,
                            )
                        )
                        self.assertEqual(image.getpixel(chair_center), (239, 236, 229))

    def test_interior_shows_open_solid_door_without_hiding_table(self):
        model = build_model()
        camera = (-900, 3290, 1600)
        target = (8800, 2700, 1200)
        door_points = (
            (4898, 2550, 0),
            (6378, 2550, 0),
            (6378, 2550, 2200),
            (4898, 2550, 2200),
        )
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "interior.png"
            render_interior(model, output)
            with Image.open(output) as image:
                door_center = tuple(
                    round(value)
                    for value in _camera_project(
                        (5638, 2550, 1100),
                        camera,
                        target,
                    )
                )
                table = model["male_table"]
                table_center = tuple(
                    round(value)
                    for value in _camera_project(
                        (table.x, table.y, 740),
                        camera,
                        target,
                    )
                )
                self.assertEqual(image.getpixel(door_center), SOLID_DOOR)
                self.assertEqual(image.getpixel(table_center), WOOD)
                projected_door = [
                    _camera_project(point, camera, target) for point in door_points
                ]
                screen_width = max(point[0] for point in projected_door) - min(
                    point[0] for point in projected_door
                )
                self.assertLess(screen_width, 80)


if __name__ == "__main__":
    unittest.main()
