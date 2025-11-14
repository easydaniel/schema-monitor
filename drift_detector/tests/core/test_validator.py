"""
Tests for the Great Expectations validator module.
"""
import pytest
import pandas as pd
from core.validator import run_validation

@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Provides sample data for testing."""
    reference_df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["A", "B", "C", "D", "E"],
        "value": [10.1, 12.3, 11.1, 9.8, 10.5]
    })
    return reference_df

def test_no_drift(sample_data: pd.DataFrame) -> None:
    """
    Test case where the target data is identical to the reference data.
    Expect no drift to be detected.
    """
    report = run_validation(sample_data, sample_data.copy())
    assert report.success is True

def test_schema_drift_missing_column(sample_data: pd.DataFrame) -> None:
    """
    Test case with schema drift (a column is missing).
    """
    target_df = sample_data.copy()
    target_df = target_df.drop(columns=["name"])
    
    report = run_validation(sample_data, target_df)
    assert report.success is False
    # Find the specific failing expectation
    failed_results = [r for r in report.results if not r.success]
    assert any(r.expectation_config.type == "expect_table_columns_to_match_set" for r in failed_results)

def test_schema_drift_added_column(sample_data: pd.DataFrame) -> None:
    """
    Test case with schema drift (a column is added).
    """
    target_df = sample_data.copy()
    target_df["new_column"] = "test"
    
    report = run_validation(sample_data, target_df)
    assert report.success is False
    # Find the specific failing expectation
    failed_results = [r for r in report.results if not r.success]
    assert any(r.expectation_config.type == "expect_table_columns_to_match_set" for r in failed_results)

def test_empty_target(sample_data: pd.DataFrame) -> None:
    """
    Test case where the target dataframe is empty.
    """
    empty_df = pd.DataFrame(columns=sample_data.columns)
    report = run_validation(sample_data, empty_df)
    assert report.success is False
    # It should fail the non-null check, among others
    failed_results = [r for r in report.results if not r.success]
    assert any(r.expectation_config.type == "expect_column_proportion_of_non_null_values_to_be_between" for r in failed_results)

def test_empty_reference(sample_data: pd.DataFrame) -> None:
    """
    Test case where the reference dataframe is empty.
    """
    empty_df = pd.DataFrame(columns=sample_data.columns)
    report = run_validation(empty_df, sample_data)
    # This will likely fail multiple checks, starting with column types and nulls
    assert report.success is False

def test_both_empty(sample_data: pd.DataFrame) -> None:
    """
    Test case where both dataframes are empty. This should result in no drift.
    """
    empty_df = pd.DataFrame(columns=sample_data.columns)
    report = run_validation(empty_df, empty_df.copy())
    assert report.success is True

def test_all_null_column() -> None:
    """
    Test case where a column contains only null values.
    """
    reference = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    target = pd.DataFrame({"id": [1, 2, 3], "value": [None, None, None]})
    report = run_validation(reference, target)
    assert report.success is False
    failed_results = [r for r in report.results if not r.success]
    # It should fail the non-null check for the 'value' column
    assert any(
        r.expectation_config.type == "expect_column_proportion_of_non_null_values_to_be_between" and
        r.expectation_config.kwargs.get("column") == "value"
        for r in failed_results
    )

def test_zero_variance_column() -> None:
    """
    Test case where a numerical column has zero variance (all values are the same).
    The standard deviation check should handle this gracefully.
    """
    reference = pd.DataFrame({"value": [100, 100, 100]})
    target = pd.DataFrame({"value": [100, 100, 100]})
    report = run_validation(reference, target)
    assert report.success is True
