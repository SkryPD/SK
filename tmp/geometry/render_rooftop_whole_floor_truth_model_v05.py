from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\SkryPD\Documents\ChatGPT\听风径民宿装修方向")
OUT_DIR = ROOT / "output" / "空间真值" / "整层灰模" / "候选_v05_20261011"
PLAN_OUT = OUT_DIR / "01_整层俯视空间控制图_v05.png"
ISO_OUT = OUT_DIR / "02_整层去顶轴测灰模_v05.png"
CEILING_OUT = OUT_DIR / "03_茶室窗洞封顶剖示_v05.png"
SCENE_JSON = OUT_DIR / "楼顶整层灰模_v05_坐标场景.json"
SURVEY_OUT = OUT_DIR / "楼顶整层灰模_v05_待复尺清单.md"
REPORT_OUT = OUT_DIR / "楼顶整层灰模_v05_候选核验报告.md"

TRUTH_LEDGER = (
    ROOT
    / "output"
    / "现场复尺审阅"
    / "20261008_逐项确认"
    / "现场复尺已确认真值_20261009.md"
)
CEILING_RECORD = (
    ROOT
    / "output"
    / "空间真值"
    / "天花设计控制"
    / "楼顶两级吊顶业主确认_20261009.md"
)

STATUS = {"verified", "derived", "owner_confirmed", "requires_site_measurement"}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    size: int = 26,
    fill: str = "#20262d",
    bold: bool = False,
    anchor: str = "mm",
) -> None:
    draw.text(xy, text, font=_font(size, bold=bold), fill=fill, anchor=anchor)


def _object(
    object_id: str,
    layer: str,
    category: str,
    bounds_mm: list[float] | None,
    status: str,
    source: str,
    *,
    label: str,
    dimensions_mm: list[float] | None = None,
    height_mm: int | None = None,
    z_mm: int = 0,
    display: bool = True,
    **extra,
) -> dict:
    assert status in STATUS
    item = {
        "id": object_id,
        "label": label,
        "layer": layer,
        "category": category,
        "bounds_mm": bounds_mm,
        "status": status,
        "source": source,
        "display": display,
    }
    if dimensions_mm is not None:
        item["dimensions_mm"] = dimensions_mm
    if height_mm is not None:
        item["height_mm"] = height_mm
    if z_mm:
        item["z_mm"] = z_mm
    item.update(extra)
    return item


def _column_objects() -> list[dict]:
    # Global embedding: confirmed topology point C at X=34240 anchors the
    # owner-confirmed column chain. This embedding is for the gray model only.
    bounds = {
        "steel_column_c1": [30935, 6085, 31040, 6235],
        "steel_column_c2": [27700, 6085, 27805, 6235],
        "steel_column_c3": [23425, 6085, 23530, 6235],
        "steel_column_c4": [19360, 6085, 19465, 6235],
    }
    objects = []
    for index, (object_id, box) in enumerate(bounds.items(), start=1):
        objects.append(
            _object(
                object_id,
                "existing_steel_columns",
                "steel_column",
                box,
                "owner_confirmed",
                "T14-T17 owner-confirmed four-column/three-bay chain; global embedding derived from confirmed point C",
                label=f"C{index}",
                dimensions_mm=[105, 150, 2700],
                height_mm=2700,
                section_mm=[105, 150],
                relative_chain_status="owner_confirmed",
                global_embedding_status="derived_from_owner_chain_plus_plan_anchor",
            )
        )
    return objects


