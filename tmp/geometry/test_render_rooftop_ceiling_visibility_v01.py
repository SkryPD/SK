from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tmp" / "geometry" / "render_rooftop_ceiling_visibility_v01.py"


def load_module():
    assert MODULE_PATH.exists(), "ceiling visibility renderer has not been implemented"
    spec = importlib.util.spec_from_file_location("rooftop_ceiling_visibility_v01", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_is_derived_from_v05_truth_scene() -> None:
    module = load_module()
    source = module.load_source_scene()

    assert source["version"] == "rooftop-whole-floor-truth-model-v05"
    assert module.ceiling_contract(source) == {
        "bounds_mm": [34240, 6160, 37440, 10260],
        "ceiling_z_mm": 2450,
        "window_z_range_mm": [350, 2450],
        "head_wall_z_range_mm": [2450, 3020],
    }


def test_outputs_are_versioned_decodable_and_visually_nonblank() -> None:
    module = load_module()
    module.render_all()

    assert module.OUT_DIR.name == "封顶可视化_候选_v01_20261011"
    for path in (module.OPAQUE_OUT, module.CUTAWAY_OUT):
        assert path.exists()
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.mode == "RGB"
            assert image.size == (2400, 1500)
            extrema = ImageStat.Stat(image).extrema
            assert any(high - low > 80 for low, high in extrema)

    report = module.REPORT_OUT.read_text(encoding="utf-8")
    for expected in (
        "rooftop-whole-floor-truth-model-v05",
        "2450",
        "570",
        "3020",
        "不得用于施工放样",
    ):
        assert expected in report


if __name__ == "__main__":
    test_contract_is_derived_from_v05_truth_scene()
    test_outputs_are_versioned_decodable_and_visually_nonblank()
    print("PASS")
