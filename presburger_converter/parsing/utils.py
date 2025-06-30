from presburger_converter.parsing.ast_nodes import Var, Exists, ForAll
from lark.lexer import Token
# ---------------------------------------------------------------------------
# Free-variable check
# ---------------------------------------------------------------------------

def _free_vars(node, bound=frozenset()) -> set[str]:
    # ── atomic cases ───────────────────────────────────────────────
    if isinstance(node, str):
        return {node} - bound

    if isinstance(node, Var):
        return {node.name} - bound

    if isinstance(node, Token):
        return {str(node)} - bound

    # ── quantifiers ────────────────────────────────────────────────
    if isinstance(node, (Exists, ForAll)):
        bound_name = node.var.name if hasattr(node.var, "name") else str(node.var)
        return _free_vars(node.formula, bound | {bound_name})

    # ── generic structural recursion ───────────────────────────────
    vars_found = set()

    # Walk over standard containers first
    if isinstance(node, (list, tuple, set)):
        for item in node:
            vars_found |= _free_vars(item, bound)
        return vars_found

    if hasattr(node, "__dict__"):
        for v in node.__dict__.values():
            vars_found |= _free_vars(v, bound)


    return vars_found