import subprocess
import os
from analysis.data_processing import process_csv
from analysis.run_tests import run_tests_from_csv
from analysis.generate_tests import generate_test_dataframe
import pandas as pd
import re

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
    timeout: int,
    data_type: str
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

    # 4.5) Filtering description
    filter_desc_map = {
        "raw": "no filtering",
        "outlier": "outliers removed",
        "collapsed": "collapsed formulas removed",
        "both": "outliers and collapsed formulas removed"
    }
    filter_note = filter_desc_map.get(data_type, "unknown filtering")

    # 5) Compute averages and dump new CSVs
    states_csv = f"plots/{test_for}/{name}/states_vs_{name}_{data_type}.csv"
    time_csv   = f"plots/{test_for}/{name}/time_vs_{name}_{data_type}.csv"

    df_s = pd.read_csv(states_csv)
    avg_s = df_s.groupby(x_field)["num_states"].mean().reset_index()
    avg_states_csv = f"plots/{test_for}/{name}/avg_states_vs_{name}_{data_type}.csv"
    avg_s.to_csv(avg_states_csv, index=False)

    df_t = pd.read_csv(time_csv)
    avg_t = df_t.groupby(x_field)["time_ms"].mean().reset_index()
    avg_time_csv = f"plots/{test_for}/{name}/avg_time_vs_{name}_{data_type}.csv"
    avg_t.to_csv(avg_time_csv, index=False)

    # 6) Common caption tail
    common = (
        f"variables={var_ct}, constant midpoint={const_mid}, mode={mode}, "
        f"timeout={timeout}\\,s. Constants sampled from "
        f"$[{const_mid-10},{const_mid+10}]$. ({filter_note})"
    )

    # 7) Snippet for states‐figure (with avg-line)
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

    # 8) Snippet for time‐figure (with avg-line)
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

    # 9) Insert depending on test_against
    if test_against == "states":
        insertion = fig_states + "\n\n"
    elif test_against == "time":
        insertion = fig_time + "\n\n"
    elif test_against == "both":
        insertion = fig_states + "\n\n" + fig_time + "\n\n"
    else:
        raise ValueError(f"Unknown test type: {test_against}")

    new_content = content.replace("\\end{document}", insertion + "\\end{document}")

    # 10) Write back
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

def construct_and_run_tests(test_for: str, test_against: str, count_values: list, c_values: list, c_variance: int, variable_counts: list, depths: list, variable_is_depth: bool, modes: list, position: str, sample_size: int, timeout: int, data_filter: list, coefficient_range: range):
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
    plot_path_states = f"plots/{test_for}/{name}/states_vs_{name}"
    plot_path_time = f"plots/{test_for}/{name}/time_vs_{name}"

    # Ensure output directories exist
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_result_path), exist_ok=True)
    os.makedirs(os.path.dirname(plot_path_states), exist_ok=True)

    # Generate and run tests
    generate_test_dataframe(position, test_path, count_values, c_values, c_variance, variable_counts, depths, variable_is_depth, modes, sample_size, coefficient_range)
    run_tests_from_csv(test_path, test_result_path,  timeout)

    # Process CSV for LaTeX plots
    for data_type in data_filter:
        if test_against in ["states", "both"]:
            process_csv(test_result_path, plot_path_states, test_for, "num_states", data_type)
        if test_against in ["time", "both"]:
            process_csv(test_result_path, plot_path_time, test_for, "time_ms", data_type)
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
            timeout= timeout,
            data_type = data_type
        )
    compile_latex("tests.tex")
    print("Compilation complete! See tests.pdf.")




if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    timeout = 300  # max time per test in seconds
    sample_size = 10  # number of samples per test
    variable_counts = [4]  # number of variables in each formula
    count_values = [2]  # number of junctions
    c_values = [5]  # constant midpoint
    c_variance = 5 # how much the constant can vary around the midpoint
    depths = [1,2,3,4]  #  ∀/∃ layers baseline
    variable_is_depth = False # if True, depth is set to variable_count - 1, only iterate through variable_count
    modes = ["and"]  # could be "random", "or" or "and"
    position = "outside"  # atomic-level quantifiers
    test_for = "depth"  # could be "junctions", "constant" or "depth"
    test_against = "both"  # could be "both", "states" or "time"
    data_filter = ["raw"] # could be "outlier", "collapsed", "raw" or "both"
    coefficient_range = range(-3, 4)  # Coefficients picked randomly from this range


    construct_and_run_tests(
        test_for=test_for,
        test_against=test_against,
        count_values=count_values,
        c_values=c_values,
        c_variance = c_variance,
        variable_counts=variable_counts,
        depths=depths,
        variable_is_depth=variable_is_depth,
        modes=modes,
        position=position,
        sample_size=sample_size,
        timeout=timeout,
        data_filter=data_filter,
        coefficient_range=coefficient_range
    )