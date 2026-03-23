#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from opentrons_lab_agent.robot_api import main


if __name__ == "__main__":
    raise SystemExit(main())

