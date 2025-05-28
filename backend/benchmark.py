#!/usr/bin/env python3
"""
benchmark_formulas.py  –  stress-test string_to_automaton()

Adjust FORMULAS or the TIMEOUT_SEC constant to taste.
"""
import statistics as stats
import time
from typing import List, Tuple

# ──────────────────────────────────────────────────────────────
# Import your pipeline (edit the import to match your project)
# ──────────────────────────────────────────────────────────────
from processing import string_to_automaton          # ← change if needed
from lark import UnexpectedInput

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
TIMEOUT_SEC = 15          # fail-fast if one formula hangs catastrophically

# 80 representative formulas, grouped by rough complexity
FORMULAS: List[str] = [
    # ── Single comparisons ────────────────────────────────
    "x = 0",
    "y <= 3",
    "2x < y",
    "3z >= 2",
    # ── Boolean connectives (no quantifiers) ───────────────
    "(x = 0) AND (y = 1)",
    "(x = 0) OR (y = 1)",
    "NOT (x < y)",
    "(x = 1) -> (y = 2)",
    "(x = 0) <-> ((y = 1) AND (z = 2))",
    # ── Simple existential / universal quantifiers ─────────
    "EX x. x = 0",
    "EX x. 2x = y",
    "ALL x. x <= 3",
    "EX z. (z = 0) OR (z = 1)",
    "ALL z. (z < 2) -> (EX w. w = z + 1)",
    # ── Two-layer quantifier nests ─────────────────────────
    "EX x. EX y. x = 2y",
    "ALL x. EX y. y = x + 1",
    "EX z. ALL w. (z <= w) -> (w <= 4)",
    "EX x. ALL y. (2x = y) AND (y <= 8)",
    # ── Three-layer nests (still ≤4 distinct variables) ────
    "EX x. EX y. EX z. (x = 2y) AND (y = 2z)",
    "ALL x. EX y. EX z. (x = y + z) AND (y <= 2)",
    "EX x. EX y. ALL z. (x + y = z) -> (z <= 4)",
    # ── Mixed connectives + quantifiers ────────────────────
    "(EX x. x = 0) AND (EX y. y = 1)",
    "(EX x. x = 0) OR (ALL y. y < 4)",
    "NOT (EX x. x = 2)",
    "(EX x. x = 0) -> (EX y. y = x + 1)",
    "((ALL x. x < 3) AND (EX y. y = 2)) -> (z = 0)",
    # ── Implication / equivalence chains ───────────────────
    "(x = 0) -> (y = 1) -> (z = 2)",
    "(x = 0) <-> (y = 1) <-> (z = 2)",
    # ── Arithmetic sums of vars / consts ───────────────────
    "x + y = 3",
    "x + y + z = 5",
    "x + 2 = y + 3",
    "2x + 3 = y + z",
    # ── Combined arithmetic & quantifiers ──────────────────
    "EX x. x + y = 4",
    "EX x. EX y. x + y = 5",
    "EX x. EX y. EX z. x + y + z = 6",
    "ALL x. EX y. x + y = 2",
    # ── Long-ish flat conjunctions/disjunctions ────────────
    "(x = 0) AND (y = 1) AND (z = 2) AND (w = 3)",
    "(x = 0) OR (y = 1) OR (z = 2) OR (w = 3)",
    # ── Nested parentheses stress-test ─────────────────────
    "(((x = 0)))",
    "((((x = 0) AND (y = 1))))",
    "(x = 0) AND ((y = 1) OR ((z = 2) AND (w = 3)))",
    # ── “Worst”-case (for ≤4 vars) but still small numbers ─
    "EX x. EX y. EX z. EX w. ((x = 2y) AND (y = 2z) AND (z = 2w) AND (x + y + z + w = 10))",
    "ALL x. EX y. EX z. EX w. (x + y = z + w) AND (x <= 2) AND (y <= 2) AND (z <= 2) AND (w <= 2)",
    # ── More variations, until we hit 80 formulas ──────────
] + [
    # programmatically generate a few size-parametrised ones for volume
    f"EX x. EX y. EX z. (x + y + z = {n})"
    for n in range(0, 13)           # 13 more
] + [
    f"(x = {i}) AND (y = {j}) OR (z = {k})"
    for i in range(3) for j in range(3) for k in range(3)   # 27 more
]

