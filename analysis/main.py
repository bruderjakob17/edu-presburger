import subprocess
import os
from analysis.data_processing import process_csv
from analysis.run_tests import run_tests_from_csv
from analysis.generate_tests import generate_test_dataframe
import re
import pandas as pd

def append_plot_snippet(
    tex_path: str,
    test_for: str,
    test_against: str,
    name: str,
    count_values: list,
    c_values: list,
    variable_counts: list,
    depths: list,
    modes: list,
    position: str,
    timeout: int
):
    # 1) Read document
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2) Determine section index
    index = len(re.findall(r'\\section\*', content)) + 1

    # 3) Shared params
    mode   = modes[0]
    var_ct = variable_counts[0]
    const_mid = c_values[0]

    # 4) Build X‐axis settings per test type
    if test_for == "depth":
        x_field = "depth"
        xlabel  = "Quantifier Depth"
        range_str = f"[{min(depths)},{max(depths)}]"
        extra = f"Quantifier depth $\\in$ {range_str} (position={position}), "
    elif test_for == "constant":
        x_field = "constant"
        xlabel  = "Constant Size"
        extra = ""
    elif test_for == "junctions":
        x_field = "junctions"
        xlabel  = "Number of Junctions"
        vals = ",".join(str(v) for v in count_values)
        extra = f"Junction count $\\in$ {{{vals}}}, "
    else:
        raise ValueError(f"Unknown test type: {test_for}")

    # 4.5) Compute averages and dump new CSVs
    # ---------------------------------------
    # States
    states_csv = f"plots/{test_for}/states_vs_{name}.csv"
    df_s = pd.read_csv(states_csv)
    avg_s = df_s.groupby(x_field)["num_states"].mean().reset_index()
    avg_states_csv = f"plots/{test_for}/avg_states_vs_{name}.csv"
    avg_s.to_csv(avg_states_csv, index=False)

    # Time
    time_csv = f"plots/{test_for}/time_vs_{name}.csv"
    df_t = pd.read_csv(time_csv)
    avg_t = df_t.groupby(x_field)["time_ms"].mean().reset_index()
    avg_time_csv = f"plots/{test_for}/avg_time_vs_{name}.csv"
    avg_t.to_csv(avg_time_csv, index=False)

    # 5) Common caption tail
    common = (
        f"variables={var_ct}, constant midpoint={const_mid}, mode={mode}, "
        f"timeout={timeout}\\,s. Constants sampled from "
        f"$[{const_mid-10},{const_mid+10}]$."
    )

    # 6) Snippet for states‐figure (with avg-line)
    fig_states = f"""
\\section*{{{index}. {test_for.capitalize()} / {mode.upper()} / C={const_mid}}}
\\begin{{figure}}[H]
  \\centering
  \\begin{{tikzpicture}}
    \\begin{{axis}}[
      xlabel={{{xlabel}}},
      ylabel={{Number of States}},
      title={{{xlabel} vs. Number of States}},
      grid=major,
      width=12cm,
      height=8cm
    ]
      % scatter
      \\addplot+[
        only marks, mark=*
      ] table[
        col sep=comma,
        x={x_field}, y=num_states
      ] {{{states_csv}}};

      % average line
      \\addplot+[
        mark=none,
        thick,
        smooth
      ] table[
        col sep=comma,
        x={x_field}, y=num_states
      ] {{{avg_states_csv}}};
    \\end{{axis}}
  \\end{{tikzpicture}}
  \\caption{{{extra}{common}}}
\\end{{figure}}
""".strip()

    # 7) Snippet for time‐figure (with avg-line)
    fig_time = f"""
\\begin{{figure}}[H]
  \\centering
  \\begin{{tikzpicture}}
    \\begin{{axis}}[
      xlabel={{{xlabel}}},
      ylabel={{Time (ms)}},
      title={{{xlabel} vs. Time (ms)}},
      grid=major,
      width=12cm,
      height=8cm
    ]
      % scatter
      \\addplot+[
        only marks, mark=*
      ] table[
        col sep=comma,
        x={x_field}, y=time_ms
      ] {{{time_csv}}};

      % average line
      \\addplot+[
        mark=none,
        thick,
        smooth
      ] table[
        col sep=comma,
        x={x_field}, y=time_ms
      ] {{{avg_time_csv}}};
    \\end{{axis}}
  \\end{{tikzpicture}}
  \\caption{{{extra}{common}}}
\\end{{figure}}
""".strip()

    # 8) Insert according to what to test_against
    if test_against == "states":
        insertion = fig_states + "\n\n"
    elif test_against == "time":
        insertion = fig_time + "\n\n"
    elif test_against == "both":
        insertion = fig_states + "\n\n" + fig_time + "\n\n"
    else:
        raise ValueError(f"Unknown test type: {test_against}")

    new_content = content.replace("\\end{document}", insertion + "\\end{document}")

    # 9) Write back
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def compile_latex(tex_path: str):
    """
    Runs pdflatex twice (to resolve cross-references) on the given .tex file.
    """
    for i in range(2):
        print(f"[LaTeX] Pass {i+1}…")
        # -interaction=nonstopmode prevents it from stopping on errors
        # -halt-on-error makes it exit with non-zero code if something fails
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path],
            check=True
        )

