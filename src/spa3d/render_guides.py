import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .geometry import CEILING_HEIGHT, WALL_HEIGHT_CUTAWAY


CANVAS = (2048, 1152)
BG = (242, 243, 241)
INK = (49, 52, 50)
WALL = (226, 227, 223)
STONE = (216, 218, 215)
WATER = (164, 201, 207)
GREEN = (126, 145, 126)
WOOD = (196, 191, 181)
TABLE_GUIDE = (166, 151, 136)
CHAIR_GUIDE = (239, 236, 229)
GLASS = (190, 218, 224)
LIGHT_4000K = (245, 247, 242)


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


def _ellipse_for_circle(circle, z=0):
    left = _iso(circle.x - circle.radius, circle.y, z)
    right = _iso(circle.x + circle.radius, circle.y, z)
    top = _iso(circle.x, circle.y - circle.radius, z)
    bottom = _iso(circle.x, circle.y + circle.radius, z)
    return (
        min(left[0], right[0], top[0], bottom[0]),
        min(left[1], right[1], top[1], bottom[1]),
        max(left[0], right[0], top[0], bottom[0]),
        max(left[1], right[1], top[1], bottom[1]),
    )


def _draw_furniture_iso(draw, model, zone):
    storage = model[f"{zone}_storage"]
    _draw_iso_box(draw, storage, 1900, WOOD, (173, 170, 162))
    table = model[f"{zone}_table"]
    draw.ellipse(
        _ellipse_for_circle(table, 740),
        fill=TABLE_GUIDE,
        outline=INK,
        width=5,
    )
    for chair in model[f"{zone}_chairs"]:
        draw.polygon(
            _rect_poly(chair, 460),
            fill=CHAIR_GUIDE,
            outline=INK,
            width=4,
        )


def _draw_partition_iso(draw, model, zone):
    for suffix in ("glass_north", "glass_south"):
        panel = model[f"{zone}_{suffix}"]
        base = _rect_poly(panel, 0)
        top = _rect_poly(panel, CEILING_HEIGHT)
        draw.polygon(
            [base[0], base[3], top[3], top[0]],
            fill=GLASS,
            outline=INK,
            width=2,
        )
    door = model[f"{zone}_bath_door"]
    _draw_iso_box(draw, door, 2200, (210, 211, 205), (184, 185, 180))


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

    for zone in ("male", "female"):
        _draw_partition_iso(draw, model, zone)
        _draw_furniture_iso(draw, model, zone)

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

    draw.text((72, 62), "汤泉完整区域｜新版拆顶轴测几何控制图", font=_font(38), fill=INK)
    draw.text(
        (74, 116),
        "同一毫米制母版 · 外墙单组四人桌椅/储物柜 · 通高玻璃＋实体门",
        font=_font(22),
        fill=(86, 89, 86),
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
    image = Image.new("RGB", CANVAS, BG)
    draw = ImageDraw.Draw(image)
    camera = (-900, 3290, 1600)
    target = (8800, 2700, 1200)
    project = lambda point: _camera_project(point, camera, target)
    support = model["male_support"]
    bath = model["male_bath"]
    pool = model["male_pool"]

    near_x = support.x
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

    draw.polygon([project(point) for point in far_wall], fill=WALL, outline=INK)
    draw.polygon([project(point) for point in ceiling], fill=WOOD, outline=INK)
    draw.polygon([project(point) for point in north_wall], fill=WALL, outline=INK)
    draw.polygon([project(point) for point in south_wall], fill=(219, 221, 217), outline=INK)
    draw.polygon([project(point) for point in floor], fill=STONE, outline=INK)

    # Ceiling slats are architectural cues; their endpoints use the same shell.
    for y in range(250, 6580, 420):
        draw.line(
            [project((near_x, y, CEILING_HEIGHT - 15)), project((far_x, y, CEILING_HEIGHT - 15))],
            fill=(143, 140, 133),
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

    storage = model["male_storage"]
    storage_face = [
        (storage.x, storage.bottom, 0),
        (storage.right, storage.bottom, 0),
        (storage.right, storage.bottom, 1900),
        (storage.x, storage.bottom, 1900),
    ]
    draw.polygon(
        [project(point) for point in storage_face],
        fill=WOOD,
        outline=INK,
        width=3,
    )

    table = model["male_table"]
    table_center = project((table.x, table.y, 740))
    draw.ellipse(
        (
            table_center[0] - 70,
            table_center[1] - 30,
            table_center[0] + 70,
            table_center[1] + 30,
        ),
        fill=WOOD,
        outline=INK,
        width=3,
    )
    for chair in model["male_chairs"]:
        draw.polygon(
            [
                project(point)
                for point in (
                    (chair.x, chair.y, 460),
                    (chair.right, chair.y, 460),
                    (chair.right, chair.bottom, 460),
                    (chair.x, chair.bottom, 460),
                )
            ],
            fill=(205, 207, 201),
            outline=INK,
            width=2,
        )

    for suffix in ("glass_north", "glass_south"):
        panel = model[f"male_{suffix}"]
        polygon = [
            (panel.x, panel.y, 0),
            (panel.x, panel.bottom, 0),
            (panel.x, panel.bottom, CEILING_HEIGHT),
            (panel.x, panel.y, CEILING_HEIGHT),
        ]
        draw.line(
            [project(point) for point in polygon + [polygon[0]]],
            fill=(112, 154, 164),
            width=4,
        )

    # Confirmed lighting option A: a restrained run of same-size 4000K globes.
    for x in (7600, 10100, 12600):
        center = project((x, north_y + 15, 2050))
        radius = 15
        draw.ellipse(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            fill=LIGHT_4000K,
            outline=(116, 119, 114),
            width=2,
        )

    # Neutral shallow-relief end wall with 4000K washing and one plant placeholder.
    relief_x = far_x - 35
    for y in range(800, 5600, 360):
        draw.line(
            [
                project((relief_x, y, 450)),
                project((relief_x, y + 220, 2400)),
            ],
            fill=(202, 204, 200),
            width=2,
        )
    draw.line(
        [
            project((far_x - 20, north_y + 300, 2800)),
            project((far_x - 20, south_y - 300, 2800)),
        ],
        fill=LIGHT_4000K,
        width=8,
    )
    plant_pot = [
        (far_x - 120, 4880, 0),
        (far_x - 120, 5480, 0),
        (far_x - 120, 5480, 700),
        (far_x - 120, 4880, 700),
    ]
    draw.polygon(
        [project(point) for point in plant_pot],
        fill=GREEN,
        outline=INK,
        width=3,
    )

    draw.rounded_rectangle((48, 40, 765, 145), radius=18, fill=(250, 247, 240), outline=(184, 176, 162), width=2)
    draw.text((72, 58), "男汤｜同模型室内透视控制图", font=_font(30), fill=INK)
    draw.text(
        (72, 103),
        "男汤过渡区向东 · 全室内封闭 · 净高暂定 3.2 m",
        font=_font(19),
        fill=(82, 78, 72),
    )
    draw.text(
        (72, 1083),
        "浅冷灰米白防滑面｜浅灰白橡木｜全 4000K｜灰绿约 10%｜无水帘",
        font=_font(21),
        fill=INK,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
