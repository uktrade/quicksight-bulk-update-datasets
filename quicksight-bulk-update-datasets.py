#
# Update any Quicksight datasets with relational tables in the source schema to use the target schema.
#
# Run in dry run mode (Do this to test it)
# python3 quicksight-bulk-update-datasets.py --account-id=<aws account id> --aws-profile=<aws profile name> --source-schema=<schema name> --target-schema=<schema name> --dry-run
#
# To run for real remove the "--dry-run" argument from the above command
#
# You will be prompted before each dataset is actually updated on Quicksight. To run it for all
# datasets without the prompt add the "--no-prompt" arg to the command
#
from argparse import ArgumentParser

import boto3
from botocore.exceptions import ClientError


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


def main():
    parser = ArgumentParser(
        description="Migrate data sources using tables in the source schema to use the target schema",
    )
    parser.add_argument("-a", "--account-id", required=True, help="The AWS account ID")
    parser.add_argument("-p", "--aws-profile", required=True, help="The profile to connect to AWS")
    parser.add_argument("-s", "--source-schema", required=True, help="The schema that will be renamed")
    parser.add_argument("-t", "--target-schema", required=True, help="The new name of the source schema")
    parser.add_argument("-i", "--dataset-id", required=False, default=None, help="Run for the dataset with this ID only")
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Do not apply changes to Quicksight",
    )
    parser.add_argument(
        "-n",
        "--no-prompt",
        action="store_true",
        help="Update all affected dataset without prompting the user",
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.aws_profile)
    client = session.client("quicksight")
    count = 0
    for dataset in _fetch_datasets(client, args.account_id, dataset_id=args.dataset_id):
        physical_table_map = dataset.get("PhysicalTableMap", {})
        for physical_table in physical_table_map.values():
            if "RelationalTable" in physical_table:
                table = physical_table["RelationalTable"]
                if table["Schema"] == args.source_schema:
                    count += 1
                    print(
                        ("DRY RUN: " if args.dry_run else "")
                        + f"Renaming table {table['Schema']}.{table['Name']} to {args.target_schema}.{table['Name']} "
                        + f"https://eu-west-2.quicksight.aws.amazon.com/sn/data-sets/{dataset['DataSetId']}"
                    )
                    if args.dry_run:
                        continue
                    if not args.no_prompt:
                        input("Press enter to update the dataset on Quicksight")
                    table["Schema"] = args.target_schema
                    client.update_data_set(
                        AwsAccountId=args.account_id,
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

if __name__ == "__main__":
    main()
