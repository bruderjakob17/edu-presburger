from __future__ import annotations

import argparse
import concurrent.futures as cf
import multiprocessing as mp
import os
import time
from pathlib import Path
from typing import List, Tuple, Literal

import pandas as pd
from presburger_converter import test_formula

Outcome = Literal["ok", "timeout", "error"]
Result = Tuple[float | None, int | None, Outcome]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def formula_worker(q, expr):
    try:
        start = time.perf_counter()
        dot_string, num_states = test_formula(expr)
        duration = (time.perf_counter() - start) * 1000
        q.put((duration, num_states))
    except Exception as e:
        print(f"Error processing {expr}: {e}")
        q.put(("n/a", "n/a"))

def run_formula_with_timeout(expr, timeout_sec):
    q = mp.Queue()
    p = mp.Process(target=formula_worker, args=(q, expr))
    p.start()
    p.join(timeout=timeout_sec)

    if p.is_alive():
        p.terminate()
        p.join()
        return "n/a", "n/a"

    if not q.empty():
        return q.get()
    else:
        return "n/a", "n/a"

def get_script_dir() -> Path:
    """Return the absolute directory containing this script."""
    return Path(__file__).resolve().parent


def _run_in_subprocess(expr: str, q: mp.Queue) -> None:  # type: ignore[type-arg]
    """Executes inside the disposable subprocess.  Sends the result back via *q*."""
    try:
        start = time.perf_counter()
        _dot, num_states = test_formula(expr)
        duration_ms = (time.perf_counter() - start) * 1000
        q.put((round(duration_ms, 2), num_states, "ok"))
    except Exception as exc:  # noqa: BLE001
        print(f"Error in test_formula({expr!r}): {exc}")
        q.put((None, None, "error"))


def _safe_run_formula(expr: str, timeout_sec: int) -> Result:
    """Run `test_formula` with a hard timeout via a dedicated subprocess."""
    ctx = mp.get_context("spawn")
    q: mp.Queue[Result] = ctx.Queue()
    p = ctx.Process(target=_run_in_subprocess, args=(expr, q))
    p.start()
    p.join(timeout_sec)

    if p.is_alive():  # hard timeout
        p.terminate()
        p.join()
        return None, None, "timeout"

    try:
        return q.get_nowait()
    except Exception:  # queue empty or other issue
        return None, None, "error"


# ---------------------------------------------------------------------------
# High‑level driver
# ---------------------------------------------------------------------------


def run_tests_from_csv(csv_path: str, output_csv: str, timeout: int, jobs: int = 8) -> None:
    csv_path = Path(csv_path).expanduser().resolve()
    output_csv = Path(output_csv).expanduser().resolve()

    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    total = len(df)

    # Pre‑allocate result columns (so dtype == float/int, NaN for missing)
    df["time_ms"] = pd.NA
    df["num_states"] = pd.NA
    df["outcome"] = "pending"

    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        fut_to_idx = {
            ex.submit(_safe_run_formula, expr, timeout): idx
            for idx, expr in enumerate(df["expression"].tolist())
        }

        finished = 0
        for fut in cf.as_completed(fut_to_idx):
            idx = fut_to_idx[fut]
            expr = df.at[idx, "expression"]
            preview = expr[:50] + ("…" if len(expr) > 50 else "")

            try:
                duration, states, status = fut.result()
            except Exception as exc:  # should never fire; already handled
                duration, states, status = None, None, "error"
                print(f"Internal error for index {idx}: {exc}")

            df.at[idx, "outcome"] = status
            if status == "ok":
                df.at[idx, "time_ms"] = duration
                df.at[idx, "num_states"] = states
                print(f"[{finished + 1}/{total}] ✅ '{preview}' → {duration:.2f} ms, {states} states")
            elif status == "timeout":
                print(f"[{finished + 1}/{total}] ⚠️  '{preview}' → timeout (>{timeout}s)")
            else:  # error
                print(f"[{finished + 1}/{total}] ❌ '{preview}' → error (see log)")

            finished += 1

    df.to_csv(output_csv, index=False)
    print(f"\n✅ Results saved to {output_csv}")

def retry_failed_tests(csv_path):
    # Make path relative to script directory
    script_dir = get_script_dir()
    csv_path = os.path.join(script_dir, csv_path)
    
    df = pd.read_csv(csv_path, dtype={"time_ms": str, "num_states": str})

    updated = False

    for idx, row in df.iterrows():
        time_val = row["time_ms"]
        if str(time_val) == "n/a" or pd.isna(time_val):
            expr = row["expression"]
            print(f"[Retry {idx+1}/{len(df)}] Retrying formula...")

            time_ms, num_states = run_formula_with_timeout(expr, timeout_sec=60)

            if time_ms == "n/a":
                print(f"⚠️ Still timeout after 60s in row {idx}")
            else:
                print(f"✅ Recovered: {time_ms:.2f}ms with {num_states} states")
                df.at[idx, "time_ms"] = time_ms
                df.at[idx, "num_states"] = num_states
                updated = True

    if updated:
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Updated file saved to {csv_path}")
    else:
        print("\nℹ️ No updates made; all timeouts remain.")

# Example usage:
# retry_failed_tests("test_results.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automaton formula tester")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run tests from a CSV")
    run_parser.add_argument("input_csv", help="Path to input CSV with formulas.")
    run_parser.add_argument("output_csv", help="Path to output CSV where results will be saved.")

    # Subcommand: retry-failed
    retry_parser = subparsers.add_parser("retry-failed", help="Retry failed tests in a results CSV")
    retry_parser.add_argument("csv_path", help="Path to CSV file to retry timeouts in.")

    args = parser.parse_args()

    if args.command == "run":
        run_tests_from_csv(args.input_csv, args.output_csv)
    elif args.command == "retry-failed":
        retry_failed_tests(args.csv_path)