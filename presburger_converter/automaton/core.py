from presburger_converter.parsing import parser, expander, macro_preprocessor
from presburger_converter.automaton.automaton_builder import build_automaton, is_deterministic, determinize
import libmata.nfa.nfa as mata_nfa

def formula_to_aut(formula: str):
    #tree = parser.parse_formula(formula)
    tree = macro_preprocessor.parse_with_macros(formula)
    pure_tree = expander.expand_shorthands(tree)

    aut, variables = build_automaton(pure_tree)
    if not is_deterministic(aut):
        aut = determinize(aut)
    aut = mata_nfa.minimize(aut)
    return aut, variables

def test_formula(formula: str):
    #tree = parser.parse_formula(formula)
    tree = macro_preprocessor.parse_with_macros(formula)
    pure_tree = expander.expand_shorthands(tree)
    aut, variables = build_automaton(pure_tree)
    if not is_deterministic(aut):
        aut = determinize(aut)
    aut = mata_nfa.minimize(aut)
    num_states = len(aut.get_reachable_states())
    dot = aut.to_dot_str()
    return dot, num_states