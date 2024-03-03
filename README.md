# quicksight-bulk-update-datasets

Makes bulk updates to Quicksight datasets.

![Screencast of quicksight-bulk-update-datasets](https://raw.githubusercontent.com/uktrade/quicksight-bulk-update-datasets/main/screencast.svg)


## Features

> [!NOTE]
> The only bulk update currently supported is a rename of table schema for PostgreSQL-based datasources

- Renames the schema in RelationalTable and CustomSQL tables in Amazon Quicksight datasets
- CustomSQL is parsed with [pglast](https://github.com/lelit/pglast) to robustly change the schema
- Outputs a CSV report of the changes made
- Has a dry-run mode


## Installation

```bash
pip install quicksight-bulk-update-datasets
```


## Usage

```shell
quicksight-bulk-update-datasets [OPTIONS] ACCOUNT_ID SOURCE_SCHEMA TARGET_SCHEMA
```

**Arguments**:

* `ACCOUNT_ID`: [required]
* `SOURCE_SCHEMA`: [required]
* `TARGET_SCHEMA`: [required]

**Options**:

* `--aws-profile TEXT`
* `--dataset-id TEXT`
* `--no-prompt / --no-no-prompt`: [default: no-no-prompt]
* `--dry-run / --no-dry-run`: [default: no-dry-run]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show help and exit.


## Contributing

### Prerequisites

To contribute you'll need:

- Familiarity with the command line, for example by taking a [course on Bash and Z Shell](https://www.pluralsight.com/courses/bash-zshell-getting-started)
- A [GitHub account](https://github.com/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- [Python](https://www.python.org/downloads/) installed
- A text editor or integrated development environment (IDE), for example [VS Code](https://code.visualstudio.com/)

You may also need to refer to the following as you're making changes:

- [Typer docs](https://typer.tiangolo.com/)
- [Typer cheatsheet](https://gist.github.com/harkabeeparolus/a6e18b1f4f4f938f450090c5e7523f68)
- [Boto3 Quicksight](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/quicksight.html)


### Get the code

If you're not a member of the uktrade GitHub organisation, you should:

1. Fork this repo at https://github.com/uktrade/quicksight-bulk-update-datasets/fork

2. Clone the fork by running the following, replacing `my-username-or-org` with the username or organisation name you forked to:

   ```bash
   git clone git@github.com:my-username-or-org/quicksight-bulk-update-datasets.git
   cd quicksight-bulk-update-datasets.
   ```

If you are a member the uktrade GitHub organisation, you should:

1. Clone this repo directly:

   ```bash
   git clone git@github.com:uktrade/quicksight-bulk-update-datasets.git
   cd quicksight-bulk-update-datasets
   ```

### Install in editable mode

```bash
pip install -e .
```

### Generating docs

```bash
pip install typer-cli
typer quicksight_bulk_update_datasets.py utils docs --name quicksight-bulk-update-datasets --output docs.md
```

Then manually copy and tweaking the docs from docs.md to the Usage section in README.md.

---

## Releasing

After merging to the main branch, create a release from the [Releases page](https://github.com/uktrade/quicksight-bulk-update-datasets/releases).

- The tag _must_ be the form "vX.Y.Z" where X.Y.Z is the new [SemVer 2.0 version](https://semver.org/).
- You should press "Generate release notes" to automatically bring in titles of PRs since the previous release.
- If there are many PRs, you should include an introductory paragraph highlighting the main changes.

Creating a GitHub release will automatically run the [GitHub Actions workflow that releases to PyPI](./.github/workflows/deploy-package-to-pypi.yml).

Only members of the uktrade GitHub organisation may create releases.
