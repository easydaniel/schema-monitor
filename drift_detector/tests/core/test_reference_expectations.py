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
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "A", "B", "B", "C", None],
        "value": [10.0, 10.2, 20.0, 20.3, 30.0, 30.5],
        "all_null": [None, None, None, None, None, None]
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
    assert exp.column_set == {"id", "category", "value", "all_null"}

def test_add_column_type_changes(sample_df: pd.DataFrame):
    """Tests the add_column_type_changes method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_column_type_changes()
    assert len(builder.expectations) == 4
    
    type_map = {
        "id": "int64",
        "category": "object",
        "value": "float64",
        "all_null": "object" # Pandas defaults null columns to object
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

    # Test the 'category' column (1/6 = 0.166 nulls -> 0.833 non-null)
    category_exp = next(exp for exp in builder.expectations if exp.column == "category")
    assert isinstance(category_exp, gxe.ExpectColumnProportionOfNonNullValuesToBeBetween)
    assert category_exp.min_value == pytest.approx(5/6 - 0.1)
    assert category_exp.max_value == pytest.approx(5/6 + 0.1)

    # Test the 'all_null' column (100% nulls -> 0.0 non-null)
    all_null_exp = next(exp for exp in builder.expectations if exp.column == "all_null")
    assert isinstance(all_null_exp, gxe.ExpectColumnProportionOfNonNullValuesToBeBetween)
    assert all_null_exp.min_value == 0.0 # max(0.0, 0.0 - 0.1)
    assert all_null_exp.max_value == 0.1 # min(1.0, 0.0 + 0.1)

def test_add_categorical_distribution_drifts(sample_df: pd.DataFrame):
    """Tests the add_categorical_distribution_drifts method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_categorical_distribution_drifts(threshold=0.2)
    
    # This method only acts on numeric columns in the current implementation
    numeric_cols_for_cat_test = ["id", "value"]
    assert len(builder.expectations) == len(numeric_cols_for_cat_test)

    id_exp = next(exp for exp in builder.expectations if exp.column == "id")
    assert isinstance(id_exp, gxe.ExpectColumnKLDivergenceToBeLessThan)
    assert id_exp.threshold == 0.2
    # Check if partition object is created correctly
    assert 1 in id_exp.partition_object
    assert id_exp.partition_object[1] == pytest.approx(1/6)

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
    assert value_mean_exp.min_value == pytest.approx(mean - 0.1)
    assert value_mean_exp.max_value == pytest.approx(mean + 0.1)


def test_add_string_pattern_drift(sample_df: pd.DataFrame):
    """Tests the add_string_pattern_drift method."""
    builder = ReferenceExpectationBuilder(sample_df)
    builder.add_string_pattern_drift("category", "A|B|C")
    assert len(builder.expectations) == 1
    exp = builder.expectations[0]
    assert isinstance(exp, gxe.ExpectColumnValuesToMatchLikePattern)
    assert exp.column == "category"
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
    # The 'category' column is object (non-numeric)
    builder.add_categorical_distribution_drifts(threshold=0.2)
    
    # Assert that no expectations were added for the 'category' column
    assert not any(exp.column == "category" for exp in builder.expectations)

def test_add_numerical_distribution_drifts_non_numeric(sample_df: pd.DataFrame):
    """
    Tests that add_numerical_distribution_drifts does not add expectations
    for non-numeric columns.
    """
    builder = ReferenceExpectationBuilder(sample_df)
    # The 'category' column is object (non-numeric)
    builder.add_numerical_distribution_drifts(threshold=0.1)
    
    # Assert that no expectations were added for the 'category' column
    assert not any(exp.column == "category" for exp in builder.expectations)
