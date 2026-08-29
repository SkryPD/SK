import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .geometry import CEILING_HEIGHT, WALL_HEIGHT_CUTAWAY


CANVAS = (2048, 1152)
BG = (244, 241, 234)
INK = (48, 48, 45)
WALL = (221, 216, 205)
STONE = (208, 202, 191)
WATER = (125, 182, 184)
GREEN = (100, 137, 92)
WOOD = (174, 132, 91)


def _font(size=30):
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _iso(x_mm, y_mm, z_mm, origin=(1000, 260), scale=0.040):
    x, y, z = x_mm * scale, y_mm * scale, z_mm * scale
    return (
        origin[0] + (x - y) * math.cos(math.radians(30)),
        origin[1] + (x + y) * math.sin(math.radians(30)) - z,
    )


def _rect_poly(rect, z=0):
    return [
        _iso(rect.x, rect.y, z),
        _iso(rect.right, rect.y, z),
        _iso(rect.right, rect.bottom, z),
        _iso(rect.x, rect.bottom, z),
    ]


def _draw_iso_box(draw, rect, height, top_fill, side_fill):
    base = _rect_poly(rect, 0)
    top = _rect_poly(rect, height)
    for first, second in ((0, 1), (1, 2), (2, 3), (3, 0)):
        draw.polygon(
            [base[first], base[second], top[second], top[first]],
            fill=side_fill,
            outline=INK,
            width=2,
        )
    draw.polygon(top, fill=top_fill, outline=INK, width=3)


