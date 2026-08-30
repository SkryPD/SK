import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SpaPromptTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / "prompts" / name).read_text(encoding="utf-8")

    def test_axonometric_prompt_locks_layout_and_style(self):
        text = self.read("spa-bright-natural-axonometric.txt")
        for required in (
            "8180 by 4240 mm",
            "male bath on the north",
            "female bath on the south",
            "exactly one four-seat round table",
            "storage along the outer wall",
            "full-height glass partition",
            "physical moisture-resistant door",
            "fully enclosed",
            "4000K",
            "no benches",
            "no water curtain",
        ):
            self.assertIn(required, text)
        self.assertIn("Image 1 is the sole furniture-layout authority", text)
        self.assertIn("Image 1 is the sole geometry authority", text)
        self.assertIn("Image 2 is style-only", text)
        self.assertNotIn("layout annotation", text)
        self.assertNotIn("legacy furniture symbols", text)

    def test_interior_a_prompt_locks_confirmed_finish_package(self):
        text = self.read("spa-bright-natural-interior-a.txt")
        for required in (
            "pale cool gray-beige",
            "pale gray-white oak",
            "about 10 percent",
            "opal globe",
            "4000K",
            "shallow relief feature wall",
            "one moisture-tolerant plant",
            "no water curtain",
            "no warm-yellow layer",
        ):
            self.assertIn(required, text)
        self.assertIn("Image 1 is the sole camera and visible-geometry authority", text)
        self.assertIn("Image 2 is the accepted revised axonometric", text)
        self.assertIn("Image 3 is style-only", text)
        self.assertNotIn("Image 4", text)
        self.assertNotIn("authoritative floor plan", text)

    def test_fixture_b_prompt_changes_only_lighting_system(self):
        text = self.read("spa-bright-natural-fixture-b.txt")
        self.assertIn("remove only the opal globe wall lights", text)
        self.assertIn("trimless recessed wet-area downlights", text)
        self.assertIn("keep every other pixel-space relationship unchanged", text)
        self.assertIn("4000K", text)


if __name__ == "__main__":
    unittest.main()
