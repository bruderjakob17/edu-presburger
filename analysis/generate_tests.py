import pandas as pd
import random
import string

def _random_atomic_formula(c: int, variables: list[str]) -> str:
    """
    Create one quantifier-free linear (in)equality over the given variables.

    Coefficients are chosen uniformly from {-3,…,-1,1,…,3}.
    The constant is random in [c-10 … c+10] (always ≥ 1).
    """
    coefficients = [random.choice([i for i in range(-3, 4) if i != 0])
                    for _ in variables]
    op = random.choice(['=', '<=', '>=', '<', '>'])

    constant = random.randint(max(1, c - 10), c + 10)

    terms = []
    for coef, var in zip(coefficients, variables):
        term = f"{coef}{var}" if coef < 0 else f"+{coef}{var}"
        terms.append(term)

    lhs = ' '.join(terms).lstrip('+')          # drop a leading “+”
    return f"{lhs} {op} {constant}"            # e.g.  "-2x +3y >= 17"


def generate_quantified_formula(count: int,
                                c: int,
                                depth: int,
                                variable_count: int,
                                mode: str = "random") -> str:
    """
    Build  ⟨quantifier block⟩ ( φ₁ ⋄ φ₂ ⋄ … φ_count )

    - `count`           how many atomic sub-formulas to glue together
    - `c`               central constant around which all RHS constants vary
    - `depth`           length of alternating quantifier prefix
                        (∀ for even positions, ∃ for odd positions)
    - `variable_count`  how many distinct variables appear in every atom
    - `mode`            "and", "or", or "random" (randomly picks AND/OR per gap)
    """
    if not (1 <= variable_count <= 10):
        raise ValueError("variable_count must be between 1 and 10.")
    if not (0 <= depth <= variable_count):
        raise ValueError("depth must be between 1 and variable_count.")
    if mode.lower() not in {"and", "or", "random"}:
        raise ValueError("mode must be 'and', 'or', or 'random'.")

    variables = list(string.ascii_lowercase[:variable_count])

    # ---- 1. create the atomic pieces (no quantifiers yet) -------------------
    atoms = [f"({_random_atomic_formula(c, variables)})" for _ in range(count)]

    # ---- 2. combine them with the requested Boolean operator(s) -------------
    combined = atoms[0]
    for atom in atoms[1:]:
        if mode.lower() == "random":
            op = random.choice(["AND", "OR"])
        else:
            op = mode.upper()
        combined = f"{combined} {op} {atom}"

    # ---- 3. prepend the alternating quantifier block ------------------------
    quant_block = ""
    for i in range(depth):
        q = 'A' if i % 2 == 0 else 'E'          # ∀ for 0,2,4…  ∃ for 1,3,5…
        quant_block += f"{q} {variables[i]}. "

    return quant_block + combined

def generate_random_formula(c, depth, variable_count):
    if not (1 <= variable_count <= 10):
        raise ValueError("variable_count must be between 1 and 10.")
    if depth > variable_count:
        raise ValueError("depth cannot be greater than variable_count.")
    c_random = random.randint(max(0, c - 10), c + 10)
    variables = list(string.ascii_lowercase[:variable_count])
    coefficients = [random.choice([i for i in range(-3, 4) if i != 0]) for _ in range(variable_count)]
    inequality_operator = random.choice(['=', '<=', '>=', '<', '>'])

    quantifier_str = ''
    for i in range(depth):
        quantifier = 'A' if i % 2 == 0 else 'E'
        quantifier_str += f"{quantifier} {variables[i]}. "

    terms = []
    for coef, var in zip(coefficients, variables):
        term = f"{coef}{var}" if coef < 0 else f"+{coef}{var}"
        terms.append(term)
    # pick c_random as an integer that is around a the interval c - 10 c + 10, where c-10 > 0
    expression = ' '.join(terms).lstrip('+')
    formula = f"{quantifier_str}{expression} {inequality_operator} {c_random}"
    return formula


def generate_combined_formulas(count, c, depth, variable_count, mode):
    if mode not in {"and", "or", "random"}:
        raise ValueError("mode must be 'and', 'or', or 'random'")
    formulas = [f"({generate_random_formula(c, depth, variable_count)})" for _ in range(count)]

    combined = formulas[0]
    for i in range(1, count):
        if mode == "random":
            op = random.choice(["AND", "OR"])
        else:
            op = mode.upper()
        combined = f"{combined} {op} {formulas[i]}"

    return combined


def generate_test_dataframe(position, path, count_values, c_values, variable_counts, depths, modes, sample_size):
    rows = []
    for count in count_values:
        for c in c_values:
            for variable_count in variable_counts:
                for depth in depths:
                    if depth > variable_count:
                        continue  # prune invalid case

                    for mode in modes:
                        #if count == 1 and mode != "random":
                        #    continue  # only do one for count == 1

                        for _ in range(sample_size):
                            #c_random = random.randint(max(0, c - 10), c + 10)
                            if position == "outside":
                                expr = generate_quantified_formula(count, c, depth, variable_count, mode)
                            else:
                                expr = generate_combined_formulas(count, c, depth, variable_count, mode)
                            rows.append({
                                "expression": expr,
                                "count": count,
                                "constant": c,
                                "variable_count": variable_count,
                                "depth": depth,
                                "mode": mode
                            })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)