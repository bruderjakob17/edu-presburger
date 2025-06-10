import pandas as pd


def process_csv(file_path: str, input_col: str, output_col: str):
    """
    Reads a CSV, removes rows with missing 'num_states', fills missing 'time_ms',
    and exports a new CSV with two selected columns.
    """
    # Read CSV
    df = pd.read_csv(file_path)
    print(df.head())
    # FIX: Strip whitespace from all column names
    df.columns = df.columns.str.strip()

    # --- Data cleaning ---

    # Fill missing 'time_ms' values with a default
    if 'time_ms' in df.columns:
        df['time_ms'] = df['time_ms'].fillna(10000)

    # Remove rows where 'num_states' is missing
    if 'num_states' in df.columns:
        df.dropna(subset=['num_states'], inplace=True)

    # --- Column selection and error handling ---

    if input_col not in df.columns or output_col not in df.columns:
        raise ValueError(f"One or both columns '{input_col}' and '{output_col}' not found in CSV.")

    selected_df = df[[input_col, output_col]]

    # ... (rest of the function is the same)

    # --- Filename determination ---
    filename = ""
    if output_col == "time_ms":
        filename = f"{input_col}_vs_time.csv"
    elif output_col == "num_states":
        filename = f"{input_col}_vs_states.csv"
    else:
        filename = f"{input_col}_vs_{output_col}.csv"

    # --- Export final data ---
    selected_df.to_csv(filename, index=False)
    print(f"Exported selected data to {filename}")

process_csv("test_results/results_num_disjunctions.csv", "count", "time_ms")
process_csv("test_results/results_num_disjunctions.csv", "count", "num_states")