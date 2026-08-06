from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from terranode.terranode.program10_human_coordination import Program10Result, run_program10_study


def build() -> Program10Result:
    return run_program10_study(Path(__file__).resolve().parents[1])

