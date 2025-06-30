import random

import pytest

from presburger_converter.solutions import find_example_solutions
from z3_helpers import classify_formula

import pandas as pd

def load_expressions_from_csv(file_path):
    """
    Loads a CSV file and extracts the 'expression' column into a list of strings.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        List[str]: List of expressions as strings.
    """
    df = pd.read_csv(file_path)
    if 'expression' not in df.columns:
        raise ValueError("CSV must contain a column named 'expression'")
    return df['expression'].dropna().astype(str).tolist()


FORMULAS = [
    "x = 3",
    "A x . x = 3",
    "E x . x = 3",
    "x = 4 AND x = 5",
    "x >= 7 AND E y . 4y = x",
    "E y . E z . 3y + 5z = 1",
    "NOT x = 3",
    "x = 3 OR y = 4",
    "x = 3 -> y = 4",
    "x = 3 <-> y = 4",
    "(x = 3)",
    "E x . x = y",
    "A x . x + 1 = 4",
    "E x . A y . x = y",
    "x <= 5",
    "x < 3",
    "x > 10",
    "x >= 11",
    "4x = 8",
    "3x + 5 = y",
    "x - 3 = 7",
    "2x + 3y = 10",
    "A x . (x > 5 -> x + 1 > 5)",
    "E x . (x < 10 AND x > 5)",
    "(x = 3 OR y = 4) AND z = 5",
    "x = 3 OR (y = 4 AND z = 5)",
    "NOT (x = 3 AND y = 4)",
    "E x . (x = 4 OR x = 5)",
    "A x . E y . (x + y = 10)",
    "x = 3 AND NOT y = 5",
    "E x . (4x + 5 = y)",
    "x = 4 OR y = 5 -> z = 6",
    "(x = 4 -> y = 5) -> z = 6",
    "x = 3 -> y = 4 -> z = 5",
    "x = 1 <-> y = 2 <-> z = 3",
    "E x . (x = 1 <-> y = 2)",
    "A x . (x + 1 = 2 -> x = 1)",
    "x + 1 = 2 AND y + 2 = 3",
    "x + y + z = 10",
    "x - y - z = 1",
    "3x + 2y - z = 7",
    "A x . x = x",
    "E x . NOT x = x",
    "x = x -> x = x",
    "(x = y) <-> (y = x)",
    "E x . (x = 3 OR x = 4)",
    "A x . (x < 0 OR x > 0)",
    "A x . E y . E z . (3x + 4y + 5z = 12)",
    "x + (y + z) = 10",
    "x + (y - z) = 3",
    "-3x + 2 = 5",
    "-x + y = 2",
    "E x . (x + 2 = 5)",
    "A x . (x + 1 < 3 -> x < 2)",
    "x = 3 AND (y = 4 OR z = 5)",
    "x = 3 OR (y = 4 AND z = 5)",
    "(x = 3 OR y = 4) AND (z = 5 -> a = 6)",
    "E x . A y . (x = y -> y = x)",
    "E x . (x = 3 -> y = 4)",
    "A x . (x = 3 <-> y = 4)",
    "x = 1 OR y = 2 OR z = 3",
    "x = 1 AND y = 2 AND z = 3",
    "x = 3 -> y = 4 -> z = 5 -> a = 6",
    "x = 3 <-> y = 4 <-> z = 5 <-> a = 6",
    "NOT (x = 3 OR y = 4)",
    "NOT (x = 3 AND y = 4)",
    "NOT (x = 3 -> y = 4)",
    "NOT (x = 3 <-> y = 4)",
    "E x . (x = 3 AND y = 4)",
    "E x . (x = 3 OR y = 4)",
    "E x . (x = 3 -> y = 4)",
    "E x . (x = 3 <-> y = 4)",
    "A x . (x = 3 AND y = 4)",
    "A x . (x = 3 OR y = 4)",
    "A x . (x = 3 -> y = 4)",
    "A x . (x = 3 <-> y = 4)",
    "x = (3 + 2)",
    "x = (y + (z - 1))",
    "x = (3x + 2)",
    "(x = 3) AND (y = 4)",
    "(x = 3) OR (y = 4)",
    "((x = 3) -> (y = 4))",
    "((x = 3) <-> (y = 4))",
    "E x . (x = 3 AND (y = 4 OR z = 5))",
    "A x . ((x = 3 -> y = 4) AND (z = 5 <-> a = 6))",
    "E x . A y . ((x = y) -> (y = x))",
    "A x . (E y . x = y) -> (E z . y = z)",
    "E x . (3x + 4 = 2x + 7)",
    "A x . (x + x = 2x)",
    "x + (y + (z + a)) = b",
    "3x = (y + 2z)",
    "(A x . E y . (3x + 4y = 12))",
    "E x . A y . (x < y -> y > x)",
    "E x . (x = 3 AND NOT (y = 4 OR z = 5))",
    "(E x . x = 1) AND (A y . y = 2)",
    "((x = 3) AND (y = 4)) -> z = 5",
    "A a. E b. (-1a -3b +2c -2d -1e -1f +2g +3h > 2)"
]

