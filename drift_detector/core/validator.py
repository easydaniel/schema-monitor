"""
This module contains the core drift detection logic using Great Expectations.
"""
import pandas as pd
import great_expectations as gx
import great_expectations.expectations as gxe
from .reference_expectations import ReferenceExpectationBuilder


from great_expectations.core import ExpectationSuiteValidationResult


def run_validation(reference_df: pd.DataFrame, target_df: pd.DataFrame) -> ExpectationSuiteValidationResult:
    """
    Validates the target dataframe against a set of expectations derived from the reference dataframe
    using Great Expectations.

    This function sets up an ephemeral Great Expectations context, builds an ExpectationSuite
    based on the reference_df using a ReferenceExpectationBuilder, and then validates the
    target_df against this suite.

    Args:
        reference_df: The reference pandas DataFrame used to build the expectations.
        target_df: The target pandas DataFrame to be validated.

    Returns:
        An ExpectationSuiteValidationResult object containing the results of the validation.
    """
    context = gx.get_context(mode="ephemeral") # In-memory context

    data_source = context.data_sources.add_pandas(name="target")
    data_asset = data_source.add_dataframe_asset(name="target_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("target_batch")

    batch = batch_definition.get_batch(batch_parameters={ "dataframe": target_df })

    # 1. Create Expectation Suite from reference_df
    suite = gx.ExpectationSuite(name="drift_detector")

    builder = ReferenceExpectationBuilder(reference_df)

    # Define all rules here
    builder.add_column_changes()
    builder.add_column_type_changes()
    builder.add_null_value_drifts()
    builder.add_numerical_distribution_drifts()

    # 2. Create rules using reference df. These can be seperate to different rules.
    for expectation in builder.expectations:
        suite.add_expectation(expectation)
    
    # 3. Add the suite to context
    context.suites.add(suite)
    return batch.validate(suite)