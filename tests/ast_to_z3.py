# ast_to_z3.py  ──────────────────────────────────────────────────────────────
from __future__ import annotations
import z3

try:
    from presburger_converter.parsing import ast_nodes as _ast
except ModuleNotFoundError:
    import ast_nodes as _ast


class _Converter:
    """Stateful visitor that caches Z3 vars, tracks scope, and enforces ℕ-domain."""
    def __init__(self):
        self._var_cache: dict[str, z3.Int] = {}
        # ───── NEW: for nat-restriction ─────
        self._scope_stack: list[str] = []   # bound variables (LIFO)
        self._free_vars: set[str] = set()   # seen outside any quantifier

    # ─────────────────────── helpers ────────────────────────
    def _var(self, name: str) -> z3.IntRef:
        # create/cache the Z3 symbol
        if name not in self._var_cache:
            self._var_cache[name] = z3.Int(name)

        # ── NEW: record as free if not currently bound ──
        if name not in self._scope_stack:
            self._free_vars.add(name)

        return self._var_cache[name]

    # ─────────────────── dispatch entry ─────────────────────
    def __call__(self, node):
        meth = "_convert_" + node.__class__.__name__
        if hasattr(self, meth):
            return getattr(self, meth)(node)
        raise TypeError(f"Unhandled AST node type: {node.__class__.__name__}")

    # ─────────────────── terms (Int) ────────────────────────
    def _convert_Var(self, n: _ast.Var):
        # ───── NEW: collect free vars ─────
        return self._var(n.name)

    def _convert_Zero(self, n: _ast.Zero):   return z3.IntVal(0)
    def _convert_One(self, n: _ast.One):     return z3.IntVal(1)
    def _convert_Const(self, n: _ast.Const): return z3.IntVal(n.value)
    def _convert_Add(self, n: _ast.Add):     return self(n.left) + self(n.right)
    def _convert_Sub(self, n: _ast.Sub):     return self(n.left) - self(n.right)
    def _convert_Mult(self, n: _ast.Mult):   return z3.IntVal(n.n) * self._var(n.var)

    # ─────────────── comparisons (Bool) ─────────────────────
    def _convert_LessEqual(self, n: _ast.LessEqual):       return self(n.left) <= self(n.right)
    def _convert_Less(self, n: _ast.Less):                 return self(n.left) <  self(n.right)
    def _convert_Greater(self, n: _ast.Greater):           return self(n.left) >  self(n.right)
    def _convert_GreaterEqual(self, n: _ast.GreaterEqual): return self(n.left) >= self(n.right)
    def _convert_Eq(self, n: _ast.Eq):                     return self(n.left) == self(n.right)

    # ────────────── Boolean connectives ─────────────────────
    def _convert_And(self, n: _ast.And):         return z3.And(self(n.left), self(n.right))
    def _convert_Or(self, n: _ast.Or):           return z3.Or(self(n.left), self(n.right))
    def _convert_Not(self, n: _ast.Not):         return z3.Not(self(n.expr))
    def _convert_Implies(self, n: _ast.Implies): return z3.Implies(self(n.left), self(n.right))
    def _convert_Iff(self, n: _ast.Iff):
        a, b = self(n.left), self(n.right)
        return a == b                            # ↔ as equality on Bool

    # ───────────────────── quantifiers ──────────────────────
    def _convert_Exists(self, n: _ast.Exists):
        vname = n.var
        v     = self._var(vname)

        # enter scope
        self._scope_stack.append(vname)
        body = self(n.formula)
        self._scope_stack.pop()

        # x ≥ 0 ∧ φ
        guarded_body = z3.And(v >= 0, body)
        return z3.Exists([v], guarded_body)

    def _convert_ForAll(self, n: _ast.ForAll):
        vname = n.var
        v     = self._var(vname)

        # enter scope
        self._scope_stack.append(vname)
        body = self(n.formula)
        self._scope_stack.pop()

        # x ≥ 0 → φ
        guarded_body = z3.Implies(v >= 0, body)
        return z3.ForAll([v], guarded_body)


# public façade -----------------------------------------------------
def to_z3(node):
    """
    Convert an AST node (formula or term) to a Z3 expression
    with all variables restricted to the natural numbers.
    """
    conv  = _Converter()
    expr  = conv(node)

    # ───── add guards for free vars ─────
    if conv._free_vars:
        guards = [conv._var(v) >= 0 for v in sorted(conv._free_vars)]
        expr   = z3.And(*(guards + [expr]))

    return expr