MORE_FORMULAS = [
    "x = 5",
    "x + 2 = 7",
    "x - 3 = 2",
    "3x = 9",
    "3x + 2 = 11",
    "x = y",
    "x + y = z",
    "x - y = 0",
    "x + y + z = 10",
    "x + (y - z) = 4",
    "3x + 2y - z = 8",
    "x = (y + 3)",
    "x = ((y + z) - a)",
    "x = (2x + 1)",
    "E x . x + 2 = 4",
    "A y . y - 1 = x",
    "E z . 2z = y",
    "A x . (x > 5 -> x < 10)",
    "E x . (x > 5 AND x < 10)",
    "x = 1 OR y = 2",
    "x = 1 AND y = 2",
    "x = 1 <-> y = 2",
    "x = 1 -> y = 2",
    "NOT x = 1",
    "NOT (x = 1 OR y = 2)",
    "NOT (x = 1 AND y = 2)",
    "(x = 1 OR y = 2) AND z = 3",
    "x = 1 OR (y = 2 AND z = 3)",
    "E x . (x = 1 OR x = 2)",
    "A x . E y . (x + y = 5)",
    "E x . A y . (x = y -> y = x)",
    "x = 1 AND NOT y = 2",
    "x = 1 OR y = 2 -> z = 3",
    "(x = 1 -> y = 2) -> z = 3",
    "x = 1 -> y = 2 -> z = 3",
    "x = 1 <-> y = 2 <-> z = 3",
    "E x . (x = 1 <-> y = 2)",
    "x + 1 = 2 AND y + 2 = 3 AND z = 4",
    "A x . (x + 1 = 2 -> x = 1)",
    "E x . A y . A z . 3x + 4y + 5z = 12",
    "A x . x = x",
    "E x . NOT x = x",
    "x = x -> x = x",
    "(x = y) <-> (y = x)",
    "E x . (x = 3 AND y = 4)",
    "A x . (x = 3 OR y = 4)",
    "E x . (x = 3 -> y = 4)",
    "A x . (x = 3 <-> y = 4)",
    "x = (3 + 2)",
    "x = (y + (z - 1))",
    "E x . (3x + 4 = 2x + 7)",
    "A x . (x + x = 2x)",
    "x + (y + (z + a)) = b",
    "3x = (y + 2z)",
    "E x . (x = 3 AND NOT (y = 4 OR z = 5))",
    "x = 1 AND (y = 2 OR z = 3)",
    "x = 1 OR (y = 2 AND z = 3)",
    "(x = 1 OR y = 2) AND (z = 3 -> a = 4)",
    "A x . ((x = 3 -> y = 4) AND (z = 5 <-> a = 6))",
    "E x . (x = 3 <-> (y = 4 OR z = 5))",
    "A x . (E y . x = y) -> (E z . y = z)",
    "E x . (x + 2 < 5)",
    "A x . (x + 1 < 3 -> x < 2)",
    "(x = 3) AND (y = 4)",
    "(x = 3) OR (y = 4)",
    "((x = 3) -> (y = 4))",
    "((x = 3) <-> (y = 4))",
    "x = 3 -> (y = 4 AND z = 5)",
    "x = 3 <-> (y = 4 -> z = 5)",
    "E x . (x = 1 AND y = 2 AND z = 3)",
    "A x . (x < 5 OR x > 10)",
    "E x . A y . (x + y < 20)",
    "E x . (x = 3 AND y = 4 OR z = 5)",
    "(E x . x = 1) AND (A y . y = 2)",
    "E x . A y . (x = y -> E z . y = z)",
    "x + 2y + 3z = 12",
    "x = (y + (z + (a + b)))",
    "x + 3 = (2y - z)",
    "-x + y = 1",
    "-3x + 2 = y",
    "A x . (x + 2 = 5 -> x = 3)",
    "A x . E y . (x = y AND y = x)",
    "E x . A y . (x + y = 10 -> y + x = 10)",
    "E x . (x = 1 OR (x = 2 AND x = 3))",
    "A x . (x = 3 -> y = 4 -> z = 5)",
    "x = 1 OR (y = 2 OR (z = 3 OR a = 4))",
    "x = 3 -> (y = 4 <-> (z = 5 -> a = 6))",
    "A x . (x = 1 AND x = 2 -> x = 3)",
    "E x . (x = 1 AND NOT x = 2)",
    "A x . (x = 1 -> (x = 2 -> x = 3))",
    "(x = 1 OR y = 2) <-> (z = 3 OR a = 4)",
    "E x . (x = 1 -> y = 2 AND z = 3)",
    "A x . (x = 1 OR y = 2 -> z = 3)",
    "x + y = y + x",
    "(x + y) + z = x + (y + z)",
    "E x . A y . (3x + 4y = 12)",
    "x + (2y - (z + 1)) = 7",
    "((x = 1 AND y = 2) -> z = 3)",
    "x = 3 AND ((y = 4 OR z = 5) -> a = 6)",
    "E x . (x + 1 = 2 AND x + 2 = 3)",
    "x = 3 -> (y = 4 -> (z = 5 -> a = 6))"
]
MAX_SOLUTIONS = 5  # Number of candidate models/solutions to collect per formula

