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
    return errors
