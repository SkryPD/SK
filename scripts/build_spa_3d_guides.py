import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.spa3d.geometry import build_model, validate_model
from src.spa3d.render_guides import render_axonometric, render_interior


def main():
    model = build_model()
    errors = validate_model(model)
    if errors:
        raise SystemExit("; ".join(errors))
    output_folder = PROJECT_ROOT / "output" / "3d"
    render_axonometric(
        model,
        output_folder / "spa-bright-natural-axonometric-guide.png",
    )
    render_interior(
        model,
        output_folder / "spa-bright-natural-interior-guide.png",
    )


if __name__ == "__main__":
    main()
