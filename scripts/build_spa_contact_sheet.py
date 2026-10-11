import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.spa3d.contact_sheet import build_contact_sheet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--axonometric", required=True)
    parser.add_argument("--interior", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build_contact_sheet(
        args.axonometric,
        args.interior,
        args.out,
        "完整区域拆顶轴测",
        "同模型室内透视｜灯具 B",
    )


if __name__ == "__main__":
    main()
