'''
Contains the definition of `TransactionBase`.
'''

from __future__ import annotations

import copy
import dataclasses
import datetime
import json

from IPython.display import display, Markdown
from pandas import Series
from typing import Any, Optional, Union

DATE_FIELDS = {
    'date': 'Date'
}

STRING_FIELDS = {
    # field: desc
    'desc': 'Description',
    'id': 'ID',
    'location': 'Location',
    'name': 'Name',
    'notes': 'User Notes'
}

STRING_LIST_FIELDS = {
    # field: (plural desc, singular desc)
    'tags': ('Tags', 'Tag')
}

VALUE_FIELDS = {
    # field: desc
    'amount': 'Transaction Amount'
}

@dataclasses.dataclass
class TransactionBase:
    '''
    Represents the base properties of transactions which are present whether
    concerning "debit" or "credit" transactions.

    This class usually isn't instantiated directly. Instead you'll most likely
    want to work with `DebitTransaction` or `CreditTransaction` objects.

    Attributes:
      amount: The dollar amount associated with the transaction.
      date: The date associated with the transaction (specifically, the report date).
      desc: The raw description string of the transaction.
      id: A unique identifier for the transaction.
      location: The general location associated with the transaction, if applicable.
      name: A human-readable name for the transaction, if categorized.
      notes: An optional string of user notes, in Markdown format.
      tags: A list of strings used to categorize the transaction.
    '''
    amount: float
    date: datetime.date
    desc: str
    id: str
    location: Optional[str]
    name: Optional[str]
    notes: Optional[str]
    tags: list[str]

    def __getitem__(self, key: str) -> Union[list[str], None, str]:
        '''
        Allows one to access fields of a transaction via dictionary syntax.

        Args:
          key: The name of the class attribute to fetch.

        Returns:
          The value associated with the specified field.
        '''
        return self.__dict__[key]

    def __hash__(self) -> int:
        '''
        Computes the hash representation of the transaction.

        Returns:
          The hash representation of the transaction.
        '''
        return hash((self.amount, self.date, self.desc))

    def keys(self) -> list[str]:
        '''
        Returns the dictionary keys associated with this transaction class.

        Returns:
          The `dict` keys as `list[str]`, corresponding to the possible fields of the transaction.
        '''
        return list(self.__dict__.keys())

    def to_base_dict(self) -> dict[str, Any]:
        '''
        Converts this transaction into a raw python dictionary.

        This method is different from `to_dict()` in that it only includes keys
        associated with `TransactionBase` objects.

        Returns:
          A copy of the `dict` representation of the transaction.
        '''
        res = {}
        for k in (list(DATE_FIELDS.keys()) + list(STRING_FIELDS.keys()) + list(STRING_LIST_FIELDS.keys()) + list(VALUE_FIELDS.keys())):
            res[k] = self[k]
        return copy.deepcopy(res)

    def to_dict(self) -> dict[str, Any]:
        '''
        Converts this transaction into a raw python dictionary.

        Returns:
          A copy of the raw `dict` representation of the transaction.
        '''
        return copy.deepcopy(self.__dict__)

    def to_json(self) -> str:
        '''
        Computes the JSON string representation of the transaction.

        Returns:
          The JSON string representation of the transaction.
        '''
        return json.dumps(self.to_dict())

    def to_series(self) -> Series:
        '''
        Converts the transaction into a [pandas Series
        object](https://pandas.pydata.org/docs/reference/series.html)

        Returns:
          A pandas `Series` object associated with the transaction.
        '''
        return Series(self.to_dict())
