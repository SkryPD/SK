import unittest

from src.spa3d.geometry import build_model, validate_model


class SpaGeometryTests(unittest.TestCase):
    def setUp(self):
        self.model = build_model()

    def test_drawing_dimensions_are_preserved(self):
        self.assertEqual(self.model["male_pool"].size, (8180, 4240))
        self.assertEqual(self.model["female_pool"].size, (8180, 4240))
        self.assertEqual(self.model["equipment"].size, (10000, 7260))

    def test_bath_zones_and_support_zones_are_separate(self):
        self.assertEqual(self.model["male_support"].size, (5038, 6580))
        self.assertEqual(self.model["female_support"].size, (5038, 6580))
        self.assertEqual(self.model["male_bath"].size, (8680, 6580))
        self.assertEqual(self.model["female_bath"].size, (8680, 6580))
        self.assertEqual(self.model["green_divider"].height, 140)

    def test_pools_fit_inside_their_bath_zones(self):
        self.assertTrue(self.model["male_bath"].contains(self.model["male_pool"]))
        self.assertTrue(self.model["female_bath"].contains(self.model["female_pool"]))

    def test_pools_are_centered_in_each_bath_zone(self):
        for bath_name, pool_name in (
            ("male_bath", "male_pool"),
            ("female_bath", "female_pool"),
        ):
            bath = self.model[bath_name]
            pool = self.model[pool_name]
            self.assertEqual(pool.x - bath.x, 250)
            self.assertEqual(pool.y - bath.y, 1170)
            self.assertEqual(bath.right - pool.right, 250)
            self.assertEqual(bath.bottom - pool.bottom, 1170)

    def test_model_validation_has_no_errors(self):
        self.assertEqual(validate_model(self.model), [])

    def test_one_four_seat_group_per_support_zone(self):
        self.assertEqual(self.model["male_table"].center, (3400, 1350))
        self.assertEqual(self.model["female_table"].center, (3400, 11950))
        self.assertEqual(len(self.model["male_chairs"]), 4)
        self.assertEqual(len(self.model["female_chairs"]), 4)

    def test_storage_follows_confirmed_outer_walls(self):
        male = self.model["male_storage"]
        female = self.model["female_storage"]
        self.assertEqual(male.y, self.model["male_support"].y + 140)
        self.assertEqual(female.bottom, self.model["female_support"].bottom - 140)
        self.assertEqual(male.size, (1500, 520))
        self.assertEqual(female.size, (1500, 520))

    def test_storage_and_seating_keep_main_routes_clear(self):
        for zone in ("male", "female"):
            route = self.model[f"{zone}_main_route"]
            self.assertFalse(route.intersects(self.model[f"{zone}_storage"]))
            self.assertFalse(route.intersects(self.model[f"{zone}_storage_clearance"]))
            self.assertFalse(route.intersects(self.model[f"{zone}_table"].bounds))
            for chair in self.model[f"{zone}_chairs"]:
                self.assertFalse(route.intersects(chair))

    def test_glass_partition_frames_physical_door(self):
        for zone in ("male", "female"):
            north = self.model[f"{zone}_glass_north"]
            door = self.model[f"{zone}_bath_door"]
            south = self.model[f"{zone}_glass_south"]
            self.assertEqual(north.bottom, door.y)
            self.assertEqual(south.y, door.bottom)
            self.assertEqual(north.x, 4898)
            self.assertEqual(south.x, 4898)
            self.assertEqual(north.width, 140)
            self.assertEqual(south.width, 140)

    def test_model_contains_no_bench(self):
        self.assertFalse(any("bench" in name for name in self.model))

    def test_confirmed_furniture_clearance_is_preserved(self):
        for zone in ("male", "female"):
            storage = self.model[f"{zone}_storage"]
            leftmost_chair = min(chair.x for chair in self.model[f"{zone}_chairs"])
            self.assertGreaterEqual(leftmost_chair - storage.right, 800)


if __name__ == "__main__":
    unittest.main()
