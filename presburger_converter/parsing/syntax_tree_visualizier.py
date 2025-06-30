# syntax_tree_visualizer.py  (extract)

from __future__ import annotations
from typing import Any
from graphviz import Digraph
from lark import Tree, Token

__all__ = ["syntax_tree_to_dot", "lark_tree_to_dot"]

# ──────────────────────────────────────────────────────────────────────────
# Utility shared by both renderers
# ──────────────────────────────────────────────────────────────────────────

def _forest_label(txt: str) -> str:
    """Escape new-lines for a forest node label."""
    return txt.replace("\\n", " ")

def _forest_wrap(label: str, children: list[str]) -> str:
    if not children:
        return f"[{label}]"
    joined = " ".join(children)
    return f"[{label} {joined}]"


# ──────────────────────────────────────────────────────────────────────────
#  1. Presburger-specific AST  ➜  PNG + forest string
# ──────────────────────────────────────────────────────────────────────────

def syntax_tree_to_dot(ast: Any, filename: str = "syntax_tree") -> str:  # noqa: D401
    """Render *ast* to PNG **and** return a \\begin{forest}… string."""
    dot = Digraph(comment="Syntax Tree")
    counter = {"id": 0}

    def _next_id() -> str:
        nid = f"n{counter['id']}"
        counter["id"] += 1
        return nid

    def _gv_label(node: Any) -> str:
        # Special multiplication pretty-print
        if hasattr(node, "n") and hasattr(node, "var"):
            return f"Mult\\n{getattr(node, 'n')} * {getattr(node, 'var')}"
        if not any(hasattr(node, a) for a in ("left", "right", "expr", "formula")):
            return f"{type(node).__name__}\\n{node}"
        return type(node).__name__

    def _forest(node: Any) -> str:
        """Return a forest fragment."""
        lab = _forest_label(_gv_label(node))
        # Quantified formula?
        if hasattr(node, "formula"):
            var_child = _forest_wrap(f"Var\\n{getattr(node, 'var')}", []) \
                        if getattr(node, "var", None) is not None else ""
            subformula = _forest(getattr(node, "formula"))
            children = [c for c in (var_child, subformula) if c]
            return _forest_wrap(lab, children)

        # Binary, unary, or generic fallback
        child_fragments = []
        if hasattr(node, "left") and hasattr(node, "right"):
            child_fragments = [_forest(node.left), _forest(node.right)]
        elif hasattr(node, "expr"):
            child_fragments = [_forest(node.expr)]
        else:
            for v in vars(node).values():
                if isinstance(v, (str, int, float, bool, type(None))):
                    continue
                if hasattr(v, "__dict__"):
                    child_fragments.append(_forest(v))
                elif isinstance(v, (list, tuple)):
                    child_fragments.extend(
                        _forest(x) for x in v if hasattr(x, "__dict__")
                    )
        return _forest_wrap(lab, child_fragments)

    # Graphviz walk – identical to before
    def _gv_add(node: Any, parent_id: str | None = None) -> None:
        nid = _next_id()
        dot.node(nid, _gv_label(node))
        if parent_id is not None:
            dot.edge(parent_id, nid)
        if hasattr(node, "formula"):
            if (v := getattr(node, "var", None)) is not None:
                vid = _next_id()
                dot.node(vid, f"Var\\n{v}")
                dot.edge(nid, vid)
            _gv_add(node.formula, nid)
            return
        if hasattr(node, "left") and hasattr(node, "right"):
            _gv_add(node.left, nid)
            _gv_add(node.right, nid)
            return
        if hasattr(node, "expr"):
            _gv_add(node.expr, nid)
            return
        for val in vars(node).values():
            if isinstance(val, (str, int, float, bool, type(None))):
                continue
            if hasattr(val, "__dict__"):
                _gv_add(val, nid)
            elif isinstance(val, (list, tuple)):
                for it in val:
                    if hasattr(it, "__dict__"):
                        _gv_add(it, nid)

    _gv_add(ast)
    dot.render(filename, format="png", cleanup=True)
    print(f"Syntax tree rendered to {filename}.png")

    latex_body = _forest(ast)
    return (
        "\\begin{forest}\n"
        "for tree={draw, rounded corners, inner sep=1pt, l=1.5cm}\n"
        f"{latex_body}\n"
        "\\end{forest}\n"
    )


# ──────────────────────────────────────────────────────────────────────────
#  2. Lark parse tree  ➜  PNG + forest string
# ──────────────────────────────────────────────────────────────────────────

def lark_tree_to_dot(ast: Tree | Token, filename: str = "syntax_tree") -> str:  # noqa: D401
    """Render *ast* to PNG **and** return a \\begin{forest}… string."""
    dot = Digraph(comment="Lark Syntax Tree")
    counter = {"id": 0}

    def _next_id() -> str:
        nid = f"n{counter['id']}"
        counter["id"] += 1
        return nid

    def _gv_label(node: Tree | Token) -> str:
        if isinstance(node, Tree):
            return node.data
        return f"{node.type}\\n{node.value}"

    def _forest(node: Tree | Token) -> str:
        label = _forest_label(_gv_label(node))
        if isinstance(node, Tree):
            children = [_forest(c) for c in node.children]
            return _forest_wrap(label, children)
        # Token → leaf
        return _forest_wrap(label, [])

    def _gv_add(node: Tree | Token, parent_id: str | None = None) -> None:
        nid = _next_id()
        dot.node(nid, _gv_label(node))
        if parent_id is not None:
            dot.edge(parent_id, nid)
        if isinstance(node, Tree):
            for ch in node.children:
                _gv_add(ch, nid)

    _gv_add(ast)
    dot.render(filename, format="png", cleanup=True)
    print(f"Syntax tree rendered to {filename}.png")

    latex_body = _forest(ast)
    return (
        "\\begin{forest}\n"
        "for tree={draw, rounded corners, inner sep=1pt, l=1.5cm}\n"
        f"{latex_body}\n"
        "\\end{forest}\n"
    )