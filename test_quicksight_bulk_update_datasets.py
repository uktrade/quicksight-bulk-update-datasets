import datetime

import botocore.session
import pytest
from botocore.stub import Stubber, ANY
from typer.testing import CliRunner

from quicksight_bulk_update_datasets import app

runner = CliRunner()


@pytest.fixture()
def quicksight_stubber(mocker):
    # At the time of writing moto doesn't support enough of Quicksight's API to be useful. Also
    # botocore's stubber docs don't make it clear, but it looks like you have to inject the exact
    # same client that's stubbed into the code under test
    session = botocore.session.get_session()
    client = session.create_client('quicksight', region_name="us-east-1")
    mocker.patch("boto3.Session.client", return_value=client)

    stubber = Stubber(client)

    with stubber:
        yield stubber


def test_rename_schema_no_updates(quicksight_stubber):
    response = {
        'DataSetSummaries': [
            {
                'DataSetId': '1',
            },
        ]
    }
    quicksight_stubber.add_response('list_data_sets', response)

    response = {
        'DataSet': {},
    }
    quicksight_stubber.add_response('describe_data_set', response)

    result = runner.invoke(app, ["--account-id", "123456789012", "--source-schema", "dit", "--target-schema", "dbt"])

    assert result.exception is None
    assert result.exit_code == 0
    quicksight_stubber.assert_no_pending_responses()


def test_rename_schema_custom_sql(quicksight_stubber):
    response = {
        'DataSetSummaries': [
            {
                'DataSetId': '1',
            },
        ]
    }
    quicksight_stubber.add_response('list_data_sets', response)

    response = {
        'DataSet': {
            'DataSetId': '1',
            'PhysicalTableMap': {
                '2': {
                    'CustomSql': {
                        'Name': 'My SQL',
                        'DataSourceArn': 'any',
                        'SqlQuery': 'SELECT a, dit.my_table.* FROM dit.my_table, another.table',
                    },
                },
            },
            'Name': 'My dataset',
            'ImportMode': 'any',
        },
    }
    quicksight_stubber.add_response('describe_data_set', response)

    request = {
        'AwsAccountId': '123456789012',
        'DataSetId': '1',
        'PhysicalTableMap': {
            '2': {
                'CustomSql': {
                    'Name': 'My SQL',
                    'DataSourceArn': 'any',
                    'SqlQuery': 'SELECT a,\n       dbt.my_table.*\nFROM dbt.my_table, another."table"',
                },
            },
        },
        'Name': 'My dataset',
        'ImportMode': 'any',
    }
    response = {
        'DataSetId': '1',
    }
    quicksight_stubber.add_response('update_data_set', response, request)

    result = runner.invoke(app, ["--account-id", "123456789012", "--source-schema", "dit", "--target-schema", "dbt", "--no-prompt"])

    assert result.exception is None
    assert result.exit_code == 0
    quicksight_stubber.assert_no_pending_responses()