EXTRA_HARD_FORMULAS = [
    # ── 1. Large flat OR with all 4 vars (12 disjuncts) ───────────────────────────
    "(x = 0) OR (y = 0) OR (z = 0) OR (w = 0) "
    "OR (x = 1) OR (y = 1) OR (z = 1) OR (w = 1) "
    "OR (x = 2) OR (y = 2) OR (z = 2) OR (w = 2)",

    # ── 2. Chain of four equivalences (each expands to two implications) ──────────
    "(x = 0) <-> (y = 1) <-> (z = 2) <-> (w = 3)",

    # ── 3–5. Three large conjunctions whose clauses are themselves wide ORs ──────
    "((x = 0) OR (y = 0) OR (z = 0)) "
    "AND ((x = 1) OR (y = 1) OR (z = 1)) "
    "AND ((x = 2) OR (y = 2) OR (z = 2))",

    "((x = 0) OR (y = 0)) AND ((x = 1) OR (y = 1)) "
    "AND ((x = 2) OR (y = 2)) AND ((x = 3) OR (y = 3))",

    "((x = 0) OR (y = 0) OR (z = 0) OR (w = 0)) "
    "AND ((x = 1) OR (y = 1) OR (z = 1) OR (w = 1))",

    # ── 6–8. Alternating quantifiers (worst for DFA→NFA→DFA blow-ups) ─────────────
    "ALL x. EX y. ALL z. EX w. ((x + y = z + w) AND (x <= 2) AND (y <= 2))",

    "EX x. ALL y. EX z. ALL w. ( (x + y + z + w = 5) OR (2x = y + z) )",

    "ALL x. EX y. ALL z. EX w. "
    "((x = 2y) OR (y = 2z) OR (z = 2w) OR (w = 2x))",

    # ── 9–11. Nested quantifiers *inside* an OR/AND mix ──────────────────────────
    "(EX x. x = 0) OR (EX y. y = 1) OR (EX z. z = 2) OR (EX w. w = 3)",

    "(ALL x. x <= 2) AND (ALL y. y <= 2) AND (ALL z. z <= 2) AND (ALL w. w <= 2)",

    "(EX x. (ALL y. y <= x)) OR (EX z. (ALL w. w <= z))",

    # ── 12–15. Big arithmetic + quantifiers combos ───────────────────────────────
    "EX x. EX y. EX z. EX w. (x + y + z + w = 7)",

    "ALL x. EX y. (x + y = 4) AND (y + 1 <= 3)",

    "EX x. ALL y. (x + y <= 4) AND (EX z. z = x + y)",

    "EX x. EX y. ALL z. (x + y = z) -> (z <= 8)",

    # ── 16–19. Long implication chains (right-associative) ───────────────────────
    "(x = 0) -> (y = 1) -> (z = 2) -> (w = 3)",

    "(x = 0) -> (y = 1) -> (z = 2) -> (w = 3) -> (x = 4)",   # still ≤4 vars

    "((x = 0) AND (y = 0)) -> ((z = 2) OR (w = 2)) -> (x = y)",

    "(x = 0) -> ((y = 1) -> ((z = 2) -> (w = 3)))",

    # ── 20–22. Nested parentheses depth stress (12 layers) ───────────────────────
    "(((((((((((x = 0)))))))))))",

    "((((((((((x = 0) AND (y = 1))))))))))",

    "((((((((((EX z. z = 0))))))))))",

    # ── 23–26. Huge OR of arithmetic equalities on one var (blow-up union) ───────
    " OR ".join(f"(x = {n})" for n in range(0, 11)),                   # x = 0 ∨ … ∨ x =10

    " OR ".join(f"(y = {n})" for n in range(0, 16)),                   # 16 disjuncts

    " OR ".join(f"(z = {n})" for n in range(0, 20)),                   # 20 disjuncts

    " OR ".join(f"(w = {n})" for n in range(0, 25)),                   # 25 disjuncts(!)

    # ── 27–30. Mixed quantifier blocks + big OR inside equivalence / impl ───────
    "(EX x. x = 0) <-> (EX y. y = 1) <-> (EX z. z = 2) <-> (EX w. w = 3)",

    "(ALL x. x < 3) -> ((EX y. y = x + 1) OR (EX z. z = x + 2))",

    "EX x. ALL y. ((EX z. z = x + y) OR (EX w. w = y + 1))",

    "ALL x. EX y. ((x + y <= 3) AND ((EX z. z = x) OR (EX w. w = y)))",
]

