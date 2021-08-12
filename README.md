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

