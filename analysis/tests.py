import pandas as pd
import random
import string


def generate_random_formula(c, depth, variable_count):
    if not (1 <= variable_count <= 10):
        raise ValueError("variable_count must be between 1 and 10.")
    if depth > variable_count:
        raise ValueError("depth cannot be greater than variable_count.")

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
    c_random = random.randint(max(0, c - 10), c + 10)
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


def generate_test_dataframe():
    count_values = [1]
    c_values = [0,50,100,150,200,250,300,350,400,450,500]
    variable_counts = [4]
    depths = [0]
    modes = ["or"]

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

                        num_samples = 10
                        for _ in range(num_samples):
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
    return df


df = generate_test_dataframe()
df.to_csv("tests/test_constants.csv", index=False)

#print(formula_to_dot("(EX z. x = 4z) AND (EX w. y = 4w)", [], 0))