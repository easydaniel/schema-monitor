# Schema Monitor

This project is a data validation framework that compares two data sources (CSV or Excel files) and detects drift between them. It uses the Great Expectations library for data validation.

## Installation

1.  Clone this repository.
2.  Install the required Python libraries:

    ```bash
    pip3 install pandas great_expectations openpyxl
    ```

## Usage

To run the framework, use the following command:

```bash
python3 main.py <file1> <file2>
```

Replace `<file1>` and `<file2>` with the paths to your data files.

### Example

```bash
python3 main.py data1.csv data2.csv
```

## How it works

1.  **Data Loading:** The framework loads the two data sources into pandas DataFrames. It automatically detects the file type (CSV or Excel) based on the file extension.
2.  **Data Validation:** It uses Great Expectations to validate the data. In this initial version, it checks if the columns of the two data sources are the same.
3.  **Drift Detection:** It uses a custom `DriftDetection` module to compare the two data sources for drift. This module is currently a placeholder and will be implemented in the future.

## Future Work

*   Implement the drift detection logic in the `DriftDetection` module.
*   Add more Great Expectations to the validation suite.
*   Add support for more data sources.
*   Create a web-based dashboard to visualize the validation results.