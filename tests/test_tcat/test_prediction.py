'''
Tests constructs defined within "prediction.py".
'''
import datetime
import pytest

from tcat import Simulator, Transaction, Transactions

from . import (
    T1,
    T2,
    T3,
    T4
)

D5 = datetime.date(2020, 1, 12)
D6 = datetime.date(2020, 2, 18)
D7 = datetime.date(2020, 3, 19)
D8 = datetime.date(2021, 4, 1)
T5 = Transaction(
    account='checking',
    amount=-9.75,
    balance=67.45,
    bank='bank1',
    date=D5,
    desc='PIZZA PLANET 0123456789 3',
    name='Pizza Planet',
    note='Got some pizza',
    tags=['food', 'pizza']
)
T6 = Transaction(
    account='checking',
    amount=-9.33,
    balance=19.18,
    bank='bank1',
    date=D6,
    desc='SUB SHOP 0123456789 3',
    name='Sub Shop',
    note='Got some subs',
    tags=['food', 'subs']
)
T7 = Transaction(
    account='checking',
    amount=-2.47,
    balance=-16.18,
    bank='bank1',
    date=D7,
    desc='PIZZA PLANET 0123456789 4',
    name='Pizza Planet',
    note='Got some more pizza',
    tags=['food', 'pizza']
)
T8 = Transaction(
    account='checking',
    amount=-64.01,
    balance=19.18,
    bank='bank1',
    date=D8,
    desc='SUB SHOP 0123456789 2',
    name='Sub Shop',
    note='Got some subs',
    tags=['food', 'subs']
)
T = Transactions([T1, T2, T3, T4, T5, T6, T7, T8])

def test_simulator():
    '''
    Tests the basic creation and execution of `Simulator` objects.
    '''
    sim = Simulator(T.filter(bank='bank1', account='checking'))
    res = sim.run(30)
