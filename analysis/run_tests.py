#!/usr/bin/env python3

import pandas as pd
import time
import re
import argparse
import os
from multiprocessing import Process, Queue
from backend.processing import formula_to_dot

def get_script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def count_states_in_dot(dot_string):
    return len(re.findall(r'^\s*\d+\s+\[label=', dot_string, re.MULTILINE))


# 🔁 Moved to top-level so it can be pickled
def formula_worker(q, expr):
    try:
        start = time.perf_counter()
        print("called formula_to_dot")
        _, dot_string, num_states = formula_to_dot(expr, [], 0)
        print(dot_string)
        duration = (time.perf_counter() - start) * 1000
        #num_states = count_states_in_dot(dot_string)
        q.put((duration, num_states))
    except Exception as e:
        print(f"Error processing {expr}: {e}")
        q.put(("n/a", "n/a"))


def run_formula_with_timeout(expr, timeout_sec=10):
    q = Queue()
    p = Process(target=formula_worker, args=(q, expr))
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


def run_tests_from_csv(csv_path, output_csv):
    # Make paths relative to script directory
    script_dir = get_script_dir()
    csv_path = os.path.join(script_dir, csv_path)
    output_csv = os.path.join(script_dir, output_csv)
    
    df = pd.read_csv(csv_path)

    times = []
    state_counts = []

    total = len(df)
    for idx, row in df.iterrows():
        expr = row['expression']
        print(expr)
        print(f"[{idx+1}/{total}] Testing formula...")

        time_ms, num_states = run_formula_with_timeout(expr)

        if time_ms == "n/a":
            print(f"⚠️ Timeout or error in row {idx}")
        else:
            print(f"✅ Done in {time_ms:.2f}ms with {num_states} states")

        times.append(time_ms)
        state_counts.append(num_states)

    df["time_ms"] = times
    df["num_states"] = state_counts

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