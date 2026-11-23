"""AC1 evidence: run the full chain 5 consecutive times against one stub instance.

Usage: .venv/bin/python scripts/run_5x.py [--runs 5]
Writes reports/chain_5x_summary.json + reports/chain_5x_run<i>.json and prints a table.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.harness import stub_server          # noqa: E402
from chain.runner import ChainRunner         # noqa: E402

REPORTS = ROOT / "reports"
RUNTIME = REPORTS / "_runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--skip-mini", action="store_true",
                    default=os.getenv("SKIP_MINI") == "1",
                    help="跳过小程序两步（也认环境变量 SKIP_MINI=1）")
    args = ap.parse_args()

    runs = []
    suffix = "_skip_mini" if args.skip_mini else ""
    with stub_server() as base_url:
        for i in range(1, args.runs + 1):
            t0 = time.perf_counter()
            report = ChainRunner(base_url, skip_mini=args.skip_mini,
                                 run_tag=f"5x-{i}").run()
            wall = round(time.perf_counter() - t0, 1)
            (RUNTIME / f"chain_5x_run{i}{suffix}.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            passed = sum(1 for s in report["steps"] if s["status"] == "passed")
            runs.append({
                "run": i, "run_id": report["run_id"], "ok": report["ok"],
                "passed_steps": passed, "total_steps": len(report["steps"]),
                "chain_ms": report["total_ms"], "wall_s": wall,
                "failed_step": report.get("failed_step"),
                "leftover_after_cleanup": report["counts_after_cleanup"]["total"],
            })
            print(f"run {i}: ok={report['ok']} steps={passed}/{len(report['steps'])} "
                  f"chain={report['total_ms'] / 1000:.1f}s leftover={runs[-1]['leftover_after_cleanup']}")

    ok = all(r["ok"] for r in runs)
    chain_times = [r["chain_ms"] for r in runs]
    summary = {
        "runs": runs,
        "all_passed": ok,
        "attempts": args.runs,
        "avg_chain_ms": round(statistics.mean(chain_times), 1),
        "max_chain_ms": max(chain_times),
        "avg_chain_seconds": round(statistics.mean(chain_times) / 1000, 2),
        "under_10_minutes": statistics.mean(chain_times) <= 600_000,
        "leftover_total": sum(r["leftover_after_cleanup"] for r in runs),
        "skip_mini": args.skip_mini,
    }
    (RUNTIME / f"chain_5x_summary{suffix}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 5x summary ===")
    for r in runs:
        print(f"#{r['run']}  {r['run_id']}  ok={r['ok']}  "
              f"{r['chain_ms'] / 1000:6.1f}s  steps={r['passed_steps']}/{r['total_steps']}")
    print(f"all_passed={ok}  avg={summary['avg_chain_seconds']}s  "
          f"max={summary['max_chain_ms'] / 1000:.1f}s  "
          f"leftover={summary['leftover_total']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
