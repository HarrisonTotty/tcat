'''
Module Unit Tests

For the most part this file just contains common resources leveraged by other
test files.
'''

import datetime
import pytest

import tcat


# ----- Pre-Read CSV Content -----

CREDIT_CSV_CONTENT = '''
Date,Transaction,Name,Memo,Amount
07/22/2020,"DEBIT","PIZZA PLANET","0123456789 2",-$2.21
8/19/2020,"DEBIT","PIZZA PLANET","0123456789 1",($8.15)
2021/02/03,"CREDIT","PAYMENT THANK YOU",";;;;;",$30.00
'''.strip()

CSV_CONTENT = '''
Date,Description,Amount,Balance
03/19/2020,"PIZZA PLANET 0123456789 2",-$9.47,-$16.18
4/13/2020,"PIZZA PLANET 0123456789 1",($3.75),$67.45
2021/06/01,"SUB SHOP 0123456789 1",-64.01,19.18
'''.strip()


# ----- Used Dates -----

D1 = datetime.date(2020, 4, 13)
D2 = datetime.date(2020, 4, 19)
D3 = datetime.date(2020, 3, 19)
D4 = datetime.date(2021, 6, 1)


# ----- Pre-Parsed Data YAML Content -----

DATA_CONTENT = [
    {
        'tags': ['food'],
        'data': [
            {'name': 'Pizza Planet', 'match': r'pizza\s*planet', 'tags': ['pizza']},
            {'name': 'Sub Shop', 'match': r'sub\s*shop', 'tags': ['subs']}
        ]
    },
    {
        'tags': ['misc'],
        'data': [
            {'name': 'Gas Pro', 'match': r'gas\s*pro', 'tags': ['gas']}
        ]
    }
]


# ----- Pre-Categorized Transactions -----

T1 = tcat.Transaction(
    account='checking',
    amount=-3.75,
    balance=67.45,
    bank='bank1',
    date=D1,
    desc='PIZZA PLANET 0123456789 1',
    name='Pizza Planet',
    note='Got some pizza',
    tags=['food', 'pizza']
)
T2 = tcat.Transaction(
    account='savings',
    amount=4.11,
    balance=982.33,
    bank='bank1',
    date=D2,
    desc='TRANSFER'
)
T3 = tcat.Transaction(
    account='checking',
    amount=-9.47,
    balance=-16.18,
    bank='bank2',
    date=D3,
    desc='PIZZA PLANET 0123456789 2',
    name='Pizza Planet',
    note='Got some more pizza',
    tags=['food', 'pizza']
)
T4 = tcat.Transaction(
    account='checking',
    amount=-64.01,
    balance=19.18,
    bank='bank1',
    date=D4,
    desc='SUB SHOP 0123456789 1',
    name='Sub Shop',
    note='Got some subs',
    tags=['food', 'subs']
)
T = tcat.Transactions([T1, T2, T3, T4])


# ----- Uncategorized Transactions -----

T1U = tcat.Transaction(
    account='checking',
    amount=-3.75,
    balance=67.45,
    bank='bank1',
    date=D1,
    desc='PIZZA PLANET 0123456789 1',
    note='Got some pizza'
)
T2U = tcat.Transaction(
    account='savings',
    amount=4.11,
    balance=982.33,
    bank='bank1',
    date=D2,
    desc='TRANSFER'
)
T3U = tcat.Transaction(
    account='checking',
    amount=-9.47,
    balance=-16.18,
    bank='bank2',
    date=D3,
    desc='PIZZA PLANET 0123456789 2',
    note='Got some more pizza'
)
T4U = tcat.Transaction(
    account='checking',
    amount=-64.01,
    balance=19.18,
    bank='bank1',
    date=D4,
    desc='SUB SHOP 0123456789 1',
    note='Got some subs'
)
TU = tcat.Transactions([T1U, T2U, T3U, T4U])


# ----- Module-Wide Tests -----

def test_module_name():
    '''
    Tests the name of the module.
    '''
    assert tcat.__name__ == 'tcat'
