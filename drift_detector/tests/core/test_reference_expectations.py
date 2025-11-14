"""
Unit tests for the ReferenceExpectationBuilder class.
"""
import pytest
import pandas as pd
import great_expectations.expectations as gxe
from core.reference_expectations import ReferenceExpectationBuilder

@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3],
        "value": [10.0, 20.0, 30.0],
        "text": ["A", "B", "C"],
        "all_null": [None, None, None]
    })

def test_builder_initialization(sample_df: pd.DataFrame):
    """Tests that the builder is initialized correctly."""
    builder = ReferenceExpectationBuilder(sample_df)
    assert builder.reference_df.equals(sample_df)
    assert builder.expectations == []

def test_add_column_changes(sample_df: pd.DataFrame):
    """Tests the add_column_changes method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_column_changes()
    assert len(builder.expectations) == 1
    exp = builder.expectations[0]
    assert isinstance(exp, gxe.ExpectTableColumnsToMatchSet)
    assert exp.column_set == {"id", "value", "text", "all_null"}

def test_add_column_type_changes(sample_df: pd.DataFrame):
    """Tests the add_column_type_changes method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_column_type_changes()
    assert len(builder.expectations) == 4
    
    type_map = {
        "id": "int64",
        "value": "float64",
        "text": "object",
        "all_null": "object"
    }
    
    for exp in builder.expectations:
        assert isinstance(exp, gxe.ExpectColumnValuesToBeOfType)
        col = exp.column
        assert exp.type_ == type_map[col]

def test_add_null_value_drifts(sample_df: pd.DataFrame):
    """Tests the add_null_value_drifts method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_null_value_drifts(tolerance=0.1)
    assert len(builder.expectations) == 4

    # Test the 'text' column (0/3 = 0.0 nulls -> 1.0 non-null)
    text_exp = next(exp for exp in builder.expectations if exp.column == "text")
    assert isinstance(text_exp, gxe.ExpectColumnProportionOfNonNullValuesToBeBetween)
    assert text_exp.min_value == pytest.approx(1.0 - 0.1)
    assert text_exp.max_value == pytest.approx(min(1.0, 1.0 + 0.1))

    # Test the 'all_null' column (100% nulls -> 0.0 non-null)
    all_null_exp = next(exp for exp in builder.expectations if exp.column == "all_null")
    assert isinstance(all_null_exp, gxe.ExpectColumnProportionOfNonNullValuesToBeBetween)
    assert all_null_exp.min_value == 0.0 # max(0.0, 0.0 - 0.1)
    assert all_null_exp.max_value == 0.1 # min(1.0, 0.0 + 0.1)

def test_add_categorical_distribution_drifts(sample_df: pd.DataFrame):
    """Tests the add_categorical_distribution_drifts method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_categorical_distribution_drifts(threshold=0.2)
    
    # Based on the new logic, only 'all_null' (non-numeric, low cardinality) should add an expectation
    assert len(builder.expectations) == 1

    all_null_exp = next(exp for exp in builder.expectations if exp.column == "all_null")
    assert isinstance(all_null_exp, gxe.ExpectColumnKLDivergenceToBeLessThan)
    assert all_null_exp.threshold == 0.2
    # Check if partition object is created correctly (only None value)
    assert all_null_exp.partition_object == {None: pytest.approx(1.0)}

def test_add_numerical_distribution_drifts(sample_df: pd.DataFrame):
    """Tests the add_numerical_distribution_drifts method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_numerical_distribution_drifts(threshold=0.1)
    
    # The method should add 2 expectations (mean, std) for each numeric column ("id", "value")
    assert len(builder.expectations) == 4

    # Check the mean expectation for the 'value' column
    value_mean_exp = next(
        exp for exp in builder.expectations 
        if exp.column == "value" and isinstance(exp, gxe.ExpectColumnMeanToBeBetween)
    )
    
    mean = sample_df['value'].mean()
    assert value_mean_exp.min_value == pytest.approx(mean - (abs(mean) * 0.1))
    assert value_mean_exp.max_value == pytest.approx(mean + (abs(mean) * 0.1))


def test_add_string_pattern_drift(sample_df: pd.DataFrame):
    """Tests the add_string_pattern_drift method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_string_pattern_drift("text", "A|B|C")
    assert len(builder.expectations) == 1
    exp = builder.expectations[0]
    assert isinstance(exp, gxe.ExpectColumnValuesToMatchLikePattern)
    assert exp.column == "text"
    assert exp.like_pattern == "A|B|C"

def test_add_string_pattern_drift_invalid_column(sample_df: pd.DataFrame):
    """Tests that an exception is raised for an invalid column."""
    builder = ReferenceExpectationBuilder(sample_df)
    with pytest.raises(Exception, match="No matching column named: `invalid_col`"):
        builder.add_string_pattern_drift("invalid_col", ".*")

def test_add_categorical_distribution_drifts_non_numeric(sample_df: pd.DataFrame):
    """
    Tests that add_categorical_distribution_drifts does not add expectations
    for non-numeric columns (as per current implementation's if condition).
    """
    builder = ReferenceExpectationBuilder(sample_df)
    # The 'text' column is object (non-numeric)
    builder.add_categorical_distribution_drifts(threshold=0.2)
    
    # Assert that no expectations were added for the 'text' column
    assert not any(exp.column == "text" for exp in builder.expectations)

def test_add_numerical_distribution_drifts_non_numeric(sample_df: pd.DataFrame):
    """
    Tests that add_numerical_distribution_drifts does not add expectations
    for non-numeric columns.
    """
    builder = ReferenceExpectationBuilder(sample_df)
    # The 'text' column is object (non-numeric)
    builder.add_numerical_distribution_drifts(threshold=0.1)
    
    # Assert that no expectations were added for the 'text' column
    assert not any(exp.column == "text" for exp in builder.expectations)
