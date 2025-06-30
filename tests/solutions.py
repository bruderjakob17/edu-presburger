from collections import deque
from typing import List, Dict, Any, Optional, Tuple, Set
import libmata.nfa.nfa as mata_nfa



def _int_to_lsbf(num: int, width: int) -> List[int]:
    """Return `width` bits, least-significant-bit first."""
    return [(num >> i) & 1 for i in range(width)]


def _lsbf_bits_to_int(bits: str) -> int:
    """Reverse of _int_to_lsbf for a bit-string such as '0101' (LSBF)."""
    return sum((int(b) << i) for i, b in enumerate(bits))


def describe_paths(
    variables: List[str],
    paths: List[List[int]],
    new_order: Optional[List[str]] = None,
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
        different order.  Bits inside every path label are re-ordered
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
        path_bits = []
        for label in path:
            bits = _int_to_lsbf(label, n)         # old order
            reordered = [bits[i] for i in mapping]
            path_bits.append("".join(str(b) for b in reordered))

        # 2. Build bit-strings for each variable (in var_out order)
        var_bits = [""] * n
        for step_bits in path_bits:
            for idx, bit_char in enumerate(step_bits):
                var_bits[idx] += bit_char

        # 3. Convert those bit-strings to integers
        var_ints = [_lsbf_bits_to_int(bstr) if bstr else 0 for bstr in var_bits]

        solutions.append(
            {
                "path_int": path,
                "path_bits": path_bits,
                "variables": var_out,
                "var_bits": dict(zip(var_out, var_bits)),
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
    while i > 1 and seq[i - 1] == 0:
        i -= 1
    return seq[:i]
"""
def find_unique_example_solutions(nfa: mata_nfa.Nfa, k, variable_order, new_variable_order = None):
    
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
            t_path = tuple(path)
            if t_path not in seen_solutions:
                seen_solutions.add(t_path)
                solutions.append(path)
                if len(solutions) == k:          # got enough → stop early
                    break

        # Breadth-first expansion
        for trans in nfa.get_trans_from_state_as_sequence(state):
            queue.append((trans.target, path + [trans.symbol]))

    described = describe_paths(variable_order, solutions, new_order=new_variable_order)

    if all(not d["var_ints"] for d in described):
        return []

    return described
"""

def find_unique_example_solutions(
    aut: mata_nfa.Nfa,
    k_solutions: int,
    variables: List[str],
    variable_order: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Breadth-first search that returns up to *k_solutions* **distinct**
    variable assignments (integer tuples).  A distinct assignment is one whose
    value-tuple differs from all previously collected ones; paths that only add
    trailing “0” labels (no bits set) are therefore ignored once their assignment
    has already been recorded.

    Parameters
    ----------
    aut : libmata.nfa.Nfa
        Automaton to explore.
    k_solutions : int
        Number of *unique* solutions desired (≤ 0 → []).
    variables : list[str]
        Variable order used when the automaton was built.
    variable_order : list[str] | None
        Optional re-ordering for human-readable output (same semantics as
        ``describe_paths``).

    Returns
    -------
    list[dict[str, Any]]
        At most *k_solutions* solution objects, in BFS order and with no
        duplicates.  If fewer than *k_solutions* distinct assignments exist,
        all of them are returned.
    """
    if k_solutions <= 0:
        return []

    n = len(variables)

    # Map automaton-bit order → desired output order
    if variable_order is None:
        mapping = list(range(n))
        out_vars = variables
    else:
        if sorted(variable_order) != sorted(variables):
            raise ValueError("variable_order must contain the same variables.")
        mapping = [variables.index(v) for v in variable_order]
        out_vars = variable_order

    # BFS queue contains (state, path_so_far)
    queue: deque[Tuple[int, List[int]]] = deque(
        (init, []) for init in aut.initial_states
    )

    seen_assignments: Set[Tuple[int, ...]] = set()
    unique_paths: List[List[int]] = []

    while queue and len(unique_paths) < k_solutions:
        state, path = queue.popleft()

        # ── 1. Accepting state? → extract assignment and record if new ─────
        if state in aut.final_states:
            var_bits = ["" for _ in range(n)]
            for label in path:
                bits = _int_to_lsbf(label, n)            # automaton order
                reordered = [bits[i] for i in mapping]   # output order
                for idx, bit in enumerate(reordered):
                    var_bits[idx] += str(bit)

            var_ints = tuple(_lsbf_bits_to_int(b) for b in var_bits)

            if var_ints not in seen_assignments:
                seen_assignments.add(var_ints)
                unique_paths.append(path)
                if len(unique_paths) == k_solutions:
                    break  # collected enough assignments

        transitions = aut.get_trans_from_state_as_sequence(state)
        if not (len(transitions) == 1 and transitions[0].symbol == 0 and transitions[0].target == state):
            for tr in transitions:
                queue.append((tr.target, path + [tr.symbol]))

    # ── 3. Wrap paths in rich, human-readable structures ───────────────────
    described = describe_paths(variables, unique_paths, new_order=variable_order)

    if all(not d["var_ints"] for d in described):
        return []

    return described


def _assignment_to_labels(
    assignment: Dict[str, int],
    variable_order: List[str],
) -> List[int]:
    """
    Encode the integers in *assignment* as LSBF labels, one label per time step.

    Example
    -------
    variable_order = ["x", "y"]
    assignment     = {"x": 5, "y": 6}   # 5=101, 6=011
    labels         = [0b10, 0b01, 0b11]  # [2, 1, 3]
    """
    if not variable_order:
        # All variables are quantified → the automaton reads ε.
        return []  # nothing to encode
    n = len(variable_order)
    max_bits = max(assignment.get(v, 0).bit_length() for v in variable_order)
    max_bits = max(max_bits, 1)  # encode 0 with at least one bit

    labels: List[int] = []
    for i in range(max_bits):
        label = 0
        for idx, var in enumerate(variable_order):
            if (assignment.get(var, 0) >> i) & 1:
                label |= 1 << idx
        labels.append(label)
    return labels


def accepts_assignment(
    nfa: mata_nfa.Nfa,
    assignment: Dict[str, int],
    variable_order: List[str],
) -> bool:
    """
    Return True iff the NFA accepts the bit-stream that encodes *assignment*.

    Parameters
    ----------
    nfa : libmata.nfa.Nfa
        Automaton built with *variable_order* as its bit positions.
    assignment : dict[str,int]
        Concrete values to test, {var: int}.
    variable_order : list[str]
        Order in which variables were placed into the bit positions when
        building the automaton (index 0 == LSB of label integer).

    Notes
    -----
    • Works even if the same assignment can be represented with trailing-zero
      variants; all produce the same prefix and the automaton must accept at
      least one of them.
    • No epsilon transitions are assumed.  If your automata use them, add an
      ε-closure step marked in the code below.
    """
    labels = _assignment_to_labels(assignment, variable_order)

    # Current frontier of states (NFA = set of states)
    current_states: Set[int] = set(nfa.initial_states)

    # -- optional: ε-closure of initial states ------------------------
    # current_states = _epsilon_closure(nfa, current_states)

    for lab in labels:
        next_states: Set[int] = set()
        for st in current_states:
            for tr in nfa.get_trans_from_state_as_sequence(st):
                if tr.symbol == lab:
                    next_states.add(tr.target)
        if not next_states:
            return False  # dead end ⇒ reject
        current_states = next_states
        # current_states = _epsilon_closure(nfa, current_states)  # if needed

    return any(st in nfa.final_states for st in current_states)