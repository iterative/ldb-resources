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

## Type checking

Type checking is done in the `mypy` pre-commit hook. To run just this hook on the entire repo, use:
```
pre-commit run -a mypy
```

To aid with adding type annotations if you start adding code without them, you can use [pyannotate](https://github.com/dropbox/pyannotate). To collect annotations from calls made inside tests run:
```
pytest --pyannotate
```
This will store collected type information in `type_info.json`. You'll notice that tests will run a bit slower with this flag.

Then to apply the collected annotations to functions that don't yet have annotations, you can run:
```
pyannotate --py3 -w filename.py
```
or
```
pyannotate --py3 -w directory/
```

This will edit the given files in-place, so it may be a good idea to stage changes before running this, so you can have a clear diff on the changes applied.

These should be considered drafts and will likely need to be fixed manually. For example, `PosixPath` or `WindowsPath` should generally be changed to `Path`, and `Any` should be changed to something more specific in most cases.

Functions without type information or with missing type information after using `pyannotate` may be an indication that the code could use more tests to cover the missing cases.