def construct_and_run_tests(test_for: str, test_against: str, count_values: list, c_values: list, variable_counts: list, depths: list, modes: list, position: str, sample_size: int, timeout: int):
    # For depth tests
    range_start = min(depths)
    range_stop = max(depths)
    constant_size = c_values[0]
    variable_count = variable_counts[0]
    junction_count = count_values[0]
    mode = modes[0]

    # Construct filename base according to test type
    if test_for == "depth":
        name = f"depth_{position}_{range_start}_{range_stop}_{constant_size}_{variable_count}_{junction_count}_{mode}_{sample_size}"
    elif test_for == "constant":
        name = f"constant_{variable_count}_{junction_count}_{mode}_{sample_size}"
    elif test_for == "junctions":
        name = f"junctions_{variable_count}_{constant_size}_{mode}_{sample_size}"
    else:
        raise ValueError(f"Unknown test type: {test_for}")

    # Build paths
    test_path = f"tests/{test_for}/test_{name}.csv"
    test_result_path = f"test_results/{test_for}/results_{name}.csv"
    plot_path_states = f"plots/{test_for}/states_vs_{name}.csv"
    plot_path_time = f"plots/{test_for}/time_vs_{name}.csv"

    # Ensure output directories exist
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    os.makedirs(os.path.dirname(plot_path_states), exist_ok=True)

    # Generate and run tests
    generate_test_dataframe(position, test_path, count_values, c_values, variable_counts, depths, modes, sample_size)
    run_tests_from_csv(test_path, test_result_path,  timeout)

    # Process CSV for LaTeX plots
    if test_against in ["states", "both"]:
        process_csv(test_result_path, plot_path_states, test_for, "num_states")
    if test_against in ["time", "both"]:
        process_csv(test_result_path, plot_path_time, test_for, "time_ms")

    append_plot_snippet(
        tex_path="tests.tex",
        test_for=test_for,
        test_against=test_against,
        name=name,
        count_values=count_values,
        c_values=c_values,
        variable_counts=variable_counts,
        depths=depths,
        modes= modes,
        position= position,
        timeout= timeout
    )
    compile_latex("tests.tex")
    print("Compilation complete! See tests.pdf.")




if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    timeout = 60  # stays constant
    sample_size = 30  # unless noted
    variable_counts = [3]  # fixed for suites 1-3 & 5
    count_values = [1,2,3,4,5,6,7,8,9,10,11,12]  # “3-way” junction baseline
    c_values = [10]  # ±10
    depths = [0]  # one ∀/∃ layer baseline
    modes = ["random"]  # balanced 50 / 50
    position = "inside"  # atomic-level quantifiers
    test_for = "junctions"  # could also be "constant" or "depth"
    test_against = "both"  # could also be "states" or "time"
    #test_for = "junctions"  # could also be "constant" or "junctions"
    #test_against = "both"   # could also be "states" or "time"
    #count_values = [1,2,3,4,5]  # junction count
    #c_values = [10]              # constant size midpoint
    #variable_counts = [5]        # number of variables
    #depths = [0]                 # quantifier depth
    #timeout = 60
    #modes = ["or"]
    #position = "inside"          # "outside" only for depth tests
    #sample_size = 10           # number of samples per test

    construct_and_run_tests(
        test_for=test_for,
        test_against=test_against,
        count_values=count_values,
        c_values=c_values,
        variable_counts=variable_counts,
        depths=depths,
        modes=modes,
        position=position,
        sample_size=sample_size,
        timeout=timeout
    )