def scene_spec() -> dict:
    # Owner-confirmed topology: A-C-B are collinear on Y=6160. The tea
    # room is C-B-D-E; C-E and B-D are parallel, and E-D is the terrace edge.
    baseline_y = 6160
    a_x, c_x, b_x = 31240, 34240, 37440
    tea_y0, tea_y1 = baseline_y, baseline_y + 4100
    window_y0 = tea_y0 + 440
    window_y1 = window_y0 + 3220

    objects = [
        _object(
            "west_unroofed_terrace",
            "existing_floor_shell",
            "floor",
            [0, 0, 17390, 9160],
            "verified",
            "DWG/PDF plan footprint; retained as the west exterior zone",
            label="西侧室外露台",
            dimensions_mm=[17390, 9160],
            level_mm=0,
            space_type="exterior",
        ),
        _object(
            "main_hall_floor",
            "existing_floor_shell",
            "floor",
            [18390, 0, 31240, 6160],
            "derived",
            "DWG/PDF hall shell with owner-controlled east passage start A",
            label="公共大厅 / 室内主体",
            dimensions_mm=[12850, 6160],
            level_mm=0,
            space_type="interior",
            note="East edge follows owner A control; not a replacement construction dimension for the historic PDF chain.",
        ),
        _object(
            "south_mountain_terrace_band",
            "existing_floor_shell",
            "floor",
            [18460, 6160, 34240, 10260],
            "derived",
            "Plan/site-photo relation: exterior terrace lies beyond the open facade column row",
            label="面山露台带",
            dimensions_mm=[15780, 4100],
            level_mm=0,
            space_type="exterior",
        ),
        _object(
            "east_transition_floor",
            "existing_floor_shell",
            "floor",
            [31240, 0, 34240, 6160],
            "derived",
            "Owner A-B control overlaid on the drawing shell",
            label="茶室前过渡 / 开放通道区",
            dimensions_mm=[3000, 6160],
            level_mm=0,
            space_type="interior_transition",
        ),
        _object(
            "tea_room_floor",
            "existing_floor_shell",
            "floor",
            [c_x, tea_y0, b_x, tea_y1],
            "owner_confirmed",
            "Owner-confirmed C-B-D-E tea-room topology retained in v05",
            label="茶室净域",
            dimensions_mm=[3200, 4100],
            level_mm=0,
            space_type="interior",
        ),
        _object(
            "core_toilet",
            "existing_core_walls",
            "room_volume",
            [23980, -2900, 27421, 0],
            "derived",
            "DWG block extents plus page-1 visual review",
            label="卫生间体块",
            height_mm=2700,
            group="core",
        ),
        _object(
            "core_stair",
            "existing_core_walls",
            "room_volume",
            [28321, -2900, 32040, 0],
            "derived",
            "DWG block extents plus page-1 visual review",
            label="楼梯体块",
            height_mm=2700,
            group="core",
        ),
        _object(
            "core_elevator",
            "existing_core_walls",
            "room_volume",
            [34330, -2900, 36930, 0],
            "derived",
            "DWG block extents plus owner identification of the primary elevator entry",
            label="电梯 / 井道体块",
            height_mm=2700,
            group="core",
        ),
        _object(
            "bar_operation_zone",
            "approved_fixed_design",
            "fixed_design_zone",
            [35040, 1130, 37440, 6160],
            "owner_confirmed",
            "Latest owner correction: 5030 bar run with 1000 standard aisle",
            label="吧台 / 后场操作区",
            dimensions_mm=[2400, 5030],
        ),
        _object(
            "bar_body",
            "approved_fixed_design",
            "fixed_fixture",
            [35040, 1130, 35840, 6160],
            "owner_confirmed",
            "Owner correction recorded after the v01/v17 archive",
            label="吧台 5030×800×1000",
            dimensions_mm=[800, 5030, 1000],
            height_mm=1000,
        ),
        _object(
            "bar_flip_gate",
            "approved_fixed_design",
            "fixed_fixture",
            [35040, 1130, 35840, 1930],
            "owner_confirmed",
            "800 upper/lower flip gate included in the 5030 bar run",
            label="800上下翻门",
            dimensions_mm=[800, 800],
            height_mm=1000,
        ),
        _object(
            "equipment_run",
            "approved_fixed_design",
            "fixed_fixture",
            [36840, 1760, 37440, 6160],
            "owner_confirmed",
            "Owner-confirmed modifiable equipment run after electrical-room entry allowance",
            label="4400设备段",
            dimensions_mm=[600, 4400],
            height_mm=900,
        ),
        _object(
            "equipment_rack",
            "approved_fixed_design",
            "fixed_fixture",
            [36640, 5160, 37440, 6160],
            "owner_confirmed",
            "Owner-confirmed 1000-long, 800-deep stacked appliance rack",
            label="上下叠放设备架",
            dimensions_mm=[800, 1000],
            height_mm=1800,
        ),
        _object(
            "equipment_background_wall",
            "approved_fixed_design",
            "wall",
            [37440, 1130, 37640, 6160],
            "owner_confirmed",
            "Owner-confirmed continuous flat background wall; zero opening or recess",
            label="完整平直设备背景墙",
            dimensions_mm=[200, 5030],
            height_mm=2700,
            opening_count=0,
        ),
        _object(
            "electrical_room_entry",
            "approved_fixed_design",
            "opening_control",
            None,
            "owner_confirmed",
            "T18-T19; entry sits on the side wall and touches the equipment-background-wall corner",
            label="电房入口570×2150",
            dimensions_mm=[570, 2150],
            display=False,
            relation="side_wall_at_equipment_background_corner",
        ),
        _object(
            "tea_open_passage",
            "approved_fixed_design",
            "opening_control",
            [a_x, baseline_y - 100, c_x, baseline_y + 100],
            "owner_confirmed",
            "T20-T21 plus C04: open passage, no door/frame/wall head",
            label="开放通道3000",
            dimensions_mm=[3000, 2700],
            height_mm=2700,
            has_door=False,
            has_frame=False,
            has_lintel_or_wall_head=False,
        ),
        _object(
            "tea_bar_shared_wall",
            "approved_fixed_design",
            "wall",
            [c_x, tea_y0, b_x, tea_y0 + 200],
            "owner_confirmed",
            "T05 and T21: bar/tea shared 200-lightweight-block wall",
            label="吧台与茶室共同墙3200",
            dimensions_mm=[3200, 200],
            height_mm=2700,
        ),
        _object(
            "tea_window_wall_north_jamb",
            "approved_fixed_design",
            "wall",
            [c_x, tea_y0, c_x + 200, window_y0],
            "derived",
            "Window length is verified; this jamb display offset remains to be site-measured",
            label="茶室窗墙北侧墙段",
            dimensions_mm=[200, 440],
            height_mm=3020,
            plan_offset_status="requires_site_measurement",
        ),
        _object(
            "tea_window_wall_south_jamb",
            "approved_fixed_design",
            "wall",
            [c_x, window_y1, c_x + 200, tea_y1],
            "derived",
            "Window length is verified; this jamb display offset remains to be site-measured",
            label="茶室窗墙南侧墙段",
            dimensions_mm=[200, 440],
            height_mm=3020,
            plan_offset_status="requires_site_measurement",
        ),
        _object(
            "tea_window_sill_wall",
            "approved_fixed_design",
            "wall",
            [c_x, window_y0, c_x + 200, window_y1],
            "owner_confirmed",
            "T01-T04 and T11 window vertical dimensions",
            label="茶室窗下墙",
            dimensions_mm=[200, 3220],
            height_mm=350,
        ),
        _object(
            "tea_window_head_wall",
            "approved_fixed_design",
            "wall",
            [c_x, window_y0, c_x + 200, window_y1],
            "owner_confirmed",
            "Owner-confirmed infill extends the upper wall down to the 2450 finished ceiling",
            label="茶室窗上封顶墙",
            dimensions_mm=[200, 3220],
            height_mm=570,
            z_mm=2450,
            z_max_mm=3020,
            former_z_mm=2750,
            resolved_infill_mm=300,
        ),
        _object(
            "tea_room_only_window",
            "approved_fixed_design",
            "opening",
            [c_x, window_y0, c_x + 200, window_y1],
            "owner_confirmed",
            "T01-T04 and T11; display centered only because the opposite-corner offset remains unmeasured",
            label="茶室唯一窗3220×2100",
            dimensions_mm=[3220, 2100],
            height_mm=2100,
            z_mm=350,
            sill_height_mm=350,
            head_height_mm=2450,
            adjacent_column_clear_mm=300,
            top_to_eave_underside_mm=570,
            former_opening_height_mm=2400,
            upper_infill_mm=300,
            plan_offset_status="requires_site_measurement",
            display=False,
        ),
        _object(
            "tea_terrace_boundary_wall",
            "approved_fixed_design",
            "wall",
            [c_x, tea_y1 - 120, b_x, tea_y1],
            "verified",
            "Owner-confirmed E-D wall/boundary coincident with the terrace edge",
            label="茶室露台侧边界墙 E-D",
            dimensions_mm=[3200, 120],
            height_mm=2700,
        ),
        _object(
            "tea_background_wall",
            "approved_fixed_design",
            "wall",
            [b_x - 120, tea_y0, b_x, tea_y1],
            "verified",
            "Owner-confirmed B-D solid background wall with no opening",
            label="茶室背景实墙 B-D",
            dimensions_mm=[120, 4100],
            height_mm=2700,
        ),
        _object(
            "ceiling_level_1_tea_room",
            "design_ceiling",
            "ceiling_control",
            [c_x, tea_y0, b_x, tea_y1],
            "owner_confirmed",
            "C01 revised by owner: the complete tea room uses the 2450 finished ceiling",
            label="茶室全域天花2450",
            dimensions_mm=[3200, 4100],
            height_mm=2450,
            display=False,
            coverage="complete_tea_room_v05_topology",
        ),
        _object(
            "ceiling_level_2_main",
            "design_ceiling",
            "ceiling_control",
            [18390, 0, 34240, 6160],
            "owner_confirmed",
            "C02 revised by owner: all interior outside the tea room, including the open passage",
            label="其余室内天花2700",
            height_mm=2700,
            display=False,
            coverage="all_interior_except_tea_room",
        ),
    ]
    objects.extend(_column_objects())

    layer_order = [
        ("existing_floor_shell", True),
        ("existing_core_walls", True),
        ("existing_steel_columns", True),
        ("approved_fixed_design", True),
        ("design_ceiling", False),
        ("future_glass_system", False),
    ]
    layers = []
    for layer_id, visible in layer_order:
        layers.append(
            {
                "id": layer_id,
                "default_visible": visible,
                "object_ids": [item["id"] for item in objects if item["layer"] == layer_id],
            }
        )

    return {
        "version": "rooftop-whole-floor-truth-model-v05",
        "candidate_status": "candidate_window_ceiling_resolved",
        "units": "millimetres",
        "purpose": "spatial truth, camera control and owner-confirmed design review; not construction setting-out",
        "authority": [
            str(TRUTH_LEDGER),
            str(CEILING_RECORD),
            "owner corrections in the current thread",
            "DWG/PDF for unchanged shell geometry",
        ],
        "coordinate_system": {
            "cad_origin": [547064.38, -262312.323],
            "local_x_rule": "cad_x-origin_x with owner-confirmed east-end overrides",
            "local_y_rule": "-(cad_y-origin_y)",
            "historic_bottom_dimension_chain_mm": [17390, 1000, 12380, 120, 2500, 120, 3930],
            "historic_total_mm": 37440,
            "east_end_anchor_points_mm": {"A": a_x, "C": c_x, "B": b_x},
            "overall_plan_bounds_mm": [0, -2900, 37640, 10260],
        },
        "global_control_mm": {
            "east_end_baseline_y": baseline_y,
            "superseded_east_end_baseline_y": 5040,
            "east_end_translation_y": 1120,
        },
        "tea_room_topology": {
            "confirmation_artifact": "34_茶室墙体拓扑_照片方向俯视确认_v02.png",
            "confirmed_on": "2026-10-10",
            "points_mm": {
                "A": [a_x, baseline_y],
                "C": [c_x, baseline_y],
                "B": [b_x, baseline_y],
                "D": [b_x, tea_y1],
                "E": [c_x, tea_y1],
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
        },
        "east_end_control_mm": {
            "passage_clear_width": 3000,
            "shared_wall_length": 3200,
            "control_total": 6200,
            "passage_has_door": False,
            "passage_has_frame": False,
            "passage_has_lintel_or_wall_head": False,
            "passage_open_height": 2700,
        },
        "open_facade_control_mm": {
            "direction": "tea_room_end_to_west_end",
            "fixed_wall_to_c1": 3200,
            "column_width_along_row": 105,
            "column_depth_indoor_to_terrace": 150,
            "clear_bays": [3130, 4170, 3960],
            "four_column_chain": 11680,
            "fixed_wall_to_c4_west_face": 14880,
        },
        "floor_levels_mm": {"public_interior": 0, "tea_room": 0, "terrace": 0},
        "ceiling_controls_mm": {
            "level_1_tea_room": {
                "height": 2450,
                "coverage": "complete_tea_room_v05_topology",
                "plan_extent_mm": [3200, 4100],
            },
            "level_2_main": {"height": 2700, "coverage": "all_interior_except_tea_room"},
            "level_difference": 250,
            "open_passage_to_level_2_ceiling": True,
        },
        "layers": layers,
        "objects": objects,
        "equipment_sequence": [
            {"id": "E1", "type": "stainless_counter_fridge_1", "length_mm": 1000},
            {"id": "E2", "type": "stainless_counter_fridge_2_with_electric_stove", "length_mm": 1000},
            {"id": "E3", "type": "stainless_blank_worktop", "length_mm": 500},
            {"id": "E4", "type": "stainless_sink_with_glass_rinser", "length_mm": 900},
            {"id": "E5", "type": "stacked_appliance_rack", "length_mm": 1000},
        ],
        "conflicts": [],
        "superseded_assumptions": [
            {
                "id": "v01_east_end_fixed_point_conflict",
                "replacement": "owner control A-B=6200 composed of 3000 open passage and 3200 shared wall",
                "status": "superseded",
            },
            {
                "id": "v01_bar_length_5300",
                "replacement": "owner-corrected bar length 5030 including 800 flip gate",
                "status": "superseded",
            },
            {
                "id": "v01_provisional_column_mapping",
                "replacement": "owner-confirmed 4 columns / 3 clear bays / 105x150 section",
                "status": "superseded",
            },
            {
                "id": "v03_tea_room_rectangle_4100_by_4120",
                "replacement": "owner-confirmed C-B-D-E topology with C-B=3200 and B-D=4100",
                "status": "superseded",
            },
        ],
        "design_clashes": [],
        "resolved_design_decisions": [
            {
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
        ],
        "excluded_scope": [
            "mep_geometry",
            "loose_furniture",
            "landscape",
            "future_glass_geometry",
            "people_and_soft_furnishings",
        ],
    }


def _line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    fill: str,
    *,
    width: int = 2,
    dash: int | None = None,
) -> None:
    if dash is None:
        draw.line(points, fill=fill, width=width, joint="curve")
        return
    for a, b in zip(points, points[1:]):
        x0, y0 = a
        x1, y1 = b
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            continue
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        cursor = 0.0
        while cursor < length:
            end = min(length, cursor + dash)
            draw.line(
                [(x0 + dx * cursor, y0 + dy * cursor), (x0 + dx * end, y0 + dy * end)],
                fill=fill,
                width=width,
            )
            cursor += dash * 1.75


def _dimension(draw, a, b, offset, label, project, color="#4b5563", size=17) -> None:
    pa, pb = project(*a), project(*b)
    if abs(pa[0] - pb[0]) >= abs(pa[1] - pb[1]):
        y = pa[1] + offset
        p1, p2 = (pa[0], y), (pb[0], y)
        draw.line([pa, (pa[0], y)], fill=color, width=2)
        draw.line([pb, (pb[0], y)], fill=color, width=2)
        draw.line([p1, p2], fill=color, width=2)
        for x in (p1[0], p2[0]):
            draw.line([(x - 6, y + 6), (x + 6, y - 6)], fill=color, width=2)
        _label(draw, ((p1[0] + p2[0]) // 2, y - 10), label, size=size, fill=color, anchor="ms")
    else:
        x = pa[0] + offset
        p1, p2 = (x, pa[1]), (x, pb[1])
        draw.line([pa, (x, pa[1])], fill=color, width=2)
        draw.line([pb, (x, pb[1])], fill=color, width=2)
        draw.line([p1, p2], fill=color, width=2)
        for y in (p1[1], p2[1]):
            draw.line([(x - 6, y + 6), (x + 6, y - 6)], fill=color, width=2)
        _label(draw, (x + 12, (p1[1] + p2[1]) // 2), label, size=size, fill=color, anchor="lm")


def _objects_by_id(scene: dict) -> dict[str, dict]:
    return {item["id"]: item for item in scene["objects"]}


def render_plan(scene: dict) -> None:
    width, height = 2600, 1600
    image = Image.new("RGBA", (width, height), "#f5f2ea")
    draw = ImageDraw.Draw(image)
    margin_left, margin_top = 105, 205
    plan_w, plan_h = 2200, 725
    x_min, x_max = -500, 38100
    y_min, y_max = -3100, 10600

    def project(x, y):
        return (
            int(round(margin_left + (x - x_min) / (x_max - x_min) * plan_w)),
            int(round(margin_top + (y - y_min) / (y_max - y_min) * plan_h)),
        )

    draw.rectangle((0, 0, width, 150), fill="#202b36")
    _label(draw, (72, 60), "楼顶整层空间真值灰模 v05｜俯视控制图（候选）", size=42, fill="white", bold=True, anchor="lm")
    _label(draw, (74, 116), "A-C-B共线；C-E与B-D平行；E-D贴露台边界｜橙色为已确认固定设计", size=22, fill="#dce5ec", anchor="lm")

    by_id = _objects_by_id(scene)
    floor_palette = {
        "west_unroofed_terrace": "#dce5e9",
        "main_hall_floor": "#eee7d7",
        "south_mountain_terrace_band": "#d9e8df",
        # This is the same continuous indoor floor as the main hall. It must
        # not read as a blue glass, window, or newly built volume.
        "east_transition_floor": "#eee7d7",
        "tea_room_floor": "#e9e0ef",
        "bar_operation_zone": "#f5dfc3",
    }
    for object_id, color in floor_palette.items():
        item = by_id[object_id]
        x0, y0, x1, y1 = item["bounds_mm"]
        draw.rectangle([project(x0, y0), project(x1, y1)], fill=color, outline="#68737b", width=2)

    # The complete owner-confirmed v05 tea-room topology is at 2450.
    low = by_id["ceiling_level_1_tea_room"]["bounds_mm"]
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle([project(low[0], low[1]), project(low[2], low[3])], fill=(235, 169, 45, 70), outline=(214, 132, 19, 255), width=4)
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    solid_categories = {"room_volume", "wall", "steel_column", "fixed_fixture"}
    colors = {
        "existing_core_walls": "#66737e",
        "existing_steel_columns": "#253b4a",
        "approved_fixed_design": "#b66b21",
    }
    for item in scene["objects"]:
        if item["category"] not in solid_categories or item["bounds_mm"] is None:
            continue
        x0, y0, x1, y1 = item["bounds_mm"]
        draw.rectangle([project(x0, y0), project(x1, y1)], fill=colors[item["layer"]], outline="#263038", width=2)

    # Equipment sequence across the 4400 confirmed run.
    equipment = [
        (1760, 2760, "E1 冰柜", "#91b5c1"),
        (2760, 3760, "E2 冰柜+电灶", "#789eaa"),
        (3760, 4260, "E3 空台", "#cbb88c"),
        (4260, 5160, "E4 水池", "#82aa91"),
        (5160, 6160, "E5 设备架", "#9e84b9"),
    ]
    for y0, y1, text, color in equipment:
        draw.rectangle([project(36840, y0), project(37440, y1)], fill=color, outline="#3d4951", width=2)
        cx, cy = project(37140, (y0 + y1) / 2)
        _label(draw, (cx, cy), text, size=15, bold=True)

    # Only one tea-room window. The run length is exact; its opposite-jamb offset is not.
    window = by_id["tea_room_only_window"]
    x0, y0, _, y1 = window["bounds_mm"]
    p1, p2 = project(x0, y0), project(x0, y1)
    draw.line([p1, p2], fill="#2477c9", width=10)
    _label(draw, (p1[0] - 14, (p1[1] + p2[1]) // 2), "窗3220", size=15, fill="#1d67aa", bold=True, anchor="rm")

    # Owner-confirmed topology controls.
    topology = scene["tea_room_topology"]
    points = topology["points_mm"]
    ax, baseline_y = points["A"]
    cx, _ = points["C"]
    bx, _ = points["B"]
    _line(draw, [project(*points["A"]), project(*points["C"])], "#d54d43", width=6, dash=13)
    _line(draw, [project(*points["C"]), project(*points["E"])], "#2477c9", width=4)
    _line(draw, [project(*points["B"]), project(*points["D"])], "#a55d16", width=4)
    _line(draw, [project(*points["E"]), project(*points["D"])], "#177c69", width=4)
    for label, (x, y) in points.items():
        color = "#d07a16" if label in {"C", "E"} else "#256489"
        px, py = project(x, y)
        draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=color, outline="white", width=2)
        label_x = px + (18 if label in {"B", "D"} else 0)
        label_y = py + (28 if label in {"D", "E"} else -27)
        _label(draw, (label_x, label_y), label, size=18, fill=color, bold=True)

    # Open-facade confirmed chain and direction.
    row_y = baseline_y
    _line(draw, [project(19360, row_y), project(cx, row_y)], "#177c69", width=4, dash=14)
    _label(draw, project(26500, 6490), "面山敞开界面｜C点茶室端 → 西端", size=19, fill="#116a59", bold=True)
    for column_id in ("steel_column_c1", "steel_column_c2", "steel_column_c3", "steel_column_c4"):
        item = by_id[column_id]
        x0, y0, x1, y1 = item["bounds_mm"]
        cxp, cyp = project((x0 + x1) / 2, (y0 + y1) / 2)
        _label(draw, (cxp, cyp - 24), item["label"], size=16, fill="#163849", bold=True)

    # Labels.
    labels = [
        ("west_unroofed_terrace", "西侧室外露台", 0, 0),
        ("main_hall_floor", "公共大厅 / 室内主体", 0, -50),
        ("south_mountain_terrace_band", "面山露台｜与室内同标高", 0, 60),
        ("core_toilet", "卫生间", 0, 0),
        ("core_stair", "楼梯", 0, 0),
        ("core_elevator", "电梯 / 井道", 0, 0),
        ("bar_operation_zone", "吧台", -45, -55),
        ("tea_room_floor", "茶室", 65, 75),
    ]
    for object_id, text, dx, dy in labels:
        item = by_id[object_id]
        x0, y0, x1, y1 = item["bounds_mm"]
        px, py = project((x0 + x1) / 2, (y0 + y1) / 2)
        _label(draw, (px + dx, py + dy), text, size=20, bold=True)

    # Dimensions for the corrected local chains.
    _dimension(draw, points["A"], points["C"], -50, "A-C开放通道3000", project, color="#c83932", size=16)
    _dimension(draw, points["C"], points["B"], 55, "C-B共同墙3200", project, color="#a55d16", size=16)
    _dimension(draw, points["B"], points["D"], 55, "B-D 4100", project, color="#704e87", size=16)
    _dimension(draw, points["E"], points["D"], 42, "E-D露台侧边界3200", project, color="#177c69", size=16)
    _dimension(draw, (cx, row_y), (31040, row_y), -78, "C至C1东侧3200", project, color="#1d5f83", size=15)
    _dimension(draw, (31040, row_y), (19360, row_y), -112, "四柱三跨11680", project, color="#1d5f83", size=16)
    _dimension(draw, (cx, row_y), (19360, row_y), -146, "C至C4西侧14880", project, color="#c43c34", size=16)

    # Owner-confirmed window-head resolution.
    callout = (1590, 1030, 2490, 1390)
    draw.rounded_rectangle(callout, radius=18, fill="#f2faf5", outline="#2e7b62", width=4)
    _label(draw, (1630, 1075), "已确认：窗洞封顶至2450天花底", size=27, fill="#246c58", bold=True, anchor="la")
    resolution_lines = [
        "窗台：350 mm｜新窗高：2100 mm",
        "新窗顶：350 + 2100 = 2450 mm",
        "上墙：Z=2450–3020，高570 mm",
        "原300 mm冲突已按业主确认封闭。",
    ]
    for i, text in enumerate(resolution_lines):
        _label(draw, (1630, 1135 + i * 52), text, size=21, fill="#444b50", anchor="la")

    # Legend and status notes.
    legend_x, legend_y = 105, 1055
    _label(draw, (legend_x, legend_y), "图层 / 状态", size=25, bold=True, anchor="la")
    legend = [
        ("#eee7d7", "室内及地坪骨架"),
        ("#253b4a", "实测确认钢柱105×150"),
        ("#b66b21", "业主确认固定构件"),
        ("#2477c9", "唯一窗：3220×2100，端部定位待复尺"),
        ("#d6a92d", "茶室全域2450天花控制"),
        ("#2e7b62", "窗顶冲突已按封顶方案解决"),
    ]
    for i, (color, text) in enumerate(legend):
        y = legend_y + 48 + i * 43
        draw.rectangle((legend_x, y - 13, legend_x + 28, y + 15), fill=color, outline="#4b565e")
        _label(draw, (legend_x + 43, y), text, size=18, anchor="lm")

    # Keep the compact east-end model readable by moving descriptive text out
    # of the drawing. A/C/B and the dimension lines remain on the plan itself.
    detail = (700, 1025, 1535, 1435)
    draw.rounded_rectangle(detail, radius=18, fill="#fffdf8", outline="#74828b", width=3)
    _label(draw, (740, 1068), "东端局部控制", size=26, fill="#273640", bold=True, anchor="la")
    detail_rows = [
        ("A-C", "开放通道3000｜无门、无门框、无门楣｜通高2700", "#bd322a"),
        ("C-B", "共同墙3200｜200轻质砖", "#a55d16"),
        ("茶室", "C-B 3200 × B-D 4100｜唯一窗3220×2100", "#76588e"),
        ("吧台", "5030×800×1000｜设备段4400", "#b66b21"),
        ("天花", "茶室全域2450｜开放通道及其余室内2700", "#8b6517"),
    ]
    for i, (key, text, color) in enumerate(detail_rows):
        y = 1125 + i * 60
        _label(draw, (740, y), key, size=19, fill=color, bold=True, anchor="la")
        _label(draw, (835, y), text, size=17, fill="#444c52", anchor="la")

    footer = "候选图｜相对尺寸按已确认真值；全局嵌入与未复尺项不得用于施工放样，效果图不得反推尺寸。"
    draw.rectangle((0, 1545, width, height), fill="#202b36")
    _label(draw, (width // 2, 1573), footer, size=19, fill="white")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(PLAN_OUT)


def isometric_boxes(scene: dict) -> list[dict]:
    included = {"room_volume", "wall", "steel_column", "fixed_fixture"}
    boxes = []
    for item in scene["objects"]:
        if item["category"] not in included or item["bounds_mm"] is None or not item.get("display", True):
            continue
        x0, y0, x1, y1 = item["bounds_mm"]
        boxes.append(
            {
                "id": item["id"],
                "label": item["label"],
                "layer": item["layer"],
                "x_mm": x0,
                "y_mm": y0,
                "z_mm": item.get("z_mm", 0),
                "width_mm": x1 - x0,
                "depth_mm": y1 - y0,
                "height_mm": item["height_mm"],
                "status": item["status"],
            }
        )
    return boxes


def _iso_projector(boxes: list[dict], canvas: tuple[int, int]):
    angle = math.radians(28)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    def raw(x, y, z):
        return (x - y) * cos_a, (x + y) * sin_a - z

    points = []
    for box in boxes:
        x0, y0, z0 = box["x_mm"], box["y_mm"], box["z_mm"]
        x1, y1, z1 = x0 + box["width_mm"], y0 + box["depth_mm"], z0 + box["height_mm"]
        points.extend(raw(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1))
    points.extend(raw(x, y, 0) for x in (0, 37640) for y in (-2900, 10600))
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    pad_x, pad_y = 170, 200
    usable_w, usable_h = canvas[0] - 2 * pad_x, canvas[1] - pad_y - 190
    scale = min(usable_w / (max(xs) - min(xs)), usable_h / (max(ys) - min(ys)))

    def project(x, y, z):
        rx, ry = raw(x, y, z)
        return int(pad_x + (rx - min(xs)) * scale), int(pad_y + (ry - min(ys)) * scale)

    return project


def _draw_box(draw, project, box, colors) -> None:
    x0, y0, z0 = box["x_mm"], box["y_mm"], box["z_mm"]
    x1, y1, z1 = x0 + box["width_mm"], y0 + box["depth_mm"], z0 + box["height_mm"]
    p000, p100 = project(x0, y0, z0), project(x1, y0, z0)
    p110, p010 = project(x1, y1, z0), project(x0, y1, z0)
    p001, p101 = project(x0, y0, z1), project(x1, y0, z1)
    p111, p011 = project(x1, y1, z1), project(x0, y1, z1)
    edge = "#45515b"
    draw.polygon([p100, p110, p111, p101], fill=colors[1], outline=edge)
    draw.polygon([p010, p110, p111, p011], fill=colors[2], outline=edge)
    draw.polygon([p001, p101, p111, p011], fill=colors[0], outline=edge)


def render_isometric(scene: dict) -> None:
    width, height = 2600, 1550
    image = Image.new("RGB", (width, height), "#f3f1eb")
    draw = ImageDraw.Draw(image)
    boxes = isometric_boxes(scene)
    project = _iso_projector(boxes, (width, height))

    draw.rectangle((0, 0, width, 150), fill="#202b36")
    _label(draw, (72, 60), "楼顶整层空间真值灰模 v05｜去顶轴测（候选）", size=42, fill="white", bold=True, anchor="lm")
    _label(draw, (74, 116), "按已确认A-C-B / C-B-D-E拓扑重建；吧台与设备段整体接至6160基线", size=22, fill="#dce5ec", anchor="lm")

    floor_polys = [
        ([project(0, 0, 0), project(17390, 0, 0), project(17390, 9160, 0), project(0, 9160, 0)], "#dce5e9"),
        ([project(18390, 0, 0), project(31240, 0, 0), project(31240, 6160, 0), project(18390, 6160, 0)], "#e9e3d6"),
        ([project(18460, 6160, 0), project(34240, 6160, 0), project(34240, 10260, 0), project(18460, 10260, 0)], "#dae8df"),
        ([project(31240, 0, 0), project(34240, 0, 0), project(34240, 6160, 0), project(31240, 6160, 0)], "#e9e3d6"),
        ([project(34240, 6160, 0), project(37440, 6160, 0), project(37440, 10260, 0), project(34240, 10260, 0)], "#e8e0ec"),
    ]
    for poly, color in floor_polys:
        draw.polygon(poly, fill=color, outline="#69747c")

    for box in sorted(boxes, key=lambda b: b["x_mm"] + b["y_mm"] + b["z_mm"] * 0.1):
        if box["layer"] == "existing_core_walls":
            colors = ("#acb5bd", "#929ea8", "#7d8a94")
        elif box["layer"] == "existing_steel_columns":
            colors = ("#456277", "#304c60", "#213c50")
        elif box["id"].startswith("tea_") or box["id"] == "equipment_background_wall":
            colors = ("#d0b98d", "#b89c6e", "#a68859")
        else:
            colors = ("#d5b27d", "#bd8f55", "#a7783e")
        _draw_box(draw, project, box, colors)

    # Open passage has no solid geometry; show its clear span at the top boundary.
    points = scene["tea_room_topology"]["points_mm"]
    p1, p2 = project(*points["A"], 2700), project(*points["C"], 2700)
    _line(draw, [p1, p2], "#d24a40", width=5, dash=12)

    annotations = [
        (project(8000, 4700, 0), (260, 1130), "西侧室外露台", "#506d7b"),
        (project(26900, 6160, 2700), (720, 780), "C1-C4四柱三跨\n105×150｜按C点锚定", "#245c78"),
        (project(25700, 2700, 0), (1210, 930), "公共大厅 / 室内主体", "#73694f"),
        (project(28500, -900, 2700), (1430, 310), "凹凸核心筒", "#596773"),
        (project(36200, 3300, 1500), (2010, 450), "吧台5030 / 设备段4400", "#b66b21"),
        (project(35840, 8210, 2350), (1980, 1080), "茶室3200×4100\n唯一窗3220×2100", "#76588e"),
        (project(32700, 6160, 2700), (1690, 770), "开放通道3000\n无门、无门楣，通高2700", "#bd3e36"),
    ]
    for anchor, text_xy, text, color in annotations:
        draw.line([anchor, text_xy], fill=color, width=4)
        draw.ellipse((anchor[0] - 6, anchor[1] - 6, anchor[0] + 6, anchor[1] + 6), fill=color)
        box_w = 365
        draw.rounded_rectangle((text_xy[0] - 12, text_xy[1] - 44, text_xy[0] + box_w, text_xy[1] + 50), radius=13, fill="#fffdf9", outline=color, width=3)
        _label(draw, (text_xy[0] + 8, text_xy[1]), text, size=18, fill=color, bold=True, anchor="lm")

    callout = (82, 175, 780, 465)
    draw.rounded_rectangle(callout, radius=18, fill="#f2faf5", outline="#2e7b62", width=4)
    _label(draw, (116, 220), "v05竖向控制｜封顶已确认", size=27, fill="#246c58", bold=True, anchor="la")
    notes = [
        "地坪：公共室内 / 茶室 / 露台均为±0；",
        "茶室全域天花2450，其余室内2700；",
        "茶室窗顶2450，与完成天花齐平；",
        "窗上封顶墙Z=2450–3020，高570。",
    ]
    for i, text in enumerate(notes):
        _label(draw, (116, 274 + i * 45), "• " + text, size=19, fill="#454c51", anchor="la")

    strip = (82, 1320, 2515, 1472)
    draw.rounded_rectangle(strip, radius=18, fill="white", outline="#aab1b7", width=2)
    _label(draw, (120, 1360), "视图状态", size=22, bold=True, anchor="la")
    states = [
        ("显示", "硬壳 / 真实柱链 / 吧台设备 / 茶室窗洞", "#246c58"),
        ("另图表达", "窗洞封顶至2450及上墙570", "#246c58"),
        ("排除", "机电 / 活动家具 / 绿植 / 人物 / 未来玻璃", "#8c3840"),
    ]
    for i, (state, text, color) in enumerate(states):
        x = 120 + i * 800
        _label(draw, (x, 1410), state, size=19, fill=color, bold=True, anchor="la")
        _label(draw, (x, 1445), text, size=16, fill="#4d545a", anchor="la")

    draw.rectangle((0, 1502, width, height), fill="#202b36")
    _label(draw, (width // 2, 1527), "候选图｜用于空间拓扑、视角和碰撞沟通，不得用于施工放样。", size=19, fill="white")
    image.save(ISO_OUT)


def render_ceiling_section(scene: dict) -> None:
    width, height = 2400, 1400
    image = Image.new("RGB", (width, height), "#f5f2ea")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 150), fill="#202b36")
    _label(draw, (72, 60), "茶室｜窗洞封顶至2450剖示 v05", size=42, fill="white", bold=True, anchor="lm")
    _label(draw, (74, 116), "窗顶与茶室2450完成天花齐平；上方570墙体封至3020", size=22, fill="#dce5ec", anchor="lm")

    floor_y = 1165
    z_scale = 0.29

    def py(z_mm: int) -> int:
        return int(round(floor_y - z_mm * z_scale))

    wall_x = 390
    boundary_x = 1800
    room_end_x = 2140
    draw.line((220, floor_y, 2200, floor_y), fill="#343e46", width=7)
    _label(draw, (230, floor_y + 32), "完成地面 ±0.000", size=20, fill="#343e46", bold=True, anchor="la")

    # Window wall and opening.
    draw.rectangle((wall_x - 80, py(3020), wall_x + 80, floor_y), fill="#b7aa93", outline="#4a5258", width=3)
    draw.rectangle((wall_x - 86, py(2450), wall_x + 86, py(350)), fill="#b9d9e7", outline="#2477c9", width=5)
    _label(draw, (wall_x, (py(2450) + py(350)) // 2), "窗\n2100", size=24, fill="#1d67aa", bold=True)
    _dimension(draw, (wall_x + 95, py(350)), (wall_x + 95, py(2450)), 60, "窗高2100", lambda x, y: (int(x), int(y)), color="#2477c9", size=18)
    _label(draw, (wall_x - 110, py(350)), "窗台350", size=18, fill="#42515c", anchor="rm")
    _label(draw, (wall_x - 110, py(2450)), "新窗顶2450", size=18, fill="#246c58", bold=True, anchor="rm")
    draw.line((250, py(3020), 620, py(3020)), fill="#6c747a", width=4)
    _label(draw, (635, py(3020)), "挡水檐下口3020（2450+570）", size=18, fill="#5b6369", anchor="lm")

    # The complete tea room is level 1; level 2 begins only outside it.
    draw.rectangle((wall_x, py(2450) - 11, boundary_x, py(2450) + 11), fill="#d69a26", outline="#9b6517", width=2)
    draw.rectangle((boundary_x, py(2700) - 11, room_end_x, py(2700) + 11), fill="#4f8a73", outline="#32664f", width=2)
    draw.line((boundary_x, py(2450), boundary_x, py(2700)), fill="#6d7479", width=4)
    _label(draw, ((wall_x + boundary_x) // 2, py(2450) + 46), "茶室全域天花2450", size=22, fill="#8b5911", bold=True)
    _label(draw, ((boundary_x + room_end_x) // 2, py(2700) + 46), "其余室内\n2700", size=18, fill="#2f674f", bold=True)
    _label(draw, (boundary_x + 20, (py(2450) + py(2700)) // 2), "高差250", size=18, fill="#565e64", anchor="lm")

    # Show the confirmed 300 mm infill against the former 2750 window head.
    draw.rectangle((wall_x - 105, py(2750), wall_x + 105, py(2450)), fill="#82b39b", outline="#2e7b62", width=3)
    _label(draw, (wall_x + 130, (py(2750) + py(2450)) // 2), "新增封闭300", size=21, fill="#246c58", bold=True, anchor="lm")
    _line(draw, [(wall_x - 120, py(2750)), (wall_x + 120, py(2750))], "#6f777b", width=2, dash=8)
    _label(draw, (wall_x - 130, py(2750)), "原窗顶2750", size=17, fill="#6f777b", anchor="rm")

    # Numeric audit panel.
    panel = (1260, 670, 2250, 1100)
    draw.rounded_rectangle(panel, radius=20, fill="#f4fbf6", outline="#2e7b62", width=4)
    _label(draw, (1310, 720), "封顶几何校核", size=29, fill="#246c58", bold=True, anchor="la")
    rows = [
        "新窗顶 = 窗台350 + 窗高2100 = 2450",
        "茶室天花 = 2450 mm（全域）",
        "封顶墙 = 3020 - 2450 = 570 mm",
        "原300 mm冲突：owner_confirmed_resolved",
        "施工前仍须深化窗框、收口及防水节点。",
    ]
    for i, text in enumerate(rows):
        _label(draw, (1310, 786 + i * 58), text, size=20, fill="#454c51", anchor="la", bold=i == 3)

    draw.rectangle((0, 1338, width, height), fill="#202b36")
    _label(draw, (width // 2, 1368), "候选图｜封顶关系已落实；本图不替代门窗、吊顶及防水节点深化。", size=20, fill="white")
    image.save(CEILING_OUT)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_scene(scene: dict) -> None:
    SCENE_JSON.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_survey_list() -> None:
    SURVEY_OUT.write_text(
        """# 楼顶整层灰模 v05｜剩余复尺与深化清单

本清单已经删除2026-10-09台账中完成确认的窗、柱链、地坪和通道项目。不得从灰模或效果图反推施工尺寸。

v05保留2026-10-10确认的A-C-B、C-B-D-E拓扑，并落实2026-10-11业主确认的“封顶”：茶室窗洞宽3220、高2100，Z=350–2450；上部墙体Z=2450–3020，高570，与2450完成天花闭合。

## 已解决设计项

1. **窗顶与天花关系**：原窗顶2750与2450天花的300mm冲突，已通过向下补齐上墙、把新窗顶锁定在2450解决；不得恢复v04冲突状态。

## 后续现场复尺（不阻塞当前空间灰模）

2. 茶室唯一窗沿C-E墙方向距C、E两端墙角的净尺寸，用于替换v05暂定显示位置。
3. 露台女儿墙/栏杆完成面高度，雨棚或檐口底标高。
4. 钢屋架最低点、最高点、主要梁底及机电综合净空。
5. 若模型需要施工级闭合，复核旧PDF整体分段与现场端到端总尺；旧`17390/18390`相关分段不得由灰模代算。

## 厂家深化

6. 两台操作台冰柜、水池、电灶、制冰机和设备架最终型号、散热及检修余量。
7. 吊顶龙骨、检修口、消防、风管和冷凝水与茶室2450/其余室内2700完成面的碰撞复核。
8. 窗框、2450封顶收口、挡水檐与防水节点由门窗及吊顶专业联合深化。
""",
        encoding="utf-8",
    )


def _write_report(scene: dict) -> None:
    files = [PLAN_OUT, ISO_OUT, CEILING_OUT, SCENE_JSON, SURVEY_OUT]
    file_lines = [f"- `{path.name}` — {path.stat().st_size:,} bytes — SHA-256 `{_sha256(path)}`" for path in files]
    REPORT_OUT.write_text(
        f"""# 楼顶整层灰模 v05｜候选核验报告

## 状态

- 版本：`{scene['version']}`
- 当前状态：`{scene['candidate_status']}`
- 用途：空间真值、镜头控制与业主确认关系复核；不得用于施工放样。

## v05已落实

| 核验项 | 状态 | 结果 |
|---|---|---|
| 吧台尺寸 | `pass` | 5030×800×1000，含800上下翻门 |
| 设备段 | `pass` | 4400，设备顺序总和闭合 |
| 茶室拓扑 | `pass` | A-C-B共线；C-E与B-D平行；E-D贴露台边界；无额外条带或内墙 |
| 茶室净域 | `pass` | C-B=3200，B-D=4100；v03旧矩形关系已停用 |
| 东端关系 | `pass` | A-C开放通道3000 + C-B共同墙3200 = 6200 |
| 通道界面 | `pass` | 无门、无门框、无墙头/门楣，直达2700天花底 |
| 柱列 | `pass` | 4柱3跨；105×150；净跨3130/4170/3960；总链11680 |
| 地坪 | `pass` | 公共室内、茶室、露台均为±0 |
| 茶室唯一窗 | `pass` | 3220×2100，窗台350，窗顶2450，Z=350–2450 |
| 窗上封顶墙 | `pass` | Z=2450–3020，高570；其中含原冲突区300的补墙 |
| 茶室天花 | `pass` | 茶室3200×4100全域完成面2450 |
| 其余室内天花 | `pass` | 开放通道及茶室以外室内完成面2700 |
| 窗沿墙端部定位 | `uncertain` | 仅居中显示；另一端墙角净距仍需现场复尺 |

## 已解决设计项

- 原状态：窗顶2750，高于茶室2450天花300mm。
- 业主确认：封顶；新窗高2100，新窗顶2450，上墙向下补至2450。
- 当前状态：`owner_confirmed_resolved`；`design_clashes`为空。
- 后续边界：门窗框、吊顶收口及防水仍须专业深化，不得直接由本灰模施工放样。

## 文件核验

{chr(10).join(file_lines)}

## 非施工声明

相对尺寸来自现场复尺与业主确认；全局嵌入仍含图纸推导关系。任何灰模、轴测或效果图均不得用于反推施工尺寸，结构、消防、机电、门窗与设备最终以现场复尺和专业深化为准。
""",
        encoding="utf-8",
    )


def render_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = scene_spec()
    render_plan(scene)
    render_isometric(scene)
    render_ceiling_section(scene)
    _write_scene(scene)
    _write_survey_list()
    _write_report(scene)


if __name__ == "__main__":
    render_all()
    print(PLAN_OUT)
    print(ISO_OUT)
    print(CEILING_OUT)
    print(SCENE_JSON)
    print(SURVEY_OUT)
    print(REPORT_OUT)
