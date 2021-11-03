## Installation

In a virtual environment, clone this repo and install LDB:
```
pip install -e path/to/ldb
```
For help, use:
```
ldb -h
```
or
```
ldb <subcommand> -h
```

## Debugging
To see a stack trace with errors, use the `-v`/`--verbose` option with a command:
```
ldb <subcommand> -v
```

## Tests

You'll need to use DVC to download the test data. It's public so no credentials are needed. You can do this step with a separate virtual environment if you want. While in the base directory of the `ldb` repo, run:
```
pip install '.[test-setup]'
dvc pull
```

Then in your dev environment:
```
pip install '.[test]'
```

To run tests:
```
pytest
```

## Linters

To set up linters:
```
pip install '.[lint]'
```
It's recommend to install the git pre-commit hook:
```
pre-commit install
```

To run linters, type-checkers, formatters, etc. (some will reformat files in place):
```
pre-commit
```
