from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from terranode.terranode.program10_human_coordination import run_program10_study


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = run_program10_study(root)
    print(
        f"Program10 complete: scenario={result.scenario_id} "
        f"conflict={result.conflict_detected} "
        f"accuracy ordinary={result.ordinary_accuracy_mean:.2f} "
        f"terranode={result.terranode_accuracy_mean:.2f}"
    )


if __name__ == "__main__":
    main()
