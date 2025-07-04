from doctest import UnexpectedException

from presburger_converter.parsing import parser, expander, macro_preprocessor
from presburger_converter.automaton.automaton_builder import build_automaton, is_deterministic, determinize
import libmata.nfa.nfa as mata_nfa

from presburger_converter.parsing.ast_nodes import LessEqual
from lark import UnexpectedInput



def formula_to_aut(user_input, display_atomic_construction=False):
    formula = macro_preprocessor.process_macros(user_input)
    tree = parser.parse_formula(formula)
    pure_tree = expander.process_syntax_tree(tree)
    #pure_tree = expander.expand_shorthands(tree)
    aut, variables = build_automaton(pure_tree)
    aut.get_reachable_states()
    if display_atomic_construction:
        if isinstance(tree, LessEqual):
            aut_minimized = mata_nfa.minimize(aut)
            return aut_minimized, aut, variables
        else:
            raise UnexpectedInput("Formula does not have form t <= s. Can not display atomic construction.")
    else:
        aut = mata_nfa.minimize(aut)
    return aut, aut, variables


def test_formula(formula: str, mode = "plain"):
    clean_formula = macro_preprocessor.process_macros(formula)
    tree = parser.parse_formula(clean_formula)
    if mode == "plain":
        pure_tree = expander.expand_shorthands(tree)
    else:
        pure_tree = expander.process_syntax_tree(tree)
    aut, variables = build_automaton(pure_tree, mode)
    if not is_deterministic(aut):
        aut = determinize(aut)
    aut = mata_nfa.minimize(aut)
    num_states = len(aut.get_reachable_states())
    dot = aut.to_dot_str()
    return dot, num_states
