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
import csv
import datetime
from collections import deque
from contextlib import contextmanager
from typing_extensions import Annotated

import boto3
import pglast
import pglast.stream
import typer
from rich.progress import MofNCompleteColumn, BarColumn, SpinnerColumn, TextColumn, TimeRemainingColumn, Progress
from botocore.exceptions import ClientError

app = typer.Typer()


@app.command()
def rename_schema(
        account_id: Annotated[str, typer.Option("--account-id", "-a", help="The AWS account ID", show_default=False)],
        source_schema: Annotated[str, typer.Option("--source-schema", "-s", help="The schema that will be renamed", show_default=False)],
        target_schema: Annotated[str, typer.Option("--target-schema", "-t", help="The new name of the source schema", show_default=False)],
        aws_profile: Annotated[str, typer.Option("--aws-profile", "-p", help="The profile to connect to AWS", show_default=False)] = None,
        dataset_id: Annotated[str, typer.Option("--dataset-id", "-i", help="Run for the dataset with this ID only")] = None,
        no_prompt: Annotated[bool, typer.Option("--no-prompt", "-n", help="Update all affected dataset without prompting the user")] = False,
        dry_run: Annotated[bool, typer.Option("--dry-run", "-d", help="Do not apply changes to Quicksight")] = False,
):
    """
    Update datasets that refer to the source schema to use the target schema
    """

    def all_dataset_ids(client):
        with Progress(SpinnerColumn(finished_text='[green]✔'), TextColumn("{task.description}")) as progress:
            task = progress.add_task("Finding all datasets...", total=1)

            dataset_ids = tuple(
                dataset_summary['DataSetId']
                for page in client.get_paginator("list_data_sets").paginate(AwsAccountId=account_id)
                for dataset_summary in page.get("DataSetSummaries", [])
            )
            progress.update(task, advance=1, description=f'Finding all datasets... done: [bold]{len(dataset_ids)}')
            return dataset_ids

    def datasets(client, console, dataset_ids):
        for _dataset_id in dataset_ids:
            try:
                response = client.describe_data_set(
                    AwsAccountId=account_id, DataSetId=_dataset_id
                )
            except ClientError as ex:
                # Some datasets cannot be described in the API, e.g. manual uploads
                console.print(f"⚠️  Error fetching detail for dataset {_dataset_id}: {ex.response['Error']['Message']}")
                continue

            yield response["DataSet"]

    @contextmanager
    def csv_output_report():
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"{timestamp}--{account_id}{'--dry-run' if dry_run else ''}.csv"

        with open(filename, 'w', newline='') as f:
            fieldnames = ['dataset_id', 'dataset_link', 'physical_table_id', 'type', 'source', 'target']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            yield writer

    def tables_from_query(query):
        statements = pglast.parse_sql(query)

        if len(statements) == 0:
            return []

        tables = set()

        node_ctenames = deque()
        node_ctenames.append((statements[0](), ()))

        while node_ctenames:
            node, ctenames = node_ctenames.popleft()

            if node.get("withClause", None) is not None:
                if node["withClause"]["recursive"]:
                    ctenames += tuple((cte["ctename"] for cte in node["withClause"]["ctes"]))
                    for cte in node["withClause"]["ctes"]:
                        node_ctenames.append((cte, ctenames))
                else:
                    for cte in node["withClause"]["ctes"]:
                        node_ctenames.append((cte, ctenames))
                        ctenames += (cte["ctename"],)

            if node.get("@", None) == "RangeVar" and (
                    node["schemaname"] is not None or node["relname"] not in ctenames
            ):
                tables.add((node["schemaname"] or "public", node["relname"]))

            for node_type, node_value in node.items():
                if node_type == "withClause":
                    continue
                for nested_node in node_value if isinstance(node_value, tuple) else (node_value,):
                    if isinstance(nested_node, dict):
                        node_ctenames.append((nested_node, ctenames))

        return sorted(list(tables))

    def rename_schema(query, source, target):
        # Strongly based on tables_from_query, but that is based on iterating over the "dict" form
        # of the parsed query. But to re-serialize, we need the object form. Could probably be
        # simplified to only use the object form
        statements = pglast.parse_sql(query)

        if len(statements) > 1:
            raise Exception("Multiple statements are not supported")

        if len(statements) == 0:
            return []

        node_ctenames = deque()
        node_ctenames.append((statements[0], ()))

        while node_ctenames:
            node, ctenames = node_ctenames.popleft()
            node_dict = node()

            if node_dict.get("withClause", None) is not None:
                if node_dict["withClause"]["recursive"]:
                    ctenames += tuple((cte.ctename for cte in node.withClause.ctes))
                    for cte in node.withClause.ctes:
                        node_ctenames.append((cte, ctenames))
                else:
                    for cte in node.withClause.ctes:
                        node_ctenames.append((cte, ctenames))
                        ctenames += (cte.ctename,)

            if node_dict.get("@", None) == "RangeVar" and (
                node_dict["schemaname"] is not None or node_dict["relname"] not in ctenames
            ) and (node.schemaname or "public") == source:
                node.schemaname = target

            for node_type in node:
                node_value = getattr(node, node_type)
                if node_type == "withClause":
                    continue
                for nested_node in node_value if isinstance(node_value, tuple) else (node_value,):
                    if isinstance(nested_node, pglast.ast.Node):
                        node_ctenames.append((nested_node, ctenames))

        return pglast.stream.IndentedStream(
            comments=pglast._extract_comments(query),
            comma_at_eoln=True,
        )(statements[0])

    def modify_dataset_dict_if_needed(console, dataset):
        for physical_table_id, physical_table in dataset.get("PhysicalTableMap", {}).items():
            dataset_link = f"https://eu-west-2.quicksight.aws.amazon.com/sn/data-sets/{dataset['DataSetId']}"
            if "RelationalTable" in physical_table:
                table = physical_table["RelationalTable"]
                if table["Schema"] == source_schema:
                    console.print(
                        f"[green]✔[/green] RelationalTable: {[(table['Schema'], table['Name'])]} ➜ {[(target_schema, table['Name'])]}"
                    )
                    table["Schema"] = target_schema
                    yield {
                        'dataset_id': dataset['DataSetId'],
                        'dataset_link': dataset_link,
                        'physical_table_id': physical_table_id,
                        'type': 'table',
                        'source': source_schema,
                        'target': target_schema,
                    }
            if "CustomSql" in physical_table:
                original_sql = physical_table["CustomSql"]["SqlQuery"]
                try:
                    tables = tables_from_query(physical_table["CustomSql"]["SqlQuery"])
                except:
                    console.print(f"⚠️  Unable to parse query in {dataset['DataSetId']}")
                    console.print(original_sql)
                    continue
                if any(schema == source_schema for schema, table in tables):
                    renamed_sql = rename_schema(original_sql, source_schema, target_schema)
                    new_tables = tables_from_query(renamed_sql)
                    console.print(f"[green]✔[/green] CustomSql: {tables} ➜ {new_tables}")
                    no_original = any(schema == source_schema for schema, table in new_tables) == False
                    any_target = any(schema == target_schema for schema, table in new_tables) == True
                    original_tables_to_be_unchanged = set((schema, table) for schema, table in tables if schema not in (source_schema, target_schema))
                    new_tables_to_be_unchanged = set((schema, table) for schema, table in new_tables if schema not in (source_schema, target_schema))
                    assert no_original
                    assert any_target
                    assert original_tables_to_be_unchanged == new_tables_to_be_unchanged
                    physical_table["CustomSql"]["SqlQuery"] = renamed_sql
                    yield {
                        'dataset_id': dataset['DataSetId'],
                        'dataset_link': dataset_link,
                        'physical_table_id': physical_table_id,
                        'type': 'sql',
                        'source': original_sql,
                        'target': rename_schema(original_sql, source_schema, target_schema),
                    }

    session_opts = {'profile_name': aws_profile} if aws_profile is not None else {}
    session = boto3.Session(**session_opts)
    client = session.client("quicksight")

    dataset_ids = \
        (dataset_id,) if dataset_id is not None else \
        all_dataset_ids(client)

    updated = 0

    with \
            csv_output_report() as writer, \
            Progress(
                SpinnerColumn(finished_text='[green]✔'),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                '[bright_yellow]Updated: {task.fields[updated]}',
                TimeRemainingColumn(),
            ) as progress:

        task = progress.add_task(("[green]\\[DRY RUN][/green] " if dry_run else "") + 'Updating datasets...', total=len(dataset_ids), updated=0)
        
        for dataset in datasets(client, progress.console, dataset_ids):

            dataset_changes = tuple(modify_dataset_dict_if_needed(progress.console, dataset))

            for dataset_change in dataset_changes:
                writer.writerow(dataset_change)

            if dataset_changes and not dry_run:
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

            updated += 1 if dataset_changes else 0
            progress.advance(task)
            progress.update(task, updated=updated)
