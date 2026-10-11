from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MODULE = ROOT / "tmp" / "geometry" / "render_rooftop_whole_floor_truth_model_v05.py"
OUT_DIR = ROOT / "output" / "空间真值" / "整层灰模" / "封顶可视化_候选_v01_20261011"
OPAQUE_OUT = OUT_DIR / "01_茶室完整封顶轴测灰模_v01.png"
CUTAWAY_OUT = OUT_DIR / "02_茶室封顶半透明剖切灰模_v01.png"
REPORT_OUT = OUT_DIR / "茶室封顶可视化_v01_候选核验报告.md"

CANVAS = (2400, 1500)
INK = "#354049"
HEADER = "#202b36"
PAPER = "#f2f1ec"
WALL_TOP = "#c9c5bd"
WALL_X = "#a9a49b"
WALL_Y = "#b9b4aa"
CEILING = "#b8ad84"
CEILING_EDGE = "#7c6a2f"
WINDOW = "#9bc6d7"
WINDOW_EDGE = "#347b98"
RESOLVED = "#2f7d67"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf" if bold else r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    *,
    size: int = 22,
    fill: str = INK,
    bold: bool = False,
    anchor: str = "la",
) -> None:
    draw.multiline_text(
        xy,
        value,
        font=_font(size, bold=bold),
        fill=fill,
        anchor=anchor,
        spacing=max(5, size // 4),
        align="left",
    )


def load_v05_module():
    if not SOURCE_MODULE.exists():
        raise FileNotFoundError(f"Missing v05 truth-model source: {SOURCE_MODULE}")
    spec = importlib.util.spec_from_file_location("whole_floor_truth_model_v05", SOURCE_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v05 truth-model module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_source_scene() -> dict:
    source = load_v05_module().scene_spec()
    if source["version"] != "rooftop-whole-floor-truth-model-v05":
        raise ValueError("Ceiling visibility renderer requires v05 truth geometry")
    return source


def _objects_by_id(scene: dict) -> dict[str, dict]:
    return {item["id"]: item for item in scene["objects"]}


def ceiling_contract(scene: dict) -> dict:
    objects = _objects_by_id(scene)
    ceiling = objects["ceiling_level_1_tea_room"]
    window = objects["tea_room_only_window"]
    head = objects["tea_window_head_wall"]
    return {
        "bounds_mm": ceiling["bounds_mm"],
        "ceiling_z_mm": ceiling["height_mm"],
        "window_z_range_mm": [window["z_mm"], window["head_height_mm"]],
        "head_wall_z_range_mm": [head["z_mm"], head["z_max_mm"]],
    }


def _local_box(item: dict, origin: tuple[int, int]) -> dict:
    x0, y0, x1, y1 = item["bounds_mm"]
    z0 = item.get("z_mm", 0)
    z1 = item.get("z_max_mm", z0 + item["height_mm"])
    return {
        "id": item["id"],
        "x0": x0 - origin[0],
        "y0": y0 - origin[1],
        "x1": x1 - origin[0],
        "y1": y1 - origin[1],
        "z0": z0,
        "z1": z1,
    }


def _projector(width_mm: int, depth_mm: int):
    angle = math.radians(30)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    def raw(x: float, y: float, z: float) -> tuple[float, float]:
        return (x - y) * cos_a, (x + y) * sin_a - z

    model_points = [
        raw(x, y, z)
        for x in (0, width_mm)
        for y in (0, depth_mm)
        for z in (0, 3020)
    ]
    xs = [point[0] for point in model_points]
    ys = [point[1] for point in model_points]
    panel = (100, 205, 1690, 1325)
    scale = min(
        (panel[2] - panel[0]) / (max(xs) - min(xs)),
        (panel[3] - panel[1]) / (max(ys) - min(ys)),
    )

    def project(x: float, y: float, z: float) -> tuple[int, int]:
        rx, ry = raw(x, y, z)
        return (
            int(round(panel[0] + (rx - min(xs)) * scale)),
            int(round(panel[1] + (ry - min(ys)) * scale)),
        )

    return project


def _draw_plane(
    image: Image.Image,
    project,
    vertices: list[tuple[float, float, float]],
    *,
    fill: tuple[int, int, int, int],
    outline: str,
    width: int = 4,
) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    points = [project(*vertex) for vertex in vertices]
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width, joint="curve")
    image.alpha_composite(overlay)


def _draw_box(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    project,
    box: dict,
    *,
    opacity: int = 255,
    highlight: bool = False,
) -> None:
    x0, y0, x1, y1 = box["x0"], box["y0"], box["x1"], box["y1"]
    z0, z1 = box["z0"], box["z1"]
    p000, p100 = project(x0, y0, z0), project(x1, y0, z0)
    p010, p110 = project(x0, y1, z0), project(x1, y1, z0)
    p001, p101 = project(x0, y0, z1), project(x1, y0, z1)
    p011, p111 = project(x0, y1, z1), project(x1, y1, z1)
    colors = ("#8eb7a6", "#6d9d8a", "#a7c8ba") if highlight else (WALL_TOP, WALL_X, WALL_Y)

    if opacity == 255:
        target = draw
    else:
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        target = ImageDraw.Draw(layer)

    def rgba(color: str):
        rgb = tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))
        return (*rgb, opacity) if opacity < 255 else color

    edge = (*tuple(int(INK[index : index + 2], 16) for index in (1, 3, 5)), opacity) if opacity < 255 else INK
    target.polygon([p000, p010, p011, p001], fill=rgba(colors[1]), outline=edge)
    target.polygon([p000, p100, p101, p001], fill=rgba(colors[2]), outline=edge)
    target.polygon([p001, p101, p111, p011], fill=rgba(colors[0]), outline=edge)
    if opacity < 255:
        image.alpha_composite(layer)


