In a virtual environment, clone this repo and install ldb:
```
pip install -e path/to/ldb
```

To run tests you'll need to use dvc to download the test data. It's public so no credentials are needed. You can do this with a separate virtual environment if you want. While in the base directory of the ldb repo, run:
```
pip install '.[test-setup]'
dvc pull
```

To see a stack trace with errors, use the `-v`/`--verbose` option with a command:
```
ldb stage -v
```
