from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int
    z: int = 0

    @property
    def size(self):
        return self.width, self.height

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def contains(self, other):
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def intersects(self, other):
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )


@dataclass(frozen=True)
class Circle:
    x: int
    y: int
    radius: int
    z: int = 0

    @property
    def center(self):
        return self.x, self.y

    @property
    def bounds(self):
        return Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
            self.z,
        )


CEILING_HEIGHT = 3200  # 设计暂定值，不是施工图尺寸
WALL_HEIGHT_CUTAWAY = 1700
WALL_THICKNESS = 140


def build_model():
    # 本地坐标：x 向东，y 向南；单位 mm。北侧设备房以负 y 表示。
    return {
        "equipment": Rect(0, -7260, 10000, 7260),
        "male_support": Rect(0, 0, 5038, 6580),
        "male_bath": Rect(5038, 0, 8680, 6580),
        "male_planter": Rect(13718, 0, 1000, 6580),
        "green_divider": Rect(5038, 6580, 9680, 140),
        "female_support": Rect(0, 6720, 5038, 6580),
        "female_bath": Rect(5038, 6720, 8680, 6580),
        "female_planter": Rect(13718, 6720, 1000, 6580),
        # 池体尺寸来自平面图；在各自 8680 x 6580 汤区内居中。
        "male_pool": Rect(5288, 1170, 8180, 4240, -600),
        "female_pool": Rect(5288, 7890, 8180, 4240, -600),
        # 门洞仅锁定概念平面位置，门洞高度留待专业深化。
        "male_entry": Rect(0, 2550, WALL_THICKNESS, 1480),
        "female_entry": Rect(0, 9270, WALL_THICKNESS, 1480),
        "male_bath_door": Rect(4898, 2550, 280, 1480),
        "female_bath_door": Rect(4898, 9270, 280, 1480),
        # 用户确认：每区一组四人桌椅，靠各自最外墙；无长凳。
        "male_table": Circle(3400, 1350, 450),
        "female_table": Circle(3400, 11950, 450),
        "male_chairs": (
            Rect(3150, 450, 500, 500),
            Rect(3150, 1750, 500, 500),
            Rect(2500, 1100, 500, 500),
            Rect(3800, 1100, 500, 500),
        ),
        "female_chairs": (
            Rect(3150, 11050, 500, 500),
            Rect(3150, 12350, 500, 500),
            Rect(2500, 11700, 500, 500),
            Rect(3800, 11700, 500, 500),
        ),
        # 浅灰白橡木储物柜；520 mm 为概念进深，须在施工深化中复核。
        "male_storage": Rect(200, 140, 1500, 520),
        "female_storage": Rect(200, 12640, 1500, 520),
        "male_storage_clearance": Rect(200, 660, 1500, 700),
        "female_storage_clearance": Rect(200, 11940, 1500, 700),
        # 中央入口—洗手—汤池主通道必须保持空出。
        "male_main_route": Rect(0, 2550, 5038, 1480),
        "female_main_route": Rect(0, 9270, 5038, 1480),
        # 通高玻璃隔断位于过渡区与汤池区交界，门洞内为防潮实体门。
        "male_glass_north": Rect(4898, 0, 140, 2550),
        "male_glass_south": Rect(4898, 4030, 140, 2550),
        "female_glass_north": Rect(4898, 6720, 140, 2550),
        "female_glass_south": Rect(4898, 10750, 140, 2550),
    }


def validate_model(model):
    errors = []
    for pool_name, bath_name in (
        ("male_pool", "male_bath"),
        ("female_pool", "female_bath"),
    ):
        pool = model[pool_name]
        bath = model[bath_name]
        if pool.size != (8180, 4240):
            errors.append(f"{pool_name} dimension drift")
        if not bath.contains(pool):
            errors.append(f"{pool_name} outside {bath_name}")
        if (
            pool.x - bath.x != bath.right - pool.right
            or pool.y - bath.y != bath.bottom - pool.bottom
        ):
            errors.append(f"{pool_name} not centered in {bath_name}")
    if model["green_divider"].height != 140:
        errors.append("green divider dimension drift")
    if model["equipment"].bottom != 0:
        errors.append("equipment room must adjoin north edge")
    if model["female_support"].y != model["green_divider"].bottom:
        errors.append("female zone must adjoin divider")
    for zone in ("male", "female"):
        route = model[f"{zone}_main_route"]
        furniture = [
            model[f"{zone}_storage"],
            model[f"{zone}_storage_clearance"],
            model[f"{zone}_table"].bounds,
            *model[f"{zone}_chairs"],
        ]
        if any(route.intersects(item) for item in furniture):
            errors.append(f"{zone} main route blocked")
        storage = model[f"{zone}_storage"]
        leftmost_chair = min(chair.x for chair in model[f"{zone}_chairs"])
        if leftmost_chair - storage.right < 800:
            errors.append(f"{zone} storage seating clearance below 800 mm")
        north = model[f"{zone}_glass_north"]
        door = model[f"{zone}_bath_door"]
        south = model[f"{zone}_glass_south"]
        if north.bottom != door.y or south.y != door.bottom:
            errors.append(f"{zone} glass partition does not frame door")
    if any("bench" in name for name in model):
        errors.append("bench must not exist in revised model")
    return errors
