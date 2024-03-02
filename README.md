# quicksight-bulk-update-datasets

Makes bulk updates to Quicksight datasets.

> [!NOTE]
> The only bulk update currently supported is a rename of table schema


## Installation

```shell
pip install quicksight-bulk-update-datasets
```


## Usage

See the source in [quicksight_bulk_update_datasets.py](https://github.com/uktrade/quicksight-bulk-update-datasets/blob/main/quicksight_bulk_update_datasets.py), or after installation run

```shell
quicksight-bulk-update-datasets --help
```

to see some brief guidance.


## Contributing

### Prerequisites

To contribute you'll need:

- Familiarity with the command line, for example by taking a [course on Bash and Z Shell](https://www.pluralsight.com/courses/bash-zshell-getting-started)
- A [GitHub account](https://github.com/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- [Python](https://www.python.org/downloads/) installed
- A text editor or integrated development environment (IDE), for example [VS Code](https://code.visualstudio.com/)

### Get the code

If you're not a member of the uktrade GitHub organisation, you should:

1. Fork this repo at https://github.com/uktrade/quicksight-bulk-update-datasets/fork

2. Clone the fork by running the following, replacing `my-username-or-org` with the username or organisation name you forked to:

   ```shell
   git clone git@github.com:my-username-or-org/quicksight-bulk-update-datasets.git
   cd quicksight-bulk-update-datasets.
   ```

If you are a member the uktrade GitHub organisation, you should:

1. Clone this repo directly:

   ```shell
   git clone git@github.com:uktrade/quicksight-bulk-update-datasets.git
   cd quicksight-bulk-update-datasets
   ```


### Install in editable mode

```shell
pip install -e .
```


### Become familiar with relevant API docs

- [Typer docs](https://typer.tiangolo.com/)
- [Typer cheatsheet](https://gist.github.com/harkabeeparolus/a6e18b1f4f4f938f450090c5e7523f68)
- [Boto3 Quicksight](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/quicksight.html)


---

## Releasing

After merging to the main branch, create a release from the [Releases page](https://github.com/uktrade/quicksight-bulk-update-datasets/releases).

- The tag _must_ be the form "vX.Y.Z" where X.Y.Z is the new [SemVer 2.0 version](https://semver.org/).
- You should press "Generate release notes" to automatically bring in titles of PRs since the previous release.
- If there are many PRs, you should include an introductory paragraph highlighting the main changes.

Creating a GitHub release will automatically run the [GitHub Actions workflow that releases to PyPI](./.github/workflows/deploy-package-to-pypi.yml).

Only members of the uktrade GitHub organisation may create releases.
