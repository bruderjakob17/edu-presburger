from libmata import alphabets as alph, parser as mata_parser
import tempfile
import os
from typing import Callable

def nfa_to_mata(
    aut,
    state_prefix: str = "q",
    symbol_to_str: Callable[[int], str] = str,
) -> str:
    """Return a @NFA-explicit representation of *aut*."""
    q = lambda sid: f"{state_prefix}{sid}"

    lines = ["@NFA-explicit",
             f"%Initial {' '.join(q(s) for s in sorted(aut.initial_states))}",
             f"%Final  {' '.join(q(s) for s in sorted(aut.final_states))}"]

    for t in sorted(aut.get_trans_as_sequence(),
                    key=lambda tr: (tr.source, tr.symbol, tr.target)):
        lines.append(f"{q(t.source)} {symbol_to_str(t.symbol)} {q(t.target)}")

    return "\n".join(lines)



def nfa_from_mata(mata_string):
    """
    Parses a MATA automaton from a string by first saving it to a temporary file,
    then reading it with the mata_parser, and finally deleting the temporary file.

    Args:
        mata_string (str): The MATA automaton definition as a string.

    Returns:
        The automaton object returned by mata_parser.from_mata.
    """
    alpha = alph.IntAlphabet()
    temp_file = None  # Initialize temp_file to None for the finally block

    try:
        # Create a temporary file with a .mata extension
        # NamedTemporaryFile ensures it has a name on the filesystem
        # delete=False means we'll manually delete it in the finally block
        # mode='w+' allows writing and reading, text=True for string content
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".mata", delete=False, encoding='utf-8') as temp_fp:
            temp_fp.write(mata_string)
            temp_file_path = temp_fp.name

        # The file is now written and closed, so mata_parser can read it
        aut = mata_parser.from_mata(temp_file_path, alpha)

        return aut
    finally:
        # Ensure the temporary file is deleted, even if an error occurred
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            # print(f"Temporary file '{temp_file_path}' deleted.") # Optional: for debugging

