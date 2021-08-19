'''
Contains definitions pertaining to credit card transactions.
'''

import dataclasses
import datetime
from typing import Any, Optional

from .transaction import Transaction, Transactions

@dataclasses.dataclass
class CreditTransaction(Transaction):
    '''
    Represents a credit card transaction. Credit card transactions have the
    following fields:
      * amount
        The dollar amount associated with the transaction.
      * card_issuer
        The name of the credit card company associated with the card.
      * card_name
        The name of the credit card associated with the transaction.
      * date
        The post date of the transaction.
      * desc
        The raw string description associated with the transaction.
      * name
        A human-readable name associated with the transaction, if categorized.
      * note
        An arbitrary string for storing notes about the transaction.
      * tags
        A list if strings used to broadly categorize the transaction.
    '''

    amount: float
    card_issuer: str
    card_name: str
    date: datetime.date
    desc: str
    name: Optional[str] = dataclasses.field(compare=False, default=None)
    note: Optional[str] = dataclasses.field(compare=False, default=None)
    tags: list[str] = dataclasses.field(compare=False, default_factory=list)
