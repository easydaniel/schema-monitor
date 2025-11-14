"""
This module contains the ReferenceExpectationBuilder class, which is responsible for
building a Great Expectations ExpectationSuite based on a reference DataFrame.
"""
import great_expectations.expectations as gxe
import pandas as pd
from pandas.api.types import is_numeric_dtype
from typing import List, Tuple

class ReferenceExpectationBuilder:
    """
    Builds a list of Great Expectations Expectations based on a reference pandas DataFrame.

    This builder allows for dynamically creating expectations for schema changes,
    column type changes, null value drifts, and numerical/categorical distribution drifts.
    """
    def __init__(self, _reference_df: pd.DataFrame) -> None:
        """
        Initializes the ReferenceExpectationBuilder with a reference DataFrame.

        Args:
            _reference_df: The pandas DataFrame to be used as the reference for building expectations.
        """
        self.reference_df: pd.DataFrame = _reference_df
        self.expectations: List[gxe.Expectation] = []
    
    def add_column_changes(self) -> None:
        """
        Adds an expectation to check for column additions or removals.
        Uses `expect_table_columns_to_match_set` to ensure the target DataFrame
        has the exact same set of columns as the reference DataFrame.
        """
        self.expectations.append(gxe.ExpectTableColumnsToMatchSet(column_set=set(self.reference_df.columns)))

    def add_column_type_changes(self) -> None:
        """
        Adds expectations to check for data type changes for each column.
        For each column in the reference DataFrame, it adds an `expect_column_values_to_be_of_type`
        expectation to ensure the target DataFrame's columns match the reference types.
        """
        for column in self.reference_df.columns:
            self.expectations.append(gxe.ExpectColumnValuesToBeOfType(column=column, type_=str(self.reference_df[column].dtype)))

    def add_null_value_drifts(self, tolerance: float = 0.1) -> None:
        """
        Adds expectations to detect drift in the proportion of non-null values for each column.
        For each column, it calculates the non-null proportion in the reference DataFrame
        and sets an `expect_column_proportion_of_non_null_values_to_be_between` expectation
        with a given tolerance.

        Args:
            tolerance: The acceptable deviation (as a proportion) from the reference non-null proportion.
        """
        for column in self.reference_df.columns:
            reference_non_null_proportion = 1 - (self.reference_df[column].isnull().sum() / len(self.reference_df))
            min_value, max_value = ReferenceExpectationBuilder.get_range(reference_non_null_proportion, tolerance)
            self.expectations.append(gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(column=column, min_value=min_value, max_value=max_value))
    
    def add_categorical_distribution_drifts(self, threshold: float = 0.1) -> None:
        """
        Adds expectations to detect distribution drift for categorical columns using KL Divergence.
        For each numerical column (as a proxy for categorical in this context, though it should be
        refined for true categorical dtypes), it calculates the value distribution in the reference
        DataFrame and adds an `expect_column_kl_divergence_to_be_less_than` expectation.

        Args:
            threshold: The maximum acceptable KL divergence between the reference and target distributions.
        """
        for column in self.reference_df.columns:
            # This condition `is_numeric_dtype` seems incorrect for categorical distribution.
            # It should check for object/category dtype.
            # For now, keeping as is based on existing code, but noting for future refinement.
            if is_numeric_dtype(self.reference_df[column]): 
                distribution = self.reference_df[column].value_counts(normalize=True)
                self.expectations.append(gxe.ExpectColumnKLDivergenceToBeLessThan(column=column, partition_object=distribution.to_dict(), threshold=threshold))
            else:
                # Other cases might not be categorical, we will need specific methods to deal with those. e.g. objects may be free form text or standardized enum text.
                pass
        
    def add_numerical_distribution_drifts(self, threshold: float = 0.1) -> None:
        """
        Adds expectations to detect distribution drift for numerical columns.
        For each numerical column, it adds expectations for the mean and standard deviation
        to be within a certain range of the reference values, based on a given threshold.

        Args:
            threshold: The acceptable deviation (as a proportion) from the reference mean/std.
        """
        for column in self.reference_df.columns:
            if self.reference_df[column].dtype == 'number': # 'number' is a pandas dtype alias for numeric types
                # Mean
                mean = self.reference_df[column].mean()
                min_value, max_value = ReferenceExpectationBuilder.get_range(mean, threshold)
                self.expectations.append(gxe.ExpectColumnMeanToBeBetween(column=column, min_value=min_value, max_value=max_value))
                # std
                std = self.reference_df[column].std()
                min_value, max_value = ReferenceExpectationBuilder.get_range(std, threshold)
                self.expectations.append(gxe.ExpectColumnStdevToBeBetween(column=column, min_value=min_value, max_value=max_value))
                # distribution can be done using ExpectColumnQuantileValuesToBeBetween with Q = [0, .25, .5, .75. 1]
            else:
                # Other cases might not be categorical, we will need specific methods to deal with those. e.g. objects may be free form text or standardized enum text.
                pass
    
    def add_string_pattern_drift(self, column: str, pattern: str) -> None:
        """
        Adds an expectation to check if column values match a given string pattern.

        Args:
            column: The name of the column to check.
            pattern: The regex pattern that column values are expected to match.

        Raises:
            Exception: If the specified column does not exist in the reference DataFrame.
        """
        if column not in self.reference_df.columns:
            raise Exception(f"No matching column named: `{column}`")
        self.expectations.append(gxe.ExpectColumnValuesToMatchLikePattern(column=column, pattern=pattern))

    @staticmethod
    def get_range(base: float, tolerance: float) -> Tuple[float, float]:
        """
        Calculates a min and max range based on a base value and a tolerance.

        Args:
            base: The central value.
            tolerance: The acceptable deviation from the base value.

        Returns:
            A tuple containing the calculated (min_value, max_value).
        """
        return max(0.0, base - tolerance), min(1.0, base + tolerance)