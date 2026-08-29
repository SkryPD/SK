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


if __name__ == "__main__":
    unittest.main()