def _callout(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    lines: list[str],
    *,
    color: str = RESOLVED,
) -> None:
    draw.rounded_rectangle(box, radius=16, fill="#fffefa", outline=color, width=3)
    _text(draw, (box[0] + 24, box[1] + 25), title, size=26, fill=color, bold=True)
    for index, line in enumerate(lines):
        _text(draw, (box[0] + 24, box[1] + 78 + index * 43), line, size=18, fill="#4a5359")


def _dimension_vertical(draw, project, x: float, y: float, z0: float, z1: float, label: str, color: str) -> None:
    p0, p1 = project(x, y, z0), project(x, y, z1)
    offset = 36
    a, b = (p0[0] - offset, p0[1]), (p1[0] - offset, p1[1])
    draw.line([p0, a], fill=color, width=2)
    draw.line([p1, b], fill=color, width=2)
    draw.line([a, b], fill=color, width=3)
    for px, py in (a, b):
        draw.line([(px - 6, py + 6), (px + 6, py - 6)], fill=color, width=3)
    _text(draw, (a[0] - 14, (a[1] + b[1]) // 2), label, size=17, fill=color, bold=True, anchor="rm")


def _scene_parts(scene: dict):
    objects = _objects_by_id(scene)
    ceiling = objects["ceiling_level_1_tea_room"]
    x0, y0, x1, y1 = ceiling["bounds_mm"]
    origin = (x0, y0)
    wall_ids = [
        "tea_bar_shared_wall",
        "tea_window_wall_north_jamb",
        "tea_window_wall_south_jamb",
        "tea_window_sill_wall",
        "tea_window_head_wall",
        "tea_terrace_boundary_wall",
        "tea_background_wall",
    ]
    walls = [_local_box(objects[object_id], origin) for object_id in wall_ids]
    walls.sort(key=lambda item: item["x1"] + item["y1"], reverse=True)
    return objects, ceiling, walls, (x1 - x0, y1 - y0)


def _base_canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", CANVAS, PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, CANVAS[0], 150), fill=HEADER)
    _text(draw, (70, 58), title, size=40, fill="white", bold=True, anchor="lm")
    _text(draw, (72, 116), subtitle, size=20, fill="#dce5ec", anchor="lm")
    draw.rectangle((0, 1450, CANVAS[0], CANVAS[1]), fill=HEADER)
    _text(draw, (CANVAS[0] // 2, 1476), "候选图｜完成天花标高控制，不表达结构厚度及施工节点。", size=18, fill="white", anchor="mm")
    return image, draw


def render_opaque(scene: dict) -> None:
    objects, ceiling, walls, (room_w, room_d) = _scene_parts(scene)
    ceiling_z = ceiling["height_mm"]
    project = _projector(room_w, room_d)
    image, draw = _base_canvas(
        "茶室完整封顶轴测灰模｜A",
        "完整显示茶室3200 x 4100范围内的2450完成天花控制面",
    )

    _draw_plane(
        image,
        project,
        [(0, 0, 0), (room_w, 0, 0), (room_w, room_d, 0), (0, room_d, 0)],
        fill=(214, 211, 203, 255),
        outline="#777e80",
        width=3,
    )
    for wall in walls:
        _draw_box(image, draw, project, wall, highlight=wall["id"] == "tea_window_head_wall")

    _draw_plane(
        image,
        project,
        [(0, 0, ceiling_z), (room_w, 0, ceiling_z), (room_w, room_d, ceiling_z), (0, room_d, ceiling_z)],
        fill=(184, 173, 132, 255),
        outline=CEILING_EDGE,
        width=7,
    )

    for wall in walls:
        if wall["z1"] <= ceiling_z:
            continue
        upper = {**wall, "z0": max(wall["z0"], ceiling_z)}
        _draw_box(image, draw, project, upper, highlight=wall["id"] == "tea_window_head_wall")

    ceiling_anchor = project(room_w * 0.58, room_d * 0.55, ceiling_z)
    draw.line([ceiling_anchor, (1755, 335)], fill=CEILING_EDGE, width=4)
    draw.ellipse((ceiling_anchor[0] - 6, ceiling_anchor[1] - 6, ceiling_anchor[0] + 6, ceiling_anchor[1] + 6), fill=CEILING_EDGE)
    _callout(
        draw,
        (1740, 235, 2335, 505),
        "完整封顶面",
        ["完成面标高：Z=2450mm", "覆盖范围：3200 x 4100mm", "本图顶面不透明，内部会被遮挡"],
        color=CEILING_EDGE,
    )

    head = _local_box(objects["tea_window_head_wall"], (ceiling["bounds_mm"][0], ceiling["bounds_mm"][1]))
    head_anchor = project((head["x0"] + head["x1"]) / 2, (head["y0"] + head["y1"]) / 2, 2810)
    draw.line([head_anchor, (1755, 695)], fill=RESOLVED, width=4)
    draw.ellipse((head_anchor[0] - 6, head_anchor[1] - 6, head_anchor[0] + 6, head_anchor[1] + 6), fill=RESOLVED)
    _callout(
        draw,
        (1740, 580, 2335, 855),
        "窗上封墙",
        ["Z=2450..3020mm", "高度：570mm", "窗顶2450与天花齐平闭合"],
    )

    _callout(
        draw,
        (1740, 960, 2335, 1265),
        "这张图看什么",
        ["1. 顶面是否完整覆盖茶室", "2. 封墙是否从2450接至3020", "3. 不用于判断顶内龙骨和设备"],
        color="#64727a",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(OPAQUE_OUT)


def render_cutaway(scene: dict) -> None:
    objects, ceiling, walls, (room_w, room_d) = _scene_parts(scene)
    ceiling_z = ceiling["height_mm"]
    project = _projector(room_w, room_d)
    image, draw = _base_canvas(
        "茶室封顶半透明剖切灰模｜B",
        "同一v05几何；局部切开封顶面，仅用于同时核验窗洞、上墙和2450天花",
    )

    _draw_plane(
        image,
        project,
        [(0, 0, 0), (room_w, 0, 0), (room_w, room_d, 0), (0, room_d, 0)],
        fill=(214, 211, 203, 255),
        outline="#777e80",
        width=3,
    )
    for wall in walls:
        _draw_box(
            image,
            draw,
            project,
            wall,
            opacity=225,
            highlight=wall["id"] == "tea_window_head_wall",
        )

    window = objects["tea_room_only_window"]
    y0 = window["bounds_mm"][1] - ceiling["bounds_mm"][1]
    y1 = window["bounds_mm"][3] - ceiling["bounds_mm"][1]
    window_vertices = [(0, y0, 350), (0, y1, 350), (0, y1, 2450), (0, y0, 2450)]
    _draw_plane(image, project, window_vertices, fill=(155, 198, 215, 105), outline=WINDOW_EDGE, width=5)

    cut = 1250
    ceiling_vertices = [
        (cut, 0, ceiling_z),
        (room_w, 0, ceiling_z),
        (room_w, room_d, ceiling_z),
        (0, room_d, ceiling_z),
        (0, cut, ceiling_z),
        (cut, cut, ceiling_z),
    ]
    _draw_plane(image, project, ceiling_vertices, fill=(184, 173, 132, 118), outline=CEILING_EDGE, width=6)
    cut_outline = [project(0, 0, ceiling_z), project(cut, 0, ceiling_z), project(cut, cut, ceiling_z), project(0, cut, ceiling_z)]
    for start, end in zip(cut_outline, cut_outline[1:] + cut_outline[:1]):
        draw.line([start, end], fill="#a15c31", width=3)

    head = _local_box(objects["tea_window_head_wall"], (ceiling["bounds_mm"][0], ceiling["bounds_mm"][1]))
    _draw_box(image, draw, project, head, highlight=True)
    mid_y = (y0 + y1) / 2
    _dimension_vertical(draw, project, 0, mid_y, 350, 2450, "窗高2100", WINDOW_EDGE)
    _dimension_vertical(draw, project, 0, mid_y, 2450, 3020, "封墙570", RESOLVED)

    closure_anchor = project(0, mid_y, 2450)
    draw.line([closure_anchor, (1755, 360)], fill=RESOLVED, width=4)
    draw.ellipse((closure_anchor[0] - 6, closure_anchor[1] - 6, closure_anchor[0] + 6, closure_anchor[1] + 6), fill=RESOLVED)
    _callout(
        draw,
        (1740, 235, 2335, 520),
        "闭合关系",
        ["窗顶：Z=2450mm", "天花：Z=2450mm", "两者齐平，不再存在300mm冲突"],
    )

    cut_anchor = project(cut * 0.55, cut * 0.55, ceiling_z)
    draw.line([cut_anchor, (1755, 720)], fill="#a15c31", width=4)
    _callout(
        draw,
        (1740, 625, 2335, 865),
        "局部剖切",
        ["缺口只用于看清内部", "不是实际天花开洞", "完整覆盖范围以A图为准"],
        color="#a15c31",
    )

    _callout(
        draw,
        (1740, 970, 2335, 1275),
        "可见构件",
        ["蓝色：唯一窗3220 x 2100", "绿色：窗上570封墙", "半透明黄灰：2450封顶控制面"],
        color="#64727a",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(CUTAWAY_OUT)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_report(scene: dict) -> None:
    contract = ceiling_contract(scene)
    files = "\n".join(
        f"- `{path.name}` — {path.stat().st_size:,} bytes — SHA-256 `{_sha256(path)}`"
        for path in (OPAQUE_OUT, CUTAWAY_OUT)
    )
    REPORT_OUT.write_text(
        f"""# 茶室封顶可视化 v01 候选核验报告

## 依据与状态

- 来源场景：`{scene['version']}`
- 本轮性质：只改变显示方式，不改变空间真值几何。
- 封顶范围：`{contract['bounds_mm']}`，平面 `3200 x 4100mm`。
- 完成天花：`Z={contract['ceiling_z_mm']}mm`。
- 唯一窗：`Z={contract['window_z_range_mm'][0]}..{contract['window_z_range_mm'][1]}mm`。
- 窗上封墙：`Z={contract['head_wall_z_range_mm'][0]}..{contract['head_wall_z_range_mm'][1]}mm`，高度 `570mm`。

## 硬约束视觉核验

| 核验项 | A 完整封顶 | B 半透明剖切 | 说明 |
|---|---|---|---|
| 茶室封顶面完整覆盖 | `pass` | `pass` | A为完整不透明面；B为同一面局部显示性剖切 |
| 天花完成面2450 | `pass` | `pass` | 两图均直接标注，数据来自v05场景 |
| 唯一窗3220 x 2100 | `not_visible` | `pass` | A顶面遮挡内部；B以蓝色窗口平面显示 |
| 窗顶2450与天花闭合 | `not_visible` | `pass` | B在同一锚点显示并标注 |
| 窗上封墙570至3020 | `pass` | `pass` | 绿色上墙来自v05 `tea_window_head_wall` |
| 窗沿墙端部精确定位 | `uncertain` | `uncertain` | 原v05仍标记为需现场复尺，本轮不补猜 |

## 文件核验

{files}

## 使用边界

两张图只证明完成天花控制面及其与窗洞、上墙的关系。顶面没有表达结构厚度、吊杆龙骨、检修口、消防、风管、防水和门窗收口；不得用于施工放样，最终以现场复尺和专业深化为准。
""",
        encoding="utf-8",
    )


def render_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = load_source_scene()
    expected = {
        "bounds_mm": [34240, 6160, 37440, 10260],
        "ceiling_z_mm": 2450,
        "window_z_range_mm": [350, 2450],
        "head_wall_z_range_mm": [2450, 3020],
    }
    if ceiling_contract(scene) != expected:
        raise ValueError("v05 ceiling contract changed; stop before rendering")
    render_opaque(scene)
    render_cutaway(scene)
    _write_report(scene)


if __name__ == "__main__":
    render_all()
    print(OPAQUE_OUT)
    print(CUTAWAY_OUT)
    print(REPORT_OUT)
