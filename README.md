![Python Version](https://img.shields.io/badge/Python-3.9-blue?style=flat-square) ![GitHub last commit](https://img.shields.io/github/last-commit/HarrisonTotty/tcat?style=flat-square)

# Financial Analytics Platform

A python library for analyzing personal financial data.


## Building

`tcat` provides two building pathways: a dedicated `Docker` image containing a
Jupyter Lab environment, and a `.whl` package to be installed with via `pip`.

To build and install the `.whl` package, ensure that you have python 3.9 and
[poetry](https://python-poetry.org/) installed on your machine. Then run the
following commands:

```bash
poetry install && poetry build -f wheel && pip install dist/*.whl
```

To build and run the Jupyter Lab environment, a `run.sh` script is provided,
otherwise just run:

```bash
docker build -t tcatenv:latest .
```


## Transaction Objects

The core unit of `tcat` is the `Transaction` object. A `Transaction` represents
the data one might find contained in a single line of a transaction CSV file
downloaded from their bank. Each transaction object is a
[dataclass](https://docs.python.org/3/library/dataclasses.html) containing the
following bits of information:

| Field Name | Data Type       | Description                                                                                                 |
|------------|-----------------|-------------------------------------------------------------------------------------------------------------|
| `account`  | `str`           | The account associated with the transaction, such as "checking" or "savings".                               |
| `amount`   | `float`         | The dollar amount of the transaction.                                                                       |
| `balance`  | `float`         | The dollar amount corresponding to the balance of the associated account after registering the transaction. |
| `bank`     | `str`           | The name of the financial institution associated with the account.                                          |
| `date`     | `datetime.date` | The _post_ date associated with the transaction.                                                            |
| `desc`     | `str`           | The description of the transaction, as raw text pulled from the source CSV file.                            |
| `name`     | `Optional[str]` | A more human-friendly version of `desc`, such as "Money Transfer" or "Pizza Planet".                        |
| `note`     | `Optional[str]` | A convenient field to add any additional arbitrary notes about the transaction.                             |
| `tags`     | `list[str]`     | A list of _tag strings_ used to categorize the transaction (see below for more information).                |

Note that the `name`, `note`, and `tags` fields may be "empty" (either `None` or
`[]`), in which case the transaction contains the same data as would be parsed
from a transaction CSV file. Such a transaction is considered _uncategorized_,
and is ultimately not very useful apart noting the change in balance over time.
`tcat` provides tools for automatically categorizing transactions, but more on
that later. A properly categorized transaction might look like the following:

```python
from tcat import Transaction

t = Transaction(
  account = 'checking',
  amount  = -3.87,
  balance = 456.78,
  bank    = 'bank1',
  date    = datetime.date(2021, 8, 12),
  desc    = 'PIZZA PLANET 0123456789 1 20210812 XXYYZZ',
  name    = 'Pizza Planet',
  tags    = ['food', 'fast-food', 'pizza']
)
```

While the `Transaction` object might be considered the "core" unit of `tcat`,
most interaction with the library will be done with `Transactions` objects (note
the `s`!). `Transactions` objects provide a convenient wrapper over a list of
transactions, and are bundled with a ton of useful methods for sorting,
filtering, importing/exporting, etc. The following provides a brief overview of
some of the things you can do:

```python
from tcat import Transactions

# Lets pretend this is a large collection of bank transactions.
transactions = Transactions()

# Transactions objects can be iterated over.
for t in transactions:
  print(str(t))
  
# What banks/accounts are associated with this collection?
accounts = transactions.accounts()
banks = transactions.banks()

# Grab all food-related transactions within the last 90 days from all checking
# accounts.
food = transactions.filter(account='checking', date=90, tags='food')

# What was the most I spent on groceries in the last 30 days?
ans1 = transactions.filter(account='checking', date=30, tags='groceries').max_amount(absolute_value=True)

# What was the average transaction amount each week for the last 90 days?
ans2 = [w.mean_amount() for w in transactions.filter(date=90).group(by='date-weekly').values()]
```


## Parsing Transaction CSV Files

Before categorizing transaction objects, one typically parses them from
transaction CSV files. Such a file might look something like the following:

```
Date,Description,Amount,Balance
03/19/2020,"PIZZA PLANET 0123456789 2",-$9.47,$67.45
03/20/2020,"SUB SHOP 0123456789 1",-$3.75,$63.70
...
```

`tcat` provides the `Parser` class for handling the translation between the
string content above and a resulting `Transactions` object:

```python
from tcat import Parser

# Parse a collection of transactions from "example.csv", indicating the bank/account they belong to.
transactions = Parser().parse_transaction_csv(path='example.csv', bank='bank1', account='checking')
```

Note that for convenience sake, the above function may imply the bank and/or
account associated with the list of transactions depending on whether the `bank`
or `account` parameters are set to `None` (their defaults).

* If neither `bank` nor `account` are defined, the parser assumes the name of
  the input CSV file is of the form `{bank}-{account}.csv`.
* If `bank` is defined but not `account`, the parser will set the account to
  the name of the input file.
* If `account` is defined but not `bank`, the parser will set the bank to the
  name of the input file.
  
A few additional notes about how the parser works:

* Amounts or balances within parentheses are considered negative. For example,
  `($3.87)` would be parsed to `-3.87`.
* The CSV file must have a header line, although field matching is
  case-insensitive and pretty flexible (either `description`, or `desc` is
  allowed, for example).
* Dates may be of the form `YYYY/MM/DD` or `MM/DD/YYYY`, and may be mixed within
  the same file.
  

## Categorizing Transactions

To categorize a collection of transactions, `tcat` leverages a database of
regular expressions defined in YAML documents. Typically `tcat` is pointed to a
directory containing many YAML files loosely grouped by some higher-level
category (`food.yaml`, `bills.yaml`, etc.), where each file looks something like
the following:

 ```yaml
# food.yaml

# A collection of tags inherited by anything that matches within this file.
tags:
  - 'expense'
  - 'food'

# Defines a list of match objects to which an uncategorized transaction's `desc`
# field will be tested.
data:
  - name: 'Pizza Planet'
    match: >-
      ^pizza\s*planet
    tags:
      - 'fast-food'
      - 'pizza'
  - name: 'Sub Shop'
    match: >-
      sub\s*shop
    tags:
      - 'fast-food'
      - 'subs'
 ```

Note that matching is done against the _lowercase_ form of the `desc` field.

To ingest these files, one instantiates a `Categorizer` object pointing at the
directory containing them, combined with the `Parser` object explained above,
one might write the following:

```python
from tcat import Categorizer, Parser

uncategorized = Parser().parse_transaction_csv('~/example/csv')

categorized = Categorizer(data_path='~/example/data').cat(uncategorized)
```
