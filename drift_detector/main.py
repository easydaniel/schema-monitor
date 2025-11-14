"""
This is the main entry point for the drift_detector command-line tool.
"""

import argparse
import pandas as pd
from pathlib import Path
from core.validator import run_validation
from pprint import pprint as pp

def load_dataframe(file_path: str) -> pd.DataFrame:
    """
    Loads a file into a pandas DataFrame, supporting CSV and Excel formats.

    Args:
        file_path: The path to the file.

    Returns:
        A pandas DataFrame with the loaded data.
    
    Raises:
        ValueError: If the file extension is not supported.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Error: The file '{file_path}' was not found.")

    suffix = path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: '{suffix}'. Please use a CSV or Excel file.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Drift Detector CLI Tool")
    parser.add_argument("--reference", type=str, required=True, help="Path to the reference dataset (CSV or Excel).")
    parser.add_argument("--target", type=str, required=True, help="Path to the target dataset (CSV or Excel).")

    args = parser.parse_args()

    try:
        print(f"Loading reference file: {args.reference}")
        reference_df = load_dataframe(args.reference)
        print(f"Reference DataFrame loaded successfully. Shape: {reference_df.shape}")

        print(f"Loading target file: {args.target}")
        target_df = load_dataframe(args.target)
        print(f"Target DataFrame loaded successfully. Shape: {target_df.shape}")

        print("\nStarting drift analysis...")
        
        drift_report = run_validation(reference_df, target_df)
        
        if not drift_report.success:
            failures = []
            for result in drift_report.results:
                if not result.success:
                    config = result.expectation_config
                    failures.append({
                        "type_of_check": config.type,
                        "severity": config.severity,
                        "expected_data": config.kwargs,
                        "observed_data": result.result,
                    })
            pp(failures)
        else:
            print("\nData valid, all expectations passed!")

    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
