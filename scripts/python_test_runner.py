from __future__ import annotations

import importlib.util
import inspect
import sys
import unittest
from collections.abc import Iterable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUNCTION_TEST_PATHS = (
    ROOT / "tmp" / "geometry" / "test_render_rooftop_whole_floor_truth_model_v05.py",
    ROOT / "tmp" / "geometry" / "test_render_rooftop_ceiling_visibility_v01.py",
)


def _load_module(path: Path, index: int):
    module_name = f"tracked_geometry_test_{index}_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Python test module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_function_tests(
    paths: Iterable[Path] = FUNCTION_TEST_PATHS,
) -> list[unittest.FunctionTestCase]:
    cases: list[unittest.FunctionTestCase] = []
    for index, path in enumerate(paths):
        if not path.is_file():
            raise FileNotFoundError(f"Tracked Python test file is missing: {path}")
        module = _load_module(path, index)
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_") or inspect.signature(function).parameters:
                continue
            cases.append(
                unittest.FunctionTestCase(
                    function,
                    description=f"{path.name}::{name}",
                )
            )
    return cases


def build_suite() -> unittest.TestSuite:
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    suite = unittest.TestSuite()
    suite.addTests(
        unittest.defaultTestLoader.discover(
            start_dir=str(ROOT / "tests"),
            pattern="test_*.py",
        )
    )
    suite.addTests(discover_function_tests())
    return suite


def main() -> int:
    result = unittest.TextTestRunner(verbosity=2).run(build_suite())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