def render_axonometric(model, output_path):
    image = Image.new("RGB", CANVAS, BG)
    draw = ImageDraw.Draw(image)

    # Floor plates are drawn south-to-north so the cutaway reads as one model.
    floor_names = [
        "female_planter",
        "female_bath",
        "female_support",
        "green_divider",
        "male_planter",
        "male_bath",
        "male_support",
        "equipment",
    ]
    for name in floor_names:
        rect = model[name]
        color = GREEN if "green" in name or "planter" in name else STONE
        draw.polygon(_rect_poly(rect), fill=color, outline=INK, width=3)

    # The equipment room is intentionally only an exterior mass.
    _draw_iso_box(draw, model["equipment"], WALL_HEIGHT_CUTAWAY, WALL, (198, 194, 185))

    for name in ("male_pool", "female_pool"):
        rect = model[name]
        rim = _rect_poly(rect, 80)
        draw.line(rim + [rim[0]], fill=(245, 239, 225), width=18, joint="curve")
        draw.polygon(rim, fill=WATER, outline=INK, width=4)
        inner = [
            _iso(rect.x + 350, rect.y + 350, 90),
            _iso(rect.right - 350, rect.y + 350, 90),
            _iso(rect.right - 350, rect.bottom - 350, 90),
            _iso(rect.x + 350, rect.bottom - 350, 90),
        ]
        draw.line(inner + [inner[0]], fill=(207, 234, 230), width=5)

    # Cutaway wall frames communicate enclosure without hiding the plan.
    for name in ("male_support", "male_bath", "female_support", "female_bath"):
        rect = model[name]
        base = _rect_poly(rect)
        top = _rect_poly(rect, WALL_HEIGHT_CUTAWAY)
        for i in range(4):
            j = (i + 1) % 4
            draw.line([base[i], top[i]], fill=INK, width=3)
            draw.line([top[i], top[j]], fill=INK, width=3)

    # Door markers use the same model entries as the interior camera logic.
    for name in ("male_entry", "female_entry", "male_bath_door", "female_bath_door"):
        opening = model[name]
        center = _iso(
            opening.x + opening.width / 2,
            opening.y + opening.height / 2,
            110,
        )
        draw.ellipse(
            (center[0] - 8, center[1] - 8, center[0] + 8, center[1] + 8),
            fill=(244, 187, 85),
            outline=INK,
            width=2,
        )

    label_font = _font(30)
    small_font = _font(21)
    labels = {
        "male_bath": "男汤",
        "female_bath": "女汤",
        "male_support": "男汤过渡/洗浴",
        "female_support": "女汤过渡/洗浴",
        "equipment": "设备房外壳",
    }
    for name, label in labels.items():
        rect = model[name]
        px = _iso(rect.x + rect.width / 2, rect.y + rect.height / 2, 180)
        draw.text(
            px,
            label,
            font=label_font if "汤" in label and "/" not in label else small_font,
            fill=INK,
            anchor="mm",
            stroke_width=3,
            stroke_fill=BG,
        )

    draw.text((72, 62), "汤泉完整区域｜拆顶轴测几何控制图", font=_font(38), fill=INK)
    draw.text(
        (74, 116),
        "同一毫米制母版 · 橙点为入口/门洞 · 墙高仅作拆顶表达",
        font=_font(22),
        fill=(86, 82, 75),
    )
    draw.rounded_rectangle((72, 1010, 815, 1088), radius=18, fill=(252, 249, 242), outline=(185, 178, 165), width=2)
    draw.text(
        (94, 1030),
        "两座池：8180 × 4240 mm｜隔离绿带：140 mm",
        font=_font(22),
        fill=INK,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def _camera_project(point, camera, target, focal=1050):
    px, py, pz = (value / 1000 for value in point)
    cx, cy, cz = (value / 1000 for value in camera)
    tx, ty, tz = (value / 1000 for value in target)
    forward = (tx - cx, ty - cy, tz - cz)
    forward_length = math.sqrt(sum(value * value for value in forward))
    forward = tuple(value / forward_length for value in forward)
    right = (forward[1], -forward[0], 0.0)
    right_length = math.sqrt(sum(value * value for value in right))
    right = tuple(value / right_length for value in right)
    up = (
        right[1] * forward[2],
        -right[0] * forward[2],
        right[0] * forward[1] - right[1] * forward[0],
    )
    delta = (px - cx, py - cy, pz - cz)
    depth = max(0.2, sum(delta[index] * forward[index] for index in range(3)))
    screen_x = sum(delta[index] * right[index] for index in range(3))
    screen_y = sum(delta[index] * up[index] for index in range(3))
    return 1024 + focal * screen_x / depth, 605 - focal * screen_y / depth


def render_interior(model, output_path):
    image = Image.new("RGB", CANVAS, (234, 229, 219))
    draw = ImageDraw.Draw(image)
    camera = (4050, 3290, 1600)
    target = (11000, 3290, 1150)
    project = lambda point: _camera_project(point, camera, target)
    bath = model["male_bath"]
    pool = model["male_pool"]

    near_x = bath.x
    far_x = bath.right
    north_y = bath.y
    south_y = bath.bottom

    far_wall = [
        (far_x, north_y, 0),
        (far_x, south_y, 0),
        (far_x, south_y, CEILING_HEIGHT),
        (far_x, north_y, CEILING_HEIGHT),
    ]
    north_wall = [
        (near_x, north_y, 0),
        (far_x, north_y, 0),
        (far_x, north_y, CEILING_HEIGHT),
        (near_x, north_y, CEILING_HEIGHT),
    ]
    south_wall = [
        (near_x, south_y, 0),
        (far_x, south_y, 0),
        (far_x, south_y, CEILING_HEIGHT),
        (near_x, south_y, CEILING_HEIGHT),
    ]
    ceiling = [
        (near_x, north_y, CEILING_HEIGHT),
        (far_x, north_y, CEILING_HEIGHT),
        (far_x, south_y, CEILING_HEIGHT),
        (near_x, south_y, CEILING_HEIGHT),
    ]
    floor = [
        (near_x, north_y, 0),
        (far_x, north_y, 0),
        (far_x, south_y, 0),
        (near_x, south_y, 0),
    ]

    draw.polygon([project(point) for point in far_wall], fill=(204, 216, 194), outline=INK)
    draw.polygon([project(point) for point in ceiling], fill=(188, 151, 111), outline=INK)
    draw.polygon([project(point) for point in north_wall], fill=(225, 220, 210), outline=INK)
    draw.polygon([project(point) for point in south_wall], fill=(218, 214, 205), outline=INK)
    draw.polygon([project(point) for point in floor], fill=STONE, outline=INK)

    # Ceiling slats are architectural cues; their endpoints use the same shell.
    for y in range(250, 6580, 420):
        draw.line(
            [project((near_x, y, CEILING_HEIGHT - 15)), project((far_x, y, CEILING_HEIGHT - 15))],
            fill=(116, 87, 61),
            width=3,
        )

    # Pool coping and water plane preserve the master-model footprint.
    water = [
        (pool.x, pool.y, 40),
        (pool.right, pool.y, 40),
        (pool.right, pool.bottom, 40),
        (pool.x, pool.bottom, 40),
    ]
    coping = [project(point) for point in water]
    draw.line(coping + [coping[0]], fill=(245, 238, 222), width=24, joint="curve")
    draw.polygon(coping, fill=WATER, outline=INK, width=5)
    for fraction in (0.25, 0.5, 0.75):
        x = pool.x + pool.width * fraction
        draw.line(
            [project((x, pool.y + 220, 50)), project((x, pool.bottom - 220, 50))],
            fill=(181, 218, 215),
            width=3,
        )

    # Wet-area globe lights and restrained end planting express Scheme C.
    for x in (6800, 8900, 11000, 12800):
        center = project((x, north_y + 15, 2050))
        radius = max(8, int(34 - (x - near_x) / 420))
        draw.ellipse(
            (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
            fill=(255, 245, 211),
            outline=(104, 93, 73),
            width=2,
        )
    planter = [
        (far_x - 120, 2500, 0),
        (far_x - 120, 4080, 0),
        (far_x - 120, 4080, 820),
        (far_x - 120, 2500, 820),
    ]
    draw.polygon([project(point) for point in planter], fill=GREEN, outline=INK, width=3)

    draw.rounded_rectangle((48, 40, 765, 145), radius=18, fill=(250, 247, 240), outline=(184, 176, 162), width=2)
    draw.text((72, 58), "男汤｜同模型室内透视控制图", font=_font(30), fill=INK)
    draw.text(
        (72, 103),
        "西侧入口向东 · 全室内封闭 · 净高暂定 3.2 m",
        font=_font(19),
        fill=(82, 78, 72),
    )
    draw.text(
        (72, 1083),
        "浅暖防滑石材｜木纹线性顶｜浅绿端景｜池体 8180 × 4240 mm",
        font=_font(21),
        fill=INK,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
