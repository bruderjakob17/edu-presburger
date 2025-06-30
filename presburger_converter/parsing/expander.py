from presburger_converter.parsing.ast_nodes import *
from presburger_converter.parsing.utils import _free_vars


def expand_shorthands(node):
    """Recursively eliminate logical‐formula shorthands while keeping
    numeric constants and multiplication nodes untouched.
    """

    # --- Atomic arithmetic terms ------------------------------------------------
    if isinstance(node, Zero):
        return node  # already canonical

    if isinstance(node, One):
        return node

    if isinstance(node, Var):
        return node

    if isinstance(node, Const):
        return node

    if isinstance(node, Mult):
        return node

    # --- Arithmetic operators ---------------------------------------------------
    if isinstance(node, Add):
        return Add(
            expand_shorthands(node.left),
            expand_shorthands(node.right),
        )

    if isinstance(node, Sub):
        return Sub(
            expand_shorthands(node.left),
            expand_shorthands(node.right),
        )

    # --- Comparisons ------------------------------------------------------------
    if isinstance(node, LessEqual):
        return LessEqual(
            expand_shorthands(node.left),
            expand_shorthands(node.right),
        )

    if isinstance(node, Eq):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(LessEqual(left, right), LessEqual(right, left)))

    if isinstance(node, Less):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(LessEqual(left, right), Not(LessEqual(right, left))))

    if isinstance(node, Greater):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(Less(right, left))

    if isinstance(node, GreaterEqual):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return LessEqual(expand_shorthands(right), expand_shorthands(left))

    # --- Logical connectives ----------------------------------------------------
    if isinstance(node, Implies):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return Or(Not(left), right)

    if isinstance(node, Iff):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return expand_shorthands(And(
            expand_shorthands(Implies(left, right)),
            expand_shorthands(Implies(right, left)),
        ))

    if isinstance(node, Not):
        return Not(expand_shorthands(node.expr))

    if isinstance(node, Or):
        return Or(
            expand_shorthands(node.left),
            expand_shorthands(node.right),
        )

    if isinstance(node, And):
        left = expand_shorthands(node.left)
        right = expand_shorthands(node.right)
        return Not(Or(Not(left), Not(right)))

    # --- Quantifiers ------------------------------------------------------------
    if isinstance(node, ForAll):
        return Not(Exists(node.var, expand_shorthands(Not(node.formula))))

    if isinstance(node, Exists):
        return Exists(node.var, expand_shorthands(node.formula))

    # ---------------------------------------------------------------------------
    raise ValueError(f"Unknown node type: {type(node)}")

def remove_unused_exists(node):
    if isinstance(node, Exists):
        inner = remove_unused_exists(node.formula)

        # normalise the bound variable to a *string*
        var_name = node.var.name if hasattr(node.var, "name") else str(node.var)

        return inner if var_name not in _free_vars(inner) else Exists(node.var, inner)

    if isinstance(node, (Or, And)):
        return type(node)(remove_unused_exists(node.left),
                          remove_unused_exists(node.right))

    if isinstance(node, Not):
        return Not(remove_unused_exists(node.expr))

    return node

def eliminate_double_negation(node):
    if isinstance(node, Not):
        inner = eliminate_double_negation(node.expr)
        return eliminate_double_negation(inner.expr) if isinstance(inner, Not) else Not(inner)
    if isinstance(node, Or):
        return Or(eliminate_double_negation(node.left),
                  eliminate_double_negation(node.right))
    if isinstance(node, Exists):
        return Exists(node.var, eliminate_double_negation(node.formula))
    return node

def _distribute_exists(var: str, subtree):
    """
    ∃x.(φ ∨ ψ)  →  (∃x.φ) ∨ (∃x.ψ)
    bound var is a string.
    """
    if isinstance(subtree, Or):
        return Or(Exists(var, _distribute_exists(var, subtree.left)),
                  Exists(var, _distribute_exists(var, subtree.right)))
    return Exists(var, subtree)


def push_exists_inward(node):
    """
    Commute consecutive ∃’s and push each ∃ through the first OR.
    Never deletes quantifiers.
    """
    if isinstance(node, Exists):
        # gather consecutive ∃’s
        chain, body = [], node
        while isinstance(body, Exists):
            chain.append(body.var)       # plain strings
            body = body.formula

        body = push_exists_inward(body)  # recurse past the chain

        for v in reversed(chain):
            body = _distribute_exists(v, body)

        return body

    if isinstance(node, Or):
        return Or(push_exists_inward(node.left),
                  push_exists_inward(node.right))

    if isinstance(node, Not):
        return Not(push_exists_inward(node.expr))

    return node

def process_syntax_tree(root):
    root = expand_shorthands(root)
    root = eliminate_double_negation(root)
    root = remove_unused_exists(root)
    root = push_exists_inward(root)
    root = remove_unused_exists(root)
    root = eliminate_double_negation(root)
    return root