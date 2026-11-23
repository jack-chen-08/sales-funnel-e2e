#!/usr/bin/env python3
"""AC3 取证辅助：跑一条完整链但保留数据（SMOKE_KEEP_DATA=1），打印 run_id。

配合 scripts/cleanup_proof.sh 使用：先直查数据库拿到「清理前」行数，
再调 DELETE 接口按 run_id 清理，最后直查「清理后」行数必须为 0。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.core.runner import run_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:5600"))
    parser.add_argument("--run-tag", default="ac3-before")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    import datetime as dt
    import uuid

    run_id = args.run_id or f"smk-{args.run_tag}-{dt.datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"
    _runner, report, failure = run_chain(args.base_url, run_id, skip_miniprogram=True, scenario="cleanup-proof")

    print(f"RUN_ID={run_id}")
    print(f"status={report['status']} passed={report['counts']['passed']} failed={report['counts']['failed']}")
    print(f"保留行数（清理前）={report['cleanup']['remaining_total']}")
    print(f"evidence={report['artifacts']['report_json']}")
    return 0 if failure is None and report["cleanup"]["remaining_total"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