from presburger_converter.parsing import parser
from presburger_converter import formula_to_aut
from ast_to_z3 import to_z3
from solutions import find_unique_example_solutions, accepts_assignment
from z3_helpers import is_assignment_sat, solve_with_z3


def _random_assignment(variables):
    result = []
    for i in range(0, MAX_SOLUTIONS):
        assignment = {}
        for var in variables:
            assignment[var] = random.randint(0, 10000)
        result.append(assignment)
    return result

#load_expressions_from_csv("/Users/johannesmichalke/Desktop/University/TUM/thesis/analysis/tests/depth/test_depth_outside_0_2_5_2_1_random_30.csv")
@pytest.mark.parametrize("formula", FORMULAS)
def test_automaton_vs_z3(formula):
    """Compare up to ``MAX_SOLUTIONS`` candidate assignments from Z3 with
    those generated by the automaton.  Two‑way consistency is required:

      • Z3 model ⇒ automaton must accept.
      • Automaton solution ⇒ Z3 must satisfy.

    If either engine produces *no* solutions, the other must also produce none.
    """


    aut, variables = formula_to_aut(formula)
    aut_solutions = find_example_solutions(aut, MAX_SOLUTIONS, variables)
    phi_z3 = to_z3(parser.parse_formula(formula))
    #print(phi_z3)
    if classify_formula(phi_z3) == "contradiction":
        assert not any(aut_solutions), (
            f"Automaton produced solutions for a contradiction formula {formula!r}.\n"
        )
    elif classify_formula(phi_z3) == "tautology":
        if not variables:
            assert not aut_solutions, (
                f"Automaton produced solutions for a tautology formula {formula!r} "
                "with no variables.\n"
            )
        else:
            assert any(aut_solutions), (
                f"Automaton produced no solutions for a tautology formula {formula!r}.\n"
            )
            random_models = _random_assignment(variables)
            for model in random_models:
                if not accepts_assignment(aut, model, variables):
                    pytest.fail(
                        f"Automaton rejected a random model for tautology {formula!r}: {model}")
    elif classify_formula(phi_z3) == "satisfiable":
        z3_models = solve_with_z3(phi_z3, max_solutions=MAX_SOLUTIONS, timeout_ms=1000)

        # ── Z3 → Automaton (soundness) ────────────────────────────────────────
        for model in z3_models:
            if not accepts_assignment(aut, model, variables):
                pytest.fail(
                    f"Automaton *rejects* a valid Z3 model for formula {formula!r}: {model}")

        # ── Automaton → Z3 (completeness) ─────────────────────────────────────
        for sol in aut_solutions:
            if not is_assignment_sat(phi_z3, sol, timeout_ms=1000):
                pytest.fail(
                    f"Automaton produced *spurious* solution for formula {formula!r}: {sol}")
    else:
        pytest.fail(f"Unexpected formula classification for {formula!r}: {classify_formula(formula)}")