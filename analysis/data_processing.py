import pandas as pd


def process_csv(file_path: str, output_path: str, input_col: str, output_col: str):
    """
    Reads a CSV, removes rows with missing 'num_states', fills missing 'time_ms',
    and exports a new CSV with two selected columns.
    """
    # Read CSV
    df = pd.read_csv(file_path)
    #print(df.head())
    # FIX: Strip whitespace from all column names
    df.columns = df.columns.str.strip()

    # --- Data cleaning ---

    # Fill missing 'time_ms' values with a default
    if 'time_ms' in df.columns:
        df['time_ms'] = df['time_ms'].fillna(10000)

    # Remove rows where 'num_states' is missing
    if 'num_states' in df.columns:
        df.dropna(subset=['num_states'], inplace=True)
    # Remove trivial cases with only one state
    #df = df[df.num_states > 1]
    # --- Column selection and error handling ---
    if input_col == "junctions":
        input_col = "count"
    if input_col not in df.columns or output_col not in df.columns:
        raise ValueError(f"One or both columns '{input_col}' and '{output_col}' not found in CSV.")

    selected_df = df[[input_col, output_col]]
    if input_col == "count":
        selected_df = selected_df.rename(columns={"count": "junctions"})
    # ... (rest of the function is the same)


    # --- Export final data ---
    selected_df.to_csv(output_path, index=False)
    print(f"Exported selected data to {output_path}")

#process_csv("test_results/depth/results_depth_outside_one_four_zero_five_three_random.csv", "depth", "time_ms")
#process_csv("test_results/depth/results_depth_outside_one_four_zero_five_three_random.csv", "depth", "num_states")