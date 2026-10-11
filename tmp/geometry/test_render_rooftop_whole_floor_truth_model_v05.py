from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tmp" / "geometry" / "render_rooftop_whole_floor_truth_model_v05.py"


def load_module():
    assert MODULE_PATH.exists(), "v05 whole-floor renderer has not been implemented"
    spec = importlib.util.spec_from_file_location("whole_floor_truth_model_v05", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def objects_by_id(scene: dict) -> dict[str, dict]:
    return {item["id"]: item for item in scene["objects"]}


def test_v05_preserves_confirmed_tea_room_topology() -> None:
    module = load_module()
    scene = module.scene_spec()
    objects = objects_by_id(scene)

    assert scene["version"] == "rooftop-whole-floor-truth-model-v05"
    assert scene["tea_room_topology"] == {
        "confirmation_artifact": "34_茶室墙体拓扑_照片方向俯视确认_v02.png",
        "confirmed_on": "2026-10-10",
        "points_mm": {
            "A": [31240, 6160],
            "C": [34240, 6160],
            "B": [37440, 6160],
            "D": [37440, 10260],
            "E": [34240, 10260],
        },
        "photo_red_circle_point": "C",
        "collinear_sequence": ["A", "C", "B"],
        "open_passage_segment": ["A", "C"],
        "shared_wall_segment": ["C", "B"],
        "window_wall_segment": ["C", "E"],
        "background_wall_segment": ["B", "D"],
        "parallel_walls": [["C", "E"], ["B", "D"]],
        "terrace_boundary_segment": ["E", "D"],
        "extra_transition_band": False,
        "extra_inner_wall": False,
    }

    assert objects["tea_room_floor"]["bounds_mm"] == [34240, 6160, 37440, 10260]
    assert objects["tea_room_floor"]["dimensions_mm"] == [3200, 4100]
    assert objects["tea_open_passage"]["bounds_mm"] == [31240, 6060, 34240, 6260]
    assert objects["tea_open_passage"]["dimensions_mm"] == [3000, 2700]
    assert objects["tea_bar_shared_wall"]["bounds_mm"] == [34240, 6160, 37440, 6360]
    assert objects["tea_bar_shared_wall"]["dimensions_mm"] == [3200, 200]
    assert objects["tea_window_wall_north_jamb"]["bounds_mm"] == [34240, 6160, 34440, 6600]
    assert objects["tea_window_wall_south_jamb"]["bounds_mm"] == [34240, 9820, 34440, 10260]
    assert objects["tea_background_wall"]["bounds_mm"] == [37320, 6160, 37440, 10260]
    assert objects["tea_terrace_boundary_wall"]["bounds_mm"] == [34240, 10140, 37440, 10260]

    serialized = json.dumps(scene, ensure_ascii=False)
    assert "4100×4120" not in serialized
    assert "PDF 4120 room depth retained" not in serialized
    assert "900 mm strip" not in serialized


def test_east_end_restores_6160_baseline_and_shifts_bar_as_one_group() -> None:
    module = load_module()
    scene = module.scene_spec()
    objects = objects_by_id(scene)

    assert scene["global_control_mm"]["east_end_baseline_y"] == 6160
    assert scene["global_control_mm"]["superseded_east_end_baseline_y"] == 5040
    assert scene["global_control_mm"]["east_end_translation_y"] == 1120

    assert objects["main_hall_floor"]["bounds_mm"] == [18390, 0, 31240, 6160]
    assert objects["east_transition_floor"]["bounds_mm"] == [31240, 0, 34240, 6160]
    assert objects["south_mountain_terrace_band"]["bounds_mm"] == [18460, 6160, 34240, 10260]

    assert objects["bar_operation_zone"]["bounds_mm"] == [35040, 1130, 37440, 6160]
    assert objects["bar_body"]["bounds_mm"] == [35040, 1130, 35840, 6160]
    assert objects["equipment_run"]["bounds_mm"] == [36840, 1760, 37440, 6160]
    assert objects["equipment_rack"]["bounds_mm"] == [36640, 5160, 37440, 6160]
    assert objects["equipment_background_wall"]["bounds_mm"] == [37440, 1130, 37640, 6160]

    assert objects["bar_body"]["dimensions_mm"] == [800, 5030, 1000]
    assert objects["equipment_run"]["dimensions_mm"] == [600, 4400]
    assert objects["equipment_rack"]["dimensions_mm"] == [800, 1000]


def test_column_chain_uses_confirmed_c_wall_anchor() -> None:
    module = load_module()
    scene = module.scene_spec()
    objects = objects_by_id(scene)

    assert scene["open_facade_control_mm"] == {
        "direction": "tea_room_end_to_west_end",
        "fixed_wall_to_c1": 3200,
        "column_width_along_row": 105,
        "column_depth_indoor_to_terrace": 150,
        "clear_bays": [3130, 4170, 3960],
        "four_column_chain": 11680,
        "fixed_wall_to_c4_west_face": 14880,
    }
    assert [objects[f"steel_column_c{i}"]["bounds_mm"] for i in range(1, 5)] == [
        [30935, 6085, 31040, 6235],
        [27700, 6085, 27805, 6235],
        [23425, 6085, 23530, 6235],
        [19360, 6085, 19465, 6235],
    ]


def test_owner_confirmed_infill_closes_window_at_2450_ceiling() -> None:
    module = load_module()
    scene = module.scene_spec()
    objects = objects_by_id(scene)

    window = objects["tea_room_only_window"]
    assert window["bounds_mm"] == [34240, 6600, 34440, 9820]
    assert window["dimensions_mm"] == [3220, 2100]
    assert window["height_mm"] == 2100
    assert window["z_mm"] == 350
    assert window["sill_height_mm"] == 350
    assert window["head_height_mm"] == 2450
    assert window["top_to_eave_underside_mm"] == 570
    assert window["plan_offset_status"] == "requires_site_measurement"

    sill_wall = objects["tea_window_sill_wall"]
    assert sill_wall["plan_offset_status"] == "requires_site_measurement"

    head_wall = objects["tea_window_head_wall"]
    assert head_wall["bounds_mm"] == [34240, 6600, 34440, 9820]
    assert head_wall["dimensions_mm"] == [200, 3220]
    assert head_wall["z_mm"] == 2450
    assert head_wall["height_mm"] == 570
    assert head_wall["z_max_mm"] == 3020
    assert head_wall["resolved_infill_mm"] == 300
    assert head_wall["plan_offset_status"] == "requires_site_measurement"

    assert scene["floor_levels_mm"] == {
        "public_interior": 0,
        "tea_room": 0,
        "terrace": 0,
    }
    assert scene["ceiling_controls_mm"]["level_1_tea_room"] == {
        "height": 2450,
        "coverage": "complete_tea_room_v05_topology",
        "plan_extent_mm": [3200, 4100],
    }
    assert objects["ceiling_level_1_tea_room"]["bounds_mm"] == [34240, 6160, 37440, 10260]

    assert scene["design_clashes"] == []
    resolution = scene["resolved_design_decisions"][0]
    assert resolution == {
        "id": "tea_window_head_vs_ceiling",
        "confirmed_on": "2026-10-11",
        "status": "owner_confirmed_resolved",
        "former_window_head_mm": 2750,
        "former_overlap_mm": 300,
        "finished_ceiling_mm": 2450,
        "new_window_head_mm": 2450,
        "new_window_opening_height_mm": 2100,
        "upper_infill_z_range_mm": [2450, 3020],
        "resolution": "extend_upper_wall_down_to_finished_ceiling",
    }


def test_v05_render_outputs_are_decodable_versioned_and_non_destructive() -> None:
    module = load_module()
    with TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory)
        previous_candidate = output_root / "existing-candidate"
        previous_candidate.mkdir()
        sentinel = previous_candidate / "preserve-me.txt"
        sentinel.write_text("historical output", encoding="utf-8")

        module.OUT_DIR = output_root / "候选_v05_20261011"
        module.PLAN_OUT = module.OUT_DIR / "01_整层俯视空间控制图_v05.png"
        module.ISO_OUT = module.OUT_DIR / "02_整层去顶轴测灰模_v05.png"
        module.CEILING_OUT = module.OUT_DIR / "03_茶室窗洞封顶剖示_v05.png"
        module.SCENE_JSON = module.OUT_DIR / "楼顶整层灰模_v05_坐标场景.json"
        module.SURVEY_OUT = module.OUT_DIR / "楼顶整层灰模_v05_待复尺清单.md"
        module.REPORT_OUT = module.OUT_DIR / "楼顶整层灰模_v05_候选核验报告.md"

        module.render_all()

        assert "候选_v05_20261011" in str(module.OUT_DIR)
        for path in [module.PLAN_OUT, module.ISO_OUT, module.CEILING_OUT]:
            assert path.exists()
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                assert image.format == "PNG"
                assert image.mode == "RGB"
                assert image.width >= 1800
                assert image.height >= 1000

        scene = json.loads(module.SCENE_JSON.read_text(encoding="utf-8"))
        assert scene["version"] == "rooftop-whole-floor-truth-model-v05"
        assert scene["candidate_status"] == "candidate_window_ceiling_resolved"
        assert scene["design_clashes"] == []

        for path in [module.SURVEY_OUT, module.REPORT_OUT]:
            assert path.exists()
            text = path.read_text(encoding="utf-8")
            assert "v05" in text
            assert "不得" in text
            assert "2450" in text
            assert "2100" in text
            assert "user_decision_required" not in text
            assert "4100×4120" not in text

        report = module.REPORT_OUT.read_text(encoding="utf-8")
        assert "requires_site_measurement" in report
        assert "| `uncertain` |" not in report
        assert sentinel.read_text(encoding="utf-8") == "historical output"


if __name__ == "__main__":
    test_v05_preserves_confirmed_tea_room_topology()
    test_east_end_restores_6160_baseline_and_shifts_bar_as_one_group()
    test_column_chain_uses_confirmed_c_wall_anchor()
    test_owner_confirmed_infill_closes_window_at_2450_ceiling()
    test_v05_render_outputs_are_decodable_versioned_and_non_destructive()
    print("PASS")
