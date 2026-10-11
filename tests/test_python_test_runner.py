from __future__ import annotations

import importlib.util
import inspect
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "python_test_runner.py"
REQUIREMENTS_PATH = ROOT / "requirements.txt"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "verify.yml"
FUNCTION_TEST_PATHS = (
    ROOT / "tmp" / "geometry" / "test_render_rooftop_whole_floor_truth_model_v05.py",
    ROOT / "tmp" / "geometry" / "test_render_rooftop_ceiling_visibility_v01.py",
)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PythonTestRunnerTests(unittest.TestCase):
    def test_runner_discovers_every_tracked_function_style_geometry_test(self) -> None:
        self.assertTrue(RUNNER_PATH.exists(), "unified Python test runner is missing")
        runner = load_module(RUNNER_PATH, "python_test_runner_under_test")

        expected = set()
        for index, path in enumerate(FUNCTION_TEST_PATHS):
            module = load_module(path, f"expected_geometry_tests_{index}")
            expected.update(
                f"{path.name}::{name}"
                for name, function in inspect.getmembers(module, inspect.isfunction)
                if name.startswith("test_") and not inspect.signature(function).parameters
            )

        discovered = {
            case.shortDescription()
            for case in runner.discover_function_tests(FUNCTION_TEST_PATHS)
        }

        self.assertEqual(discovered, expected)
        self.assertGreaterEqual(len(discovered), 7)

    def test_runner_builds_the_complete_suite_from_a_non_package_tests_directory(self) -> None:
        self.assertTrue(RUNNER_PATH.exists(), "unified Python test runner is missing")
        runner = load_module(RUNNER_PATH, "python_test_runner_suite_under_test")

        suite = runner.build_suite()

        self.assertGreaterEqual(suite.countTestCases(), 31)

    def test_requirements_pin_the_verified_python_test_dependencies(self) -> None:
        self.assertTrue(REQUIREMENTS_PATH.exists(), "requirements.txt is missing")
        requirements = {
            line.strip()
            for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
        self.assertEqual(
            requirements,
            {
                "numpy==2.3.5",
                "Pillow==12.3.0",
                "python-docx==1.2.0",
            },
        )

    def test_github_workflow_runs_the_repository_verification_entrypoints(self) -> None:
        self.assertTrue(WORKFLOW_PATH.exists(), "GitHub verification workflow is missing")
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for required_command in (
            "python -m pip install -r requirements.txt",
            "npm ci --prefix tools/rooftop3d-web",
            "python scripts/python_test_runner.py",
            "node --test tests/*.mjs",
            "python -m compileall -q scripts tests tmp/geometry",
            "git diff --check",
        ):
            with self.subTest(command=required_command):
                self.assertIn(required_command, workflow)


if __name__ == "__main__":
    unittest.main()
