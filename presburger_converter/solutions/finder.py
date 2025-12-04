# finder.py
from collections import deque
import libmata.nfa.nfa as mata_nfa
from typing import List, Dict, Any, Optional, Tuple, Set


def _int_to_lsbf(num: int, width: int, base: int = 2) -> List[int]:
    """Return `width` digits, least-significant-digit first.
    
    Args:
        num: Integer to convert
        width: Number of digits in output
        base: The base for encoding (default 2 for binary)
    
    Returns:
        List of digits in least-significant-first order
    """
    return [(num // (base ** i)) % base for i in range(width)]


def _lsbf_digits_to_int(digits: str, base: int = 2) -> int:
    """Reverse of _int_to_lsbf for a digit-string such as '0101' (LSBF).
    
    Args:
        digits: String of digits in least-significant-first order
        base: The base for encoding (default 2 for binary)
    
    Returns:
        Integer value
    """
    return sum((int(d) * (base ** i)) for i, d in enumerate(digits))


def describe_paths(
    variables: List[str],
    paths: List[List[int]],
    new_order: Optional[List[str]] = None,
    base: int = 2,
) -> List[Dict[str, Any]]:
    """
    Convert integer-label paths into rich, human-readable descriptions.

    Parameters
    ----------
    variables : List[str]
        Variable order the automaton was built with.
    paths : List[List[int]]
        Output of `find_shortest_paths` – each path is a list of integers.
    new_order : Optional[List[str]]
        If given, must contain *exactly* the same variable names but in a
        different order.  Digits inside every path label are re-ordered
        accordingly **before** all other computations.

    Returns
    -------
    List[Dict[str, Any]]
        One dictionary per solution, in BFS order.
        Keys:
            * "path_int"   – original integer labels (unchanged)
            * "path_bits"  – labels as binary strings (re-ordered if requested)
            * "variables"  – the variable order the description uses
            * "var_bits"   – {var: bit-string LSBF}
            * "var_ints"   – {var: integer value}
    """
    n = len(variables)
    if new_order is None:
        mapping = list(range(n))                  # identity
        var_out = variables
    else:
        if sorted(new_order) != sorted(variables):
            raise ValueError("new_order must contain the same variables.")
        mapping = [variables.index(v) for v in new_order]
        var_out = new_order

    solutions = []

    for path in paths:
        # 1. Re-order every label *inside the path* if needed
        path_digits = []
        for label in path:
            digits = _int_to_lsbf(label, n, base)  # old order
            reordered = [digits[i] for i in mapping]
            path_digits.append("".join(str(d) for d in reordered))

        # 2. Build digit-strings for each variable (in var_out order)
        var_digits = [""] * n
        for step_digits in path_digits:
            for idx, digit_char in enumerate(step_digits):
                var_digits[idx] += digit_char

        # 3. Convert those digit-strings to integers
        var_ints = [_lsbf_digits_to_int(dstr, base) if dstr else 0 for dstr in var_digits]

        solutions.append(
            {
                "path_int": path,
                "path_digits": path_digits,
                "path_bits": path_digits,  # Alias for backward compatibility with frontend
                "variables": var_out,
                "var_digits": dict(zip(var_out, var_digits)),
                "var_bits": dict(zip(var_out, var_digits)),  # Alias for backward compatibility
                "var_ints": dict(zip(var_out, var_ints)),
            }
        )

    return solutions

def remove_trailing_zeros(seq: List[int]) -> List[int]:
    """
    Removes trailing zeros from a list until the last element is nonzero,
    or only one element remains.
    """
    i = len(seq)
    while i > 0 and seq[i - 1] == 0:
        i -= 1
    return seq[:i]

def find_shortest_paths(nfa: mata_nfa.Nfa, k: int = 1) -> List[List[int]]:
    """
    Return up to *k* shortest accepting paths of an NFA, even in the presence
    of cycles (self-loops, etc.).  Paths are produced in non-decreasing
    length order.

    Parameters
    ----------
    nfa : mata_nfa.Nfa
        The automaton to explore.
    k : int, optional
        Number of paths to return (default: 1).

    Returns
    -------
    List[List[int]]
        The label sequences of the discovered paths.
    """
    if k <= 0:
        return []

    # (state, path_so_far)
    queue: deque[Tuple[int, List[int]]] = deque(
        (init, []) for init in nfa.initial_states
    )

    solutions: List[List[int]] = []
    seen_solutions: Set[Tuple[int, ...]] = set()   # dedup identical label sequences

    while queue and len(solutions) < k:
        state, path = queue.popleft()

        # Accepting configuration?
        if state in nfa.final_states:
            t_path = tuple(remove_trailing_zeros(path))
            if t_path not in seen_solutions:
                seen_solutions.add(t_path)
                solutions.append(path)
                if len(solutions) == k:          # got enough → stop early
                    break

        # Breadth-first expansion
        transitions = nfa.get_trans_from_state_as_sequence(state)
        if not (len(transitions) == 1 and transitions[0].symbol == 0 and transitions[0].target == state):
            for tr in transitions:
                queue.append((tr.target, path + [tr.symbol]))

    return solutions


def find_example_solutions(aut, k_solutions, variables_order, new_variable_order = None, base=2):
    example_solutions = find_shortest_paths(aut, k_solutions)
    if new_variable_order:
        example_solutions = describe_paths(variables_order, example_solutions, new_variable_order, base)
    else:
        # comment out for benchmarks
        example_solutions = describe_paths(variables_order, example_solutions, base=base)
    if all(not d["var_ints"] for d in example_solutions):
        return []
    return example_solutions
