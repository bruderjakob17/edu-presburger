# macro_preprocessor.py
"""
Collects user-defined macros, checks them, expands them recursively and
finally delegates to `parser.parse_formula()`.

Usage
-----
from presburger_converter.parsing.macro_preprocessor import parse_with_macros
ast = parse_with_macros(text_with_macros)
"""
from __future__ import annotations
import re
from lark.lexer import Token          #  <-- new
from dataclasses import dataclass
from collections import OrderedDict
from typing import Mapping, Sequence

# --- Project imports --------------------------------------------------------
from presburger_converter.parsing.parser import parse_formula, UnexpectedInput
from presburger_converter.parsing.ast_nodes import Var, Exists, ForAll   # others via hasattr()

# ---------------------------------------------------------------------------

@dataclass
class Macro:
    name: str
    params: tuple[str, ...]   # formal parameter names
    body_src: str             # raw RHS exactly as typed by the user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_header_rx = re.compile(
    r"""^\s*([A-Za-z]\w*)           # name
         \s*\(\s*([^)]*)\)\s*=\s*   # (p1, ..., pn) =
         (.+)$                      #   RHS
    """,
    re.X,
)

_call_rx = re.compile(r"\b([A-Za-z]\w*)\s*\(")


def _split_lines(text: str) -> list[str]:
    """Strip comments & blank lines, preserve order."""
    result = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        result.append(ln.rstrip())
    return result


def _parse_parenthesised_args(src: str, open_idx: int) -> tuple[list[str], int]:
    """
    Given the index of the opening '(' in *src*, return (args, idx_after_closing_paren).

    Splits top-level commas only; nested parens are handled.
    """
    depth = 0
    last = open_idx + 1         # char after '('
    args: list[str] = []
    i = last
    while i < len(src):
        ch = src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                args.append(src[last:i].strip())
                return args, i + 1
            depth -= 1
        elif ch == "," and depth == 0:
            args.append(src[last:i].strip())
            last = i + 1
        i += 1
    raise SyntaxError("unbalanced parentheses while reading macro call")


def _expand(src: str, macros: Mapping[str, Macro], stack: tuple[str, ...] = ()) -> str:
    """
    Recursively expand every macro call found in *src*.
    """
    out = []
    i = 0
    while i < len(src):
        m = _call_rx.search(src, i)
        if not m:
            out.append(src[i:])
            break

        name = m.group(1)
        # copy text *before* the call
        out.append(src[i : m.start()])
        i = m.end() - 1                    # position of '('

        if name not in macros:
            # not a macro, just copy the original token *including its '('*
            out.append(src[m.start():m.end()])  # "OR (" , "AND (" , etc.
            i = m.end()  # <-- **add this line**
            continue

        if name in stack:
            cycle = " -> ".join(stack + (name,))
            raise RecursionError(f"cyclic macro usage detected: {cycle}")

        args, i = _parse_parenthesised_args(src, i)
        macro = macros[name]
        if len(args) != len(macro.params):
            raise SyntaxError(
                f"macro '{name}' expects {len(macro.params)} args, got {len(args)}"
            )

        # === positional substitution =======================================
        # 1.  Pure textual replacement of the *formal* names by the *actual*
        #     argument strings – no extra parens here!
        subst = macro.body_src
        for formal, actual in zip(macro.params, args):
            subst = re.sub(rf"\b{re.escape(formal)}\b", actual, subst)

        # 2.  Recursively expand any macro calls *inside* that text.
        expanded_body = _expand(subst, macros, stack + (name,))

        # 3.  Finally wrap the ENTIRE replacement in one pair of parentheses
        #     so the caller always receives a syntactically atomic formula.
        out.append(f"({expanded_body})")
    return "".join(out)


# ---------------------------------------------------------------------------
# Free-variable check
# ---------------------------------------------------------------------------

def _free_vars(node, bound=frozenset()) -> set[str]:
    """
    Return the set of variable names that occur free in *node*.
    Handles both ast_nodes.Var and raw lark Token objects.
    """
    # ── atomic cases ───────────────────────────────────────────────
    if isinstance(node, Var):
        return {node.name} - bound

    if isinstance(node, Token):
        # A Token only shows up as a *bound* variable (from the quantifier
        # header) or, in the worst case, a bare variable that the AST
        # transformer forgot to wrap.  Treat it like a plain name string.
        return {str(node)} - bound

    # ── quantifiers ────────────────────────────────────────────────
    if isinstance(node, (Exists, ForAll)):
        # The “var” field may be Var *or* Token, so normalise to str.
        bound_name = node.var.name if hasattr(node.var, "name") else str(node.var)
        return _free_vars(node.formula, bound | {bound_name})

    # ── generic structural recursion ───────────────────────────────
    vars_found = set()

    # Walk over standard containers first
    if isinstance(node, (list, tuple, set)):
        for item in node:
            vars_found |= _free_vars(item, bound)
        return vars_found

    # Then dive into attributes of AST objects
    if hasattr(node, "__dict__"):
        for v in node.__dict__.values():
            vars_found |= _free_vars(v, bound)

    return vars_found

# ---------------------------------------------------------------------------
# Main procedure
# ---------------------------------------------------------------------------

def _collect_macros(lines: Sequence[str]) -> tuple[OrderedDict[str, Macro], int]:
    """
    Scan *lines* from the top, collect macro definitions.
    Returns (macros_dict, index_of_first_non_macro_line).
    """
    macros: OrderedDict[str, Macro] = OrderedDict()
    idx = 0
    for idx, raw in enumerate(lines):
        m = _header_rx.match(raw)
        if not m:
            break

        name, params_csv, rhs = m.groups()
        params = tuple(p.strip() for p in params_csv.split(",") if p.strip())

        # check duplicates
        if name in macros:
            raise SyntaxError(f"duplicate macro '{name}' (line {idx+1})")

        # expand RHS using *earlier* macros only
        expanded_rhs = _expand(rhs, macros)
        try:
            ast_rhs = parse_formula(expanded_rhs)
        except UnexpectedInput as e:
            raise SyntaxError(
                f"syntax error inside macro '{name}' (line {idx+1}):\n{e}"
            ) from None

        if _free_vars(ast_rhs) != set(params):
            raise SyntaxError(
                f"free vars {sorted(_free_vars(ast_rhs))} "
                f"don’t match parameter list {sorted(params)} "
                f"(line {idx+1})"
            )

        macros[name] = Macro(name, params, rhs.strip())
    else:
        # all lines were macros
        idx += 1
    return macros, idx


def parse_with_macros(text: str):
    """
    Public entry point – call this **instead of** `parse_formula`
    when the user may have defined macros.
    """
    lines = _split_lines(text)
    if not lines:
        raise SyntaxError("empty input")

    macros, start_idx = _collect_macros(lines)

    # The remaining lines form the actual formula.
    formula_src = "\n".join(lines[start_idx:])
    if not formula_src:
        raise SyntaxError("no formula line found after macro definitions")

    expanded_formula = _expand(formula_src, macros)
    print(f"Expanded formula:\n{expanded_formula}\n")
    # Delegate to the ordinary parser so existing errors look the same
    return parse_formula(expanded_formula)