# Sat4Ec

`sat4ec` is a Python package to monitor occupancy rates of automotive producing facilities by exploiting Sentinel-1 IW GRD data.

## Installation

This project uses a `conda` environment. For installing dependencies use:

```bash
conda env create
```

## Dependencies
For the latest list of dependencies check the [`environment.yml`](environment.yml).

# Development

## `pre-commit`

Some development guardrails are enforced via [`pre-commit`](https://pre-commit.com/). This is to
ensure we follow similar code styles or it automatically cleans up jupyter notebooks.

To install `pre-commit` (not necessary if you [installed the conda
environment](#install-conda-evnironment)):

```shell
conda/pip install pre-commit
```

To initialize all pre-commit hooks, run:

```shell
pre-commit install
```

To test whether `pre-commit` works:

```shell
pre-commit run --all-files
```

It will check all files tracked by git and apply the triggers set up in
[`.pre-commit-config.yaml`](.pre-commit-config.yaml). That is, it will run triggers, possibly
changing the contents of the file (e.g. `black` formatting). Once set up, `pre-commit` will run, as
the name implies, prior to each `git commit`. In its current config, it will format code with
`black` and `isort`, clean up `jupyter notebook` output cells, remove trailing whitespaces and will
block large files to be committed. If it fails, one has to re-stage the affected files (`git add` or
`git stage`), and re-commit.

## Contributors
The DLR-DFD team creates and adapts libraries which simplify the usage of satellite data. Our team
includes (in alphabetical order):
* Krullikowski, Christian

German Aerospace Center (DLR)

## Licenses
This software is licensed under the [Apache 2.0 License](LICENSE.txt).

Copyright (c) 2023 German Aerospace Center (DLR) * German Remote Sensing Data Center * Department:
Geo-Risks and Civil Security