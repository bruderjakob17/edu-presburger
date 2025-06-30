"""
z3_helpers.py ────────────────────────────────────────────────────────────────
Utility helpers for testing Presburger-arithmetic formulas with Z3.

Public API
~~~~~~~~~~
solve_with_z3(formula, banned_solutions=None, max_solutions=5, timeout_ms=None)
      → list[{var: value}]
conjoin_with_assignment(formula, assignment)
      → z3.BoolRef  representing (formula ∧ assignment)
is_assignment_sat(formula, assignment, timeout_ms=None)
      → bool        True iff *formula* is SAT under *assignment*.

The helpers now accept **either** a plain ``{var: int}`` mapping *or* a
solution-object returned by ``find_unique_example_solutions`` (i.e. one that
contains a ``"var_ints"`` field).  In the latter case we transparently pick up
``solution["var_ints"]`` so you can pass the whole dict without manual
unpacking.
"""

from __future__ import annotations
from typing import Dict, List, Sequence, Union, Optional, Any
import z3

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
BoolRef = getattr(z3, "BoolRef", z3.ExprRef)  # fallback for very old z3 builds
ModelDict = Dict[str, int]
Assignment = ModelDict
FormulaLike = Union[str, BoolRef]


# ---------------------------------------------------------------------------
#  Public: classify a Presburger/Z3 formula
# ---------------------------------------------------------------------------
def classify_formula(
    formula: FormulaLike,
    *,
    timeout_ms: int | None = None,
) -> str:
    """
    Return one of the strings

        'tautology'     -- φ is valid   (¬φ is UNSAT)
        'contradiction' -- φ is UNSAT
        'satisfiable'   -- φ is SAT but not valid
        'unknown'       -- Z3 answered 'unknown' for at least one check

    This check never enumerates models, so it’s very cheap.
    """
    phi = _ensure_z3_formula(formula)

    pos = z3.Solver()
    neg = z3.Solver()
    if timeout_ms is not None:
        pos.set("timeout", timeout_ms)
        neg.set("timeout", timeout_ms)

    pos.add(phi)
    neg.add(z3.Not(phi))

    res_pos = pos.check()
    res_neg = neg.check()

    if res_pos == z3.unsat:
        return "contradiction"
    if res_neg == z3.unsat:
        return "tautology"
    if res_pos == z3.sat:
        return "satisfiable"
    return "unknown"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_z3_formula(formula: FormulaLike) -> BoolRef:
    """Return a z3.BoolRef given either an SMT-LIB2 string or an existing BoolRef."""
    if isinstance(formula, BoolRef):
        return formula

    # Accept plain SMT-LIB2 or a bare expression (wrap in (assert …)).
    if "(assert" in formula:
        fmls = z3.parse_smt2_string(formula)
    else:
        fmls = z3.parse_smt2_string(f"(assert {formula})")

    if len(fmls) != 1:
        raise ValueError("Expected exactly one top-level formula in SMT string")
    return fmls[0]


def _model_to_dict(model: z3.ModelRef) -> ModelDict:
    """Convert a Z3 model into a plain {var: value} dict (Int and Bool sorts)."""
    res: ModelDict = {}
    for d in model.decls():
        val = model[d]
        if val is None:
            continue
        if z3.is_int_value(val):
            res[d.name()] = val.as_long()
        elif z3.is_true(val):
            res[d.name()] = 1
        elif z3.is_false(val):
            res[d.name()] = 0
        else:
            raise TypeError(f"Unsupported value sort for {d}: {val.sort()}")
    return res


def _disequality_constraint(solution: Assignment) -> BoolRef:
    """Return an Or(var ≠ val, …) constraint excluding *exactly* this assignment."""
    if not solution:
        return z3.BoolVal(False)  # No vars ⇒ no constraint
    return z3.Or([z3.Int(name) != val for name, val in solution.items()])


# ---------------------------------------------------------------------------
# Normalising external assignment objects
# ---------------------------------------------------------------------------

def _normalise_assignment(raw: Any) -> Assignment:
    """Return a clean {var: int} mapping.

    * Accepts:
        • a vanilla dict {str: int}
        • a solution object from finder.py that contains a ``"var_ints"`` key
    * Filters out non-int values and raises if anything looks fishy.
    """
    if isinstance(raw, dict):
        if "var_ints" in raw and isinstance(raw["var_ints"], dict):
            raw = raw["var_ints"]  # unwrap solution-dict
        # Keep only int-like entries (avoid lists, paths, etc.)
        cleaned: Assignment = {}
        for k, v in raw.items():
            if isinstance(v, bool):
                v = int(v)
            if isinstance(v, int):
                cleaned[k] = v
        if not cleaned:
            raise ValueError("No integer variables found in assignment object.")
        return cleaned
    raise TypeError("Assignment must be a dict or solution object from finder.py")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def solve_with_z3(
    formula: FormulaLike,
    *,
    banned_solutions: Sequence[Assignment] | None = None,
    max_solutions: int = 5,
    timeout_ms: int | None = None,
) -> List[Assignment]:
    """Enumerate up to *max_solutions* satisfying assignments for *formula*."""

    banned_solutions = list(banned_solutions or [])
    fml = _ensure_z3_formula(formula)

    s = z3.Solver()
    if timeout_ms is not None:
        s.set("timeout", timeout_ms)
    s.add(fml)

    for ban in banned_solutions:
        s.add(_disequality_constraint(ban))
    solutions: List[Assignment] = []
    while len(solutions) < max_solutions and s.check() == z3.sat:
        sol = _model_to_dict(s.model())
        if not sol:
            break
        solutions.append(sol)
        s.add(_disequality_constraint(sol))  # block this model next round
    return solutions


def conjoin_with_assignment(formula: FormulaLike, assignment: Any) -> BoolRef:
    """Return (formula) ∧ (∧ var = value) as a z3.BoolRef.

    The *assignment* can be either a plain mapping or a full solution dict
    from ``find_unique_example_solutions``.
    """
    clean = _normalise_assignment(assignment)
    base = _ensure_z3_formula(formula)
    equalities = [z3.Int(name) == val for name, val in clean.items()]
    return z3.And(base, *equalities)


def is_assignment_sat(
    formula: FormulaLike,
    assignment: Any,
    *,
    timeout_ms: int | None = None,
) -> bool:
    """Return True iff *formula* is still SAT when *assignment* is fixed.

    Accepts solution objects or plain mappings; see ``_normalise_assignment``.
    """
    phi = conjoin_with_assignment(formula, assignment)
    s = z3.Solver()
    if timeout_ms is not None:
        s.set("timeout", timeout_ms)
    s.add(phi)
    return s.check() == z3.sat


__all__ = [
    "solve_with_z3",
    "conjoin_with_assignment",
    "is_assignment_sat",
    "classify_formula",
    "_model_to_dict",
]