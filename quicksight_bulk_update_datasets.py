#
# Update any Quicksight datasets with relational tables in the source schema to use the target schema.
#
# Run in dry run mode (Do this to test it)
# quicksight-bulk-update-datasets --account-id=<aws account id> --aws-profile=<aws profile name> --source-schema=<schema name> --target-schema=<schema name> --dry-run
#
# To run for real remove the "--dry-run" argument from the above command
#
# You will be prompted before each dataset is actually updated on Quicksight. To run it for all
# datasets without the prompt add the "--no-prompt" arg to the command
#
from typing_extensions import Annotated

import boto3
import typer
from botocore.exceptions import ClientError


app = typer.Typer()


def _fetch_datasets(client, account_id, dataset_id=None):
    if dataset_id is not None:
        yield client.describe_data_set(AwsAccountId=account_id, DataSetId=dataset_id)["DataSet"]
        return

    next_token = None
    while True:
        params = dict(AwsAccountId=account_id)
        if next_token is not None:
            params["NextToken"] = next_token
        response = client.list_data_sets(**params)
        for dataset in response.get("DataSetSummaries", []):
            try:
                yield client.describe_data_set(
                    AwsAccountId=account_id, DataSetId=dataset["DataSetId"]
                )["DataSet"]
            except ClientError as ex:
                print(
                    f"Error fetching detail for dataset {dataset['Name']}: {ex.response['Error']['Message']}"
                )
                continue

        next_token = response.get("NextToken")
        if not next_token:
            break

@app.command()
def rename_schema(
        account_id: Annotated[str, typer.Option("--account-id", "-a", help="The AWS account ID")],
        aws_profile: Annotated[str, typer.Option("--aws-profile", "-p", help="The profile to connect to AWS")],
        source_schema: Annotated[str, typer.Option("--source-schema", "-s", help="The schema that will be renamed")],
        target_schema: Annotated[str, typer.Option("--target-schema", "-t", help="The new name of the source schema")],
        dataset_id: Annotated[str, typer.Option("--dataset-id", "-i", help="Run for the dataset with this ID only")] = None,
        no_prompt: Annotated[bool, typer.Option("--no-prompt", "-n", help="Update all affected dataset without prompting the user")] = False,
        dry_run: Annotated[bool, typer.Option("--dry-run", "-d", help="Do not apply changes to Quicksight")] = False,
):
    """
    Update datasets that refer to the source schema to use the target schema
    """

    session = boto3.Session(profile_name=aws_profile)
    client = session.client("quicksight")
    count = 0
    for dataset in _fetch_datasets(client, account_id, dataset_id=dataset_id):
        physical_table_map = dataset.get("PhysicalTableMap", {})
        for physical_table in physical_table_map.values():
            if "RelationalTable" in physical_table:
                table = physical_table["RelationalTable"]
                if table["Schema"] == source_schema:
                    count += 1
                    print(
                        ("DRY RUN: " if dry_run else "")
                        + f"Renaming table {table['Schema']}.{table['Name']} to {target_schema}.{table['Name']} "
                        + f"https://eu-west-2.quicksight.aws.amazon.com/sn/data-sets/{dataset['DataSetId']}"
                    )
                    if dry_run:
                        continue
                    if not no_prompt:
                        input("Press enter to update the dataset on Quicksight")
                    table["Schema"] = target_schema
                    client.update_data_set(
                        AwsAccountId=account_id,
                        **{
                            x: v
                            for x, v in dataset.items()
                            if x
                            not in [
                                "Arn",
                                "CreatedTime",
                                "LastUpdatedTime",
                                "OutputColumns",
                                "ConsumedSpiceCapacityInBytes",
                            ]
                        },
                    )
    print(f"Total: {count}")
