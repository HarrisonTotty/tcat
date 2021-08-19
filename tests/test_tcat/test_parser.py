'''
Tests transaction parser objects and associated definitions.
'''

import datetime

from tcat import Parser, Transaction, Transactions

from . import CREDIT_CSV_CONTENT, CSV_CONTENT


def test_amount_string_conversions():
    '''
    Tests conversions from dollar amounts to dollar strings and back.
    '''
    assert Parser.amount_from_str('4.55')     == 4.55
    assert Parser.amount_from_str('$1.23')    == 1.23
    assert Parser.amount_from_str('$-99')     == -99.0
    assert Parser.amount_from_str('($67.55)') == -67.55
    assert Parser.amount_to_str(5.89)         == '$5.89'
    assert Parser.amount_to_str(-986.344)     == '-$986.34'

def test_parse_credit_csv_content():
    '''
    Tests the ability of the parser to parse credit CSV content.
    '''
    start = Parser().parse_credit_csv_content(
        card_issuer = 'bank1',
        card_name = 'Super Platinum Card',
        content = CREDIT_CSV_CONTENT,
        start_balance = 0.0
    )
    assert len(start) ==  3
    assert start[0] == Transaction(
        account = 'Super Platinum Card',
        amount  = -2.21,
        balance = -2.21,
        bank    = 'bank1',
        date    = datetime.date(2020, 7, 22),
        desc    = 'PIZZA PLANET 0123456789 2'
    )
    assert start[1] == Transaction(
        account = 'Super Platinum Card',
        amount  = -8.15,
        balance = -10.36,
        bank    = 'bank1',
        date    = datetime.date(2020, 8, 19),
        desc    = 'PIZZA PLANET 0123456789 1'
    )
    assert start[2] == Transaction(
        account = 'Super Platinum Card',
        amount  = 30.00,
        balance = 19.64,
        bank    = 'bank1',
        date    = datetime.date(2021, 2, 3),
        desc    = 'PAYMENT THANK YOU ;;;;;'
    )
    end = Parser().parse_credit_csv_content(
        card_issuer = 'bank1',
        card_name = 'Super Platinum Card',
        content = CREDIT_CSV_CONTENT,
        end_balance = 0.0
    )
    assert len(end) ==  3
    assert end[0] == Transaction(
        account = 'Super Platinum Card',
        amount  = -2.21,
        balance = -21.85,
        bank    = 'bank1',
        date    = datetime.date(2020, 7, 22),
        desc    = 'PIZZA PLANET 0123456789 2'
    )
    assert end[1] == Transaction(
        account = 'Super Platinum Card',
        amount  = -8.15,
        balance = -30.0,
        bank    = 'bank1',
        date    = datetime.date(2020, 8, 19),
        desc    = 'PIZZA PLANET 0123456789 1'
    )
    assert end[2] == Transaction(
        account = 'Super Platinum Card',
        amount  = 30.00,
        balance = 0.0,
        bank    = 'bank1',
        date    = datetime.date(2021, 2, 3),
        desc    = 'PAYMENT THANK YOU ;;;;;'
    )

def test_parse_transaction_csv_content():
    '''
    Tests the ability of the parser to parse transaction CSV content.
    '''
    transactions = Parser().parse_transaction_csv_content(
        account = 'checking',
        bank = 'bank1',
        content = CSV_CONTENT
    )
    assert len(transactions) == 3
    assert transactions[0] == Transaction(
        account = 'checking',
        amount  = -9.47,
        balance = -16.18,
        bank    = 'bank1',
        date    = datetime.date(2020, 3, 19),
        desc    = 'PIZZA PLANET 0123456789 2'
    )
    assert transactions[1] == Transaction(
        account = 'checking',
        amount  = -3.75,
        balance = 67.45,
        bank    = 'bank1',
        date    = datetime.date(2020, 4, 13),
        desc    = 'PIZZA PLANET 0123456789 1'
    )
    assert transactions[2] == Transaction(
        account = 'checking',
        amount  = -64.01,
        balance = 19.18,
        bank    = 'bank1',
        date    = datetime.date(2021, 6, 1),
        desc    = 'SUB SHOP 0123456789 1'
    )
