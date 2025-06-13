import os

import pandas as pd


def process_csv(file_path: str, output_path: str, input_col: str, output_col: str, data_filter: list):
    """
    Reads a CSV, removes rows with missing 'num_states', fills missing 'time_ms',
    removes outliers in output column, and exports a new CSV with two selected columns.
    """
    # Read CSV
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()  # Strip whitespace from all column names
    #print(df.head())
    # --- Data cleaning ---
    if 'time_ms' in df.columns:
        df.dropna(subset=['time_ms'], inplace=True)
    if 'num_states' in df.columns:
        df.dropna(subset=['num_states'], inplace=True)

    # Column aliasing
    if input_col == "junctions":
        input_col = "count"

    if input_col not in df.columns or output_col not in df.columns:
        raise ValueError(f"One or both columns '{input_col}' and '{output_col}' not found in CSV.")

    # --- Group-wise IQR filtering ---
    def filter_group(group):
        Q1 = group[output_col].quantile(0.25)
        Q3 = group[output_col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return group[(group[output_col] >= lower) & (group[output_col] <= upper)]

    #Filter outliers based on the specified data_filter
    if "outlier" == data_filter or "both" == data_filter:
        df = df.groupby(input_col, group_keys=False).apply(filter_group)

    #Filter collapsed based on the specified data_filter (num_states = 1)
    if "collapsed" == data_filter or "both" == data_filter:
        df = df[df['num_states'] != 1]

    # --- Column selection ---
    selected_df = df[[input_col, output_col]]
    if input_col == "count":
        selected_df = selected_df.rename(columns={"count": "junctions"})

    # --- Export ---
    final_path = f"{output_path}_{data_filter}.csv"
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    selected_df.to_csv(final_path, index=False)
    print(f"Exported selected data to {final_path}")