from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT / "tmp" / "geometry" / "render_rooftop_whole_floor_truth_model_v05.py"
RENDERER_TEST_PATH = ROOT / "tmp" / "geometry" / "test_render_rooftop_whole_floor_truth_model_v05.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("relocated_rooftop_v05", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RooftopPortabilityTests(unittest.TestCase):
    def test_v05_files_do_not_embed_the_owner_workstation_path(self) -> None:
        for path in (RENDERER_PATH, RENDERER_TEST_PATH):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn(r"C:\Users\SkryPD", source)
                self.assertIn("Path(__file__).resolve().parents[2]", source)

    def test_renderer_root_follows_a_relocated_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_root = Path(temporary_directory) / "relocated-project"
            relocated = fake_root / "tmp" / "geometry" / RENDERER_PATH.name
            relocated.parent.mkdir(parents=True)
            relocated.write_text(RENDERER_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            module = load_module(relocated)

            self.assertEqual(module.ROOT, fake_root)


if __name__ == "__main__":
    unittest.main()
