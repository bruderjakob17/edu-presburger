# parser.py

from lark import Lark, Transformer, v_args, Token
from presburger_converter.parsing.ast_nodes import *
from lark import UnexpectedInput
import os

from presburger_converter.parsing.syntax_tree_visualizier import syntax_tree_to_dot, lark_tree_to_dot

# Load grammar
grammar_path = os.path.join(os.path.dirname(__file__), "grammar.lark")
with open(grammar_path) as file:
    grammar = file.read()

parser = Lark(grammar, start="start")

# parser.py

@v_args(inline=True)
class ASTTransformer(Transformer):
    # Variables and constants
    def unary_minus(self, expr):
        return Sub(Zero(), expr)

    def var(self, token):
        return Var(str(token))

    def const(self, token):
        return Const(int(token))

    def mult(self, const, var):
        return Mult(int(const), str(var))

    # Terms
    def add(self, left, right):
        return Add(left, right)

    def sub(self, left, right):
        return Sub(left, right)
    # Comparisons
    def leq(self, left, right):
        return LessEqual(left, right)

    def eq(self, left, right):
        return Eq(left, right)

    def less(self, left, right):
        return Less(left, right)

    def greater(self, left, right):
        return Greater(left, right)

    def greater_equal(self, left, right):
        return GreaterEqual(left, right)

    # Logical connectives
    def or_expr(self, left, right):
        return Or(left, right)

    def and_expr(self, left, right):
        return And(left, right)

    def not_expr(self, expr):
        return Not(expr)

    def implies(self, left, right):
        return Implies(left, right)

    def iff(self, left, right):
        return Iff(left, right)

    def ex_quantifier(self, _ex_token, var, formula):
        return Exists(var, formula)

    def all_quantifier(self, _all_token, var, formula):
        return ForAll(var, formula)

    def parent(self, expr):
        return expr

    # ────────────────────────────── pass-through helpers ──────────────────────────
    def term(self, expr):     return expr          # if a ‘term’ is just a ‘sum’
    def sum(self, expr):      return expr          # if a ‘sum’ is just a ‘product’
    def product(self, expr):  return expr          # if a ‘product’ is just a ‘factor’


def visualize_whitespace(line: str) -> str:
    """
    Replaces tabs with 4 spaces and makes other invisible characters visible.
    """
    line = line.replace("\t", "    ")  # Convert tabs to 4 spaces
    #line = line.replace(" ", "·")      # Optionally show spaces explicitly
    return line


# Main parser function
def parse_formula(formula):
    try:
        tree = parser.parse(formula)
        ast = ASTTransformer().transform(tree)
        return ast
    except UnexpectedInput as e:
        # Get raw line and caret context
        context = e.get_context(formula)

        # Clean and align with visible markers
        lines = context.splitlines()
        if len(lines) >= 2:
            input_line, caret_line = lines[-2], lines[-1]
            visual_input = visualize_whitespace(input_line)
            caret_offset = caret_line.index("^")
            visual_caret = " " * caret_offset + "^"
            context = visual_input + "\n" + visual_caret

        error_message = f"\n{context}"
        raise UnexpectedInput(error_message) # Optionally re-raise if you want to halt further execution