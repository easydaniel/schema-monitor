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
