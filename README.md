# Labrea

![](https://img.shields.io/badge/version-1.4.0-blue.svg)
[![lifecycle](https://img.shields.io/badge/lifecycle-stable-green.svg)](https://www.tidyverse.org/lifecycle/#stable)
[![PyPI Downloads](https://img.shields.io/pypi/dm/labrea.svg?label=PyPI%20downloads)](https://pypi.org/project/labrea/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Coverage](https://raw.githubusercontent.com/8451/labrea/meta/coverage/coverage.svg)](https://github.com/8451/labrea/tree/meta/coverage)
[![docs](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat)](https://8451.github.io/labrea)

A framework for declarative, functional dataset definitions.

## Installation
Labrea is available for install via pip.

```bash
pip install labrea
````

Alternatively, you can install the latest development version from GitHub.

```bash
pip install git+https://github.com/8451/labrea@develop
```

## Usage
See our usage guide [here](docs/source/usage.md).

Labrea exposes a `dataset` decorator that allows you to define datasets and their dependencies in a declarative manner. 
Dependencies can either be other datasets or `Option`s, which are values that can be passed in at runtime via a 
dictionary.

```python
from labrea import dataset, Option
import pandas as pd


@dataset
def stores(path: Option('PATHS.STORES')) -> pd.DataFrame:
    return pd.read_csv(path)


@dataset
def transactions(path: Option('PATHS.SALES')) -> pd.DataFrame:
    return pd.read_csv(path)


@dataset
def sales_by_region(
        stores_: pd.DataFrame = stores, 
        transactions_: pd.DataFrame = transactions
) -> pd.DataFrame:
    """Merge stores to transactions, sum sales by region"""
    return pd.merge(transactions_, stores_, on='store_id').groupby('region')['sales'].sum().reset_index()


options = {
    'PATHS': {
        'STORES': 'path/to/stores.csv',
        'SALES': 'path/to/sales.csv'
    }
}


stores(options)
## +-----------------+-----------+
## | store_id        | region    |
## |-----------------+-----------|
## | 1               | North     |
## | 2               | South     |
## | 3               | East      |
## +-----------------+-----------+

transactions(options)
## +-----------------+-----------------+-----------------+
## | store_id        | sales           | transaction_id  |
## |-----------------+-----------------+-----------------|
## | 1               | 100             | 1               |
## | 2               | 200             | 2               |
## | 3               | 300             | 3               |
## +-----------------+-----------------+-----------------+

sales_by_region(options)
## +-----------------+-----------------+
## | region          | sales           |
## |-----------------+-----------------|
## | North           | 100             |
## | South           | 200             |
## | East            | 300             |
## +-----------------+-----------------+
```

## Contributing
If you would like to contribute to **labrea**, please read the
[Contributing Guide](docs/source/contributing.md).

## Changelog
A summary of recent updates to **labrea** can be found in the
[Changelog](docs/source/changelog.md).

## Maintainers

| Maintainer                                                | Email                    |
|-----------------------------------------------------------|--------------------------|
| [Austin Warner](https://github.com/austinwarner-8451)     | austin.warner@8451.com   |
| [Michael Stoepel](https://github.com/michaelstoepel-8451) | michael.stoepel@8451.com |

## Links
- Report a bug or request a feature: https://github.com/8451/labrea/issues/new/choose
- Documentation: https://8451.github.io/labrea
