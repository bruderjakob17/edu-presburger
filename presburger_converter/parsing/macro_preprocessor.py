# macro_preprocessor.py
"""
Collects user-defined macros, checks them, expands them recursively and
returns the expanded formula as a string.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from collections import OrderedDict
from typing import Mapping, Sequence

# --- Project imports --------------------------------------------------------
from presburger_converter.parsing.parser import parse_formula, UnexpectedInput
from presburger_converter.parsing.utils import _free_vars

# ---------------------------------------------------------------------------

@dataclass
class Macro:
    name: str
    params: tuple[str, ...]
    body_src: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_header_rx = re.compile(
    r"""^\s*([A-Za-z]\w*)
         \s*\(\s*([^)]*)\)\s*=\s*
         (.+)$
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

        args, i = _parse_parenthesised_args(src, i)
        macro = macros[name]
        if len(args) != len(macro.params):
            raise UnexpectedInput(
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
        # check if name is logical operator
        if name in {"AND", "OR", "NOT", "E", "EX", "A", "ALL"}:
            raise UnexpectedInput("macro names cannot be logical operators")
        # check duplicates
        if name in macros:
            raise SyntaxError(f"duplicate macro '{name}' (line {idx+1})")

        # expand RHS using *earlier* macros only
        expanded_rhs = _expand(rhs, macros)
        try:
            ast_rhs = parse_formula(expanded_rhs)
        except UnexpectedInput as e:
            raise UnexpectedInput(
                f"Inside macro '{name}' (line {idx+1}):\n{e}"
            )

        if _free_vars(ast_rhs) != set(params):
            raise UnexpectedInput(
                f"free vars {sorted(_free_vars(ast_rhs))} "
                f"don’t match parameter list {sorted(params)} "
                f"(line {idx+1})"
            )

        macros[name] = Macro(name, params, rhs.strip())
    else:
        # all lines were macros
        idx += 1
    return macros, idx


def process_macros(user_input):
    lines = _split_lines(user_input)
    if not lines:
        raise UnexpectedInput("Empty input")

    macros, start_idx = _collect_macros(lines)

    # The remaining lines form the actual formula.
    formula_src = "\n".join(lines[start_idx:])
    if not formula_src:
        raise UnexpectedInput("No formula line found after macro definitions")

    expanded_formula = _expand(formula_src, macros)
    #print(f"Expanded formula:\n{expanded_formula}\n")
    return expanded_formula