from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path, PureWindowsPath


ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT / "tmp" / "geometry" / "render_rooftop_whole_floor_truth_model_v05.py"
RENDERER_TEST_PATH = ROOT / "tmp" / "geometry" / "test_render_rooftop_whole_floor_truth_model_v05.py"
V04_SCENE_PATH = (
    ROOT
    / "output"
    / "空间真值"
    / "整层灰模"
    / "候选_v04_20261010"
    / "楼顶整层灰模_v04_坐标场景.json"
)
V05_SCENE_PATH = (
    ROOT
    / "output"
    / "空间真值"
    / "整层灰模"
    / "候选_v05_20261011"
    / "楼顶整层灰模_v05_坐标场景.json"
)
EXPECTED_AUTHORITY_PATHS = [
    "output/现场复尺审阅/20261008_逐项确认/现场复尺已确认真值_20261009.md",
    "output/空间真值/天花设计控制/楼顶两级吊顶业主确认_20261009.md",
]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("relocated_rooftop_v05", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RooftopPortabilityTests(unittest.TestCase):
    def test_historical_v04_scene_is_repository_portable(self) -> None:
        self.assertTrue(V04_SCENE_PATH.is_file(), "v01 rebuild input must be versioned")

        scene = json.loads(V04_SCENE_PATH.read_text(encoding="utf-8"))
        absolute_authorities = [
            entry for entry in scene["authority"] if PureWindowsPath(entry).is_absolute()
        ]

        self.assertEqual(absolute_authorities, [])

    def test_current_v05_generator_and_scene_use_repository_relative_authorities(self) -> None:
        renderer = load_module(RENDERER_PATH)
        scenes = {
            "generator": renderer.scene_spec(),
            "archived": json.loads(V05_SCENE_PATH.read_text(encoding="utf-8")),
        }

        for source, scene in scenes.items():
            with self.subTest(source=source):
                self.assertEqual(scene["authority"][:2], EXPECTED_AUTHORITY_PATHS)
                self.assertFalse(
                    any(PureWindowsPath(entry).is_absolute() for entry in scene["authority"])
                )

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

    def test_v05_non_destructive_check_uses_a_temporary_sentinel(self) -> None:
        source = RENDERER_TEST_PATH.read_text(encoding="utf-8")

        self.assertNotIn("候选_v03_20261009", source)
        self.assertIn("TemporaryDirectory", source)
        self.assertIn("sentinel", source)


if __name__ == "__main__":
    unittest.main()
