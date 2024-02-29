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


@app.command()
def rename_schema(
        account_id: Annotated[str, typer.Option("--account-id", "-a", help="The AWS account ID", show_default=False)],
        aws_profile: Annotated[str, typer.Option("--aws-profile", "-p", help="The profile to connect to AWS", show_default=False)],
        source_schema: Annotated[str, typer.Option("--source-schema", "-s", help="The schema that will be renamed", show_default=False)],
        target_schema: Annotated[str, typer.Option("--target-schema", "-t", help="The new name of the source schema", show_default=False)],
        dataset_id: Annotated[str, typer.Option("--dataset-id", "-i", help="Run for the dataset with this ID only")] = None,
        no_prompt: Annotated[bool, typer.Option("--no-prompt", "-n", help="Update all affected dataset without prompting the user")] = False,
        dry_run: Annotated[bool, typer.Option("--dry-run", "-d", help="Do not apply changes to Quicksight")] = False,
):
    """
    Update datasets that refer to the source schema to use the target schema
    """

    def datasets():
        dataset_ids = (
            dataset_summary['DataSetId']
            for page in client.get_paginator("list_data_sets").paginate(AwsAccountId=account_id)
            for dataset_summary in page.get("DataSetSummaries", [])
        ) if dataset_id is None else (dataset_id,)

        for _dataset_id in dataset_ids:
            try:
                response = client.describe_data_set(
                    AwsAccountId=account_id, DataSetId=_dataset_id
                )
            except ClientError as ex:
                # Some datasets cannot be described in the API, e.g. manual uploads
                print(f"Error fetching detail for dataset {_dataset_id}: {ex.response['Error']['Message']}")
                continue

            yield response["DataSet"]

    session = boto3.Session(profile_name=aws_profile)
    client = session.client("quicksight")

    count = 0
    for dataset in datasets():
        dataset_changed = False

        for physical_table in dataset.get("PhysicalTableMap", {}).values():
            try:
                table = physical_table["RelationalTable"]
            except KeyError:
                continue
            if table["Schema"] != source_schema:
                continue
            dataset_changed = True
            print(
                ("DRY RUN: " if dry_run else "")
                + f"Renaming table {table['Schema']}.{table['Name']} to {target_schema}.{table['Name']} "
                + f"https://eu-west-2.quicksight.aws.amazon.com/sn/data-sets/{dataset['DataSetId']}"
            )
            table["Schema"] = target_schema

        if not dataset_changed:
            continue
        count += 1
        if dry_run:
            continue
        if not no_prompt:
            input("Press enter to update the dataset on Quicksight")
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
