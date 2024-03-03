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

### Recording a new screencast

There is usually a fair bit of trial and error involved in recording a new screencast. The existing screencast was recorded using [iTerm2](https://iterm2.com/) so you probably should do the same to avoid extra issues and for the following instructions to be as applicable as possible.

- Install [asciinema](https://asciinema.org/) and [svg-term-cli](https://github.com/marionebl/svg-term-cli), and download [iTerm2 Dark Background.itermcolors](https://github.com/mbadolato/iTerm2-Color-Schemes/tree/master/schemes) to the current directory.

- Temporarily modify the code to fetch fewer datasets and to rename any tables using (for example) [Docker's random name generator](https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go), and hard code the real account ID and profile name.

- Construct and test a command line with a fake account ID and profile in a text editor ready to paste at the start of a recording. If going over multiple lines, output is usually better if it's pre-split with the `\` continuation operator.

   ```bash
   quicksight-bulk-update-datasets --account-id=123456789012 --aws-profile=my-profile \
       --source-schema dit --target-schema dbt --no-prompt --dry-run
   ```

  When testing set your terminal width to be as thin as possible where the output still looks good, e.g. without extra wrapping.

- Edit your `~/.zshrc` file (or corresponding file for your shell) to make a simple prompt, and unset highlighting after prompting if necessary.

   ```bash
   PROMPT='$ '
   unset zle_bracketed_paste
   ```

- Start recording.

  ```bash
  asciinema rec screencast.cast
  ```

- Paste in your pre-prepared command, wait a second or so, and hit enter to run it.

- When it's done, wait a few seconds and press CTRL+D. The few seconds is so at the end of the screencast the final output remains on screen for a few seconds, before it auto replays from the beginning.

- Convert to SVG.

   ```bash
   svg-term --in screencast.cast --out screencast.svg --window --term iterm2 \
       --profile "./iTerm2 Dark Background.itermcolors" --height 17 --width 92
   ```

   The height and width should be set as small as possible, but not so small it results strange effects at the edges, such as truncated characters or bleed through from one side of the image to the other.

---

## Releasing

After merging to the main branch, create a release from the [Releases page](https://github.com/uktrade/quicksight-bulk-update-datasets/releases).

- The tag _must_ be the form "vX.Y.Z" where X.Y.Z is the new [SemVer 2.0 version](https://semver.org/).
- You should press "Generate release notes" to automatically bring in titles of PRs since the previous release.
- If there are many PRs, you should include an introductory paragraph highlighting the main changes.

Creating a GitHub release will automatically run the [GitHub Actions workflow that releases to PyPI](./.github/workflows/deploy-package-to-pypi.yml).

Only members of the uktrade GitHub organisation may create releases.