QUICK_TEST_FORMULAS = [
    # Flat OR (worst-case structure from previous benchmark)
    "(x = 0) OR (y = 0) OR (z = 0) OR (w = 0)",

    # Long implication chain (deep right-association)
    "(x = 0) -> (y = 1) -> (z = 2) -> (w = 3)",

    # Mixed quantifiers with arithmetic (DFA→NFA nesting)
    "EX x. ALL y. (x + y = 4)",

    # Big arithmetic conjunction
    "(x + y = 2) AND (z + w = 3)",

    # Wide equivalence chain
    "(x = 0) <-> (y = 1) <-> (z = 2) <-> (w = 3)",

    # Nested quantifier logic inside implication
    "(ALL x. x < 3) -> ((EX y. y = x + 1) OR (EX z. z = x + 2))",

    # Deeply nested parentheses
    "(((((((((((x = 0)))))))))))",

    # Arithmetic + quantifiers + Boolean nesting
    "(EX x. x + y = 4) AND (z = 1)",

    # Alternating quantifiers (stress nested automaton ops)
    "ALL x. EX y. ALL z. EX w. ((x + y = z + w) AND (x <= 2))",

    # Arithmetic-heavy OR chain
    " OR ".join(f"(w = {n})" for n in range(5))  # w = 0 ∨ w = 1 ∨ … ∨ w = 4
]

assert len(FORMULAS) == 83, f"Unexpected formula count: {len(FORMULAS)}"

# ──────────────────────────────────────────────────────────────
# Benchmark loop
# ──────────────────────────────────────────────────────────────
Result = Tuple[str, float, str]
results: List[Result] = []

print(f"Running benchmark on {len(QUICK_TEST_FORMULAS)} formulas …\n")
for idx, formula in enumerate(QUICK_TEST_FORMULAS, 1):
    t0 = time.perf_counter()
    status = "OK"
    try:
        string_to_automaton(formula)
    except UnexpectedInput as e:
        status = "ParseError"
    except Exception as e:
        status = f"{type(e).__name__}"
    dt = time.perf_counter() - t0
    results.append((formula, dt, status))

    # fail-fast if something takes forever
    if dt > TIMEOUT_SEC:
        print(f"⚠️  Aborting – single run exceeded {TIMEOUT_SEC}s")
        break

# ──────────────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────────────
max_len = max(len(f) for f, *_ in results)
print("\nFormula".ljust(max_len), " |  ms    | Status")
print("-" * (max_len + 21))
for f, dt, status in results:
    print(f.ljust(max_len), f"| {dt*1e3:7.2f} | {status}")

durations_ok = [dt for _, dt, s in results if s == "OK"]
if durations_ok:
    print("\nSummary (successful runs only):")
    print(f"  count : {len(durations_ok)}")
    print(f"  min   : {min(durations_ok)*1e3:.2f} ms")
    print(f"  median: {stats.median(durations_ok)*1e3:.2f} ms")
    print(f"  95-th : {stats.quantiles(durations_ok, n=20)[18]*1e3:.2f} ms")
    print(f"  max   : {max(durations_ok)*1e3:.2f} ms")
else:
    print("\n‼️  No successful runs recorded.")