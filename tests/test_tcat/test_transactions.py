'''
Tests transaction objects.
'''

import datetime

from tcat import Transaction, Transactions

from . import (
    D1,
    D2,
    D3,
    D4,
    T1,
    T2,
    T3,
    T4,
    T
)

def test_transaction_dict_rep():
    '''
    Tests the dictionary representation of transactions.
    '''
    assert T1['account'] == 'checking'
    assert set(T1.keys()) == set([
        'account',
        'amount',
        'balance',
        'bank',
        'date',
        'desc',
        'name',
        'note',
        'tags'
    ])
    assert dict(T2) == {
        'account': 'savings',
        'amount': 4.11,
        'balance': 982.33,
        'bank': 'bank1',
        'date': D2,
        'desc': 'TRANSFER',
        'name': None,
        'note': None,
        'tags': []
    }

def test_transaction_json_conversion():
    '''
    Tests the JSON conversion of a transaction.
    '''
    T1_json = T1.to_json()
    T1_str  = str(T1)
    T1_from_json = Transaction.from_json(T1_json)
    assert T1_json == T1_str
    assert T1_from_json == T1

def test_transaction_lengths():
    '''
    Tests the lengths of transactions.
    '''
    assert len(T1) == 2
    assert len(T2) == 0
    assert len(T3) == 2
    assert len(T4) == 2

def test_transaction_methods():
    '''
    Tests methods defined on transaction objects.
    '''
    assert T1.has_note()
    assert T1.is_categorized()
    assert T1.is_named()
    assert not T2.has_note()
    assert not T2.is_categorized()
    assert not T2.is_named()
    assert T3.has_note()
    assert T3.is_categorized()
    assert T3.is_named()
    assert T4.has_note()
    assert T4.is_categorized()
    assert T4.is_named()

def test_transaction_values():
    '''
    Tests the values of `T1` and `T2`.
    '''
    assert T1.account == 'checking'
    assert T1.amount  == -3.75
    assert T1.balance == 67.45
    assert T1.bank    == 'bank1'
    assert T1.date    == D1
    assert T1.desc    == 'PIZZA PLANET 0123456789 1'
    assert T1.name    == 'Pizza Planet'
    assert T1.note   == 'Got some pizza'
    assert T1.tags    == ['food', 'pizza']
    assert T2.account == 'savings'
    assert T2.amount  == 4.11
    assert T2.balance == 982.33
    assert T2.bank    == 'bank1'
    assert T2.date    == D2
    assert T2.desc    == 'TRANSFER'
    assert T2.tags    == []
    assert T2.name is None
    assert T2.note is None

def test_transactions_collections():
    '''
    Tests the `accounts()`, `banks()`, and `tags()` methods.
    '''
    assert set(T.accounts())        == set(['checking', 'savings'])
    assert set(T.accounts('bank2')) == set(['checking'])
    assert set(T.banks())           == set(['bank1', 'bank2'])
    assert set(T.dates())           == set([D1, D2, D3, D4])
    assert set(T.names())           == set(['Pizza Planet', 'Sub Shop'])
    assert set(T.tags())            == set(['food', 'pizza', 'subs'])
    assert set(T.descs()) == set([
        'PIZZA PLANET 0123456789 1',
        'PIZZA PLANET 0123456789 2',
        'SUB SHOP 0123456789 1',
        'TRANSFER'
    ])

def test_transactions_counts():
    '''
    Tests the `counts()` method.
    '''
    counts = T.counts()
    assert counts['UNKNOWN']      == 1
    assert counts['Pizza Planet'] == 2
    assert counts['Sub Shop']     == 1

def test_transactions_coverage():
    '''
    Tests the `coverage()` and `uncategorized()` methods.
    '''
    assert T.uncategorized() == Transactions([T2])
    assert T.coverage() == 75.0

def test_transactions_filtering():
    '''
    Tests various invocations of the `filter()` method.
    '''
    # bank
    assert set(T.filter(bank='bank1'))                     == set([T1, T2, T4])
    assert set(T.filter(bank='bank1', negate=True))           == set([T3])
    # account
    assert set(T.filter(account='CHECKING'))               == set([T1, T3, T4])
    assert set(T.filter(account='CHECKING', negate=True))     == set([T2])
    # tags
    assert set(T.filter(tags='food'))                      == set([T1, T3, T4])
    assert set(T.filter(tags='food', negate=True))            == set([T2])
    assert set(T.filter(tags=['pizza', 'subs']))           == set([T1, T3, T4])
    assert set(T.filter(tags=['pizza', 'subs'], negate=True)) == set([T2])
    # name
    assert set(T.filter(name='Pizza Planet'))              == set([T1, T3])
    assert set(T.filter(name='Pizza Planet', negate=True))    == set([T2, T4])
    # desc
    assert set(T.filter(desc='PIZZA'))                     == set([T1, T3])
    assert set(T.filter(desc='PIZZA', negate=True))           == set([T2, T4])
    # note
    assert set(T.filter(note='got some'))                  == set([T1, T3, T4])
    assert set(T.filter(note='got some', negate=True))        == set([T2])
    # amount
    assert set(T.filter(amount='+'))                       == set([T2])
    assert set(T.filter(amount='d'))                       == set([T2])
    assert set(T.filter(amount='deposit'))                 == set([T2])
    assert set(T.filter(amount='-'))                       == set([T1, T3, T4])
    assert set(T.filter(amount='w'))                       == set([T1, T3, T4])
    assert set(T.filter(amount='withdrawal'))              == set([T1, T3, T4])
    assert set(T.filter(amount=(-10.0, -1.0)))             == set([T1, T3])
    # date
    assert set(T.filter(date='2020'))                      == set([T1, T2, T3])
    assert set(T.filter(date='2020/04'))                   == set([T1, T2])
    assert set(T.filter(date='2020/04/13'))                == set([T1])
    assert set(T.filter(date=D1))                          == set([T1])
    assert set(T.filter(date=('2020/03', '2020/04')))      == set([T1, T2, T3])
    # combination
    assert set(T.filter(account='checking', date='2020'))  == set([T1, T3])

def test_transactions_grouping():
    '''
    Tests the ability to group transactions.
    '''
    account      = T.group(by='account')
    amount       = T.group(by='amount', drange=50)
    balance      = T.group(by='balance', drange=100)
    bank         = T.group(by='bank')
    bank_account = T.group(by='bank-account')
    date_daily   = T.group(by='date-daily')
    date_weekly  = T.group(by='date-weekly')
    date_monthly = T.group(by='date-monthly')
    date_yearly  = T.group(by='date-yearly')
    descs        = T.group(by='desc')
    names        = T.group(by='name')
    tags         = T.group(by='tags')
    assert account == {
        'checking': Transactions([T3, T1, T4]),
        'savings': Transactions([T2])
    }
    assert amount == {
        (-65.0, -15.0): Transactions([T4]),
        (-15.0, 35.0): Transactions([T3, T1, T2])
    }
    assert balance == {
        (-17.0, 83.0): Transactions([T3, T1, T4]),
        (883.0, 983.0): Transactions([T2])
    }
    assert bank == {
        'bank1': Transactions([T1, T2, T4]),
        'bank2': Transactions([T3])
    }
    assert bank_account == {
        ('bank1', 'checking'): Transactions([T1, T4]),
        ('bank1', 'savings'): Transactions([T2]),
        ('bank2', 'checking'): Transactions([T3])
    }
    assert len(date_daily.keys())   == 4
    assert len(date_weekly.keys())  == 4
    assert len(date_monthly.keys()) == 3
    assert len(date_yearly.keys())  == 2
    assert descs == {
        'PIZZA PLANET 0123456789 1': Transactions([T1]),
        'PIZZA PLANET 0123456789 2': Transactions([T3]),
        'SUB SHOP 0123456789 1': Transactions([T4]),
        'TRANSFER': Transactions([T2])
    }
    assert names == {
        'Pizza Planet': Transactions([T3, T1]),
        'Sub Shop': Transactions([T4])
    }
    assert tags == {
        ('food', 'pizza'): Transactions([T3, T1]), # already sorted.
        ('food', 'subs'): Transactions([T4])
    }

def test_transactions_hovertext():
    '''
    Tests the `hovertext()` method.
    '''
    assert T.hovertext() == 'Pizza Planet (-3.75) | ? (4.11) | Pizza Planet (-9.47) | Sub Shop (-64.01)'
    assert T.hovertext(
        pkey = 'amount',
        skey = 'balance'
    ) == '-3.75 (67.45) | 4.11 (982.33) | -9.47 (-16.18) | -64.01 (19.18)'

def test_transactions_iter():
    '''
    Tests the ability to iterate over transactions.
    '''
    assert len(T) == 4
    assert T[0] == T1
    for i, t in enumerate(T):
        assert t == [T1, T2, T3, T4][i]

def test_transactions_json_conversion():
    '''
    Tests the JSON conversion of a list of transactions.
    '''
    T_json = T.to_json()
    T_from_json = Transactions.from_json(T_json)
    assert T_from_json == T

def test_transactions_merging():
    '''
    Tests the `merge()` method.
    '''
    t1 = Transactions([T1, T2])
    t2 = Transactions([T3, T4])
    t3 = Transactions([T1, T4])
    assert set(Transactions.merge(t1, t2))     == set([T1, T2, T3, T4])
    assert set(Transactions.merge(t1, t2, t3)) == set([T1, T2, T3, T4])
    assert set(Transactions.merge(t1, t3))     == set([T1, T2, T4])

def test_transactions_statistics():
    '''
    Tests the various statistical methods on transactions.
    '''
    assert T.max_amount()     == 4.11
    assert T.max_balance()    == 982.33
    assert T.mean_amount()    == -18.28
    assert T.mean_balance()   == 263.19
    assert T.median_amount()  == -6.61
    assert T.median_balance() == 43.31
    assert T.min_amount()     == -64.01
    assert T.min_balance()    == -16.18
    assert T.stdev_amount()   == 30.99
    assert T.stdev_balance()  == 480.65
    assert T.total_amount()   == -73.12
    assert T.total_balance()  == 1052.78
    assert T.max_amount(absolute_value=True)     == 64.01
    assert T.max_balance(absolute_value=True)    == 982.33
    assert T.mean_amount(absolute_value=True)    == 20.34
    assert T.mean_balance(absolute_value=True)   == 271.29
    assert T.median_amount(absolute_value=True)  == 6.79
    assert T.median_balance(absolute_value=True) == 43.31
    assert T.min_amount(absolute_value=True)     == 3.75
    assert T.min_balance(absolute_value=True)    == 16.18
    assert T.stdev_amount(absolute_value=True)   == 29.23
    assert T.stdev_balance(absolute_value=True)  == 474.61
    assert T.total_amount(absolute_value=True)   == 81.34
    assert T.total_balance(absolute_value=True)  == 1085.14
    assert T.mean_freq(scale='daily')     == 0.0091
    assert T.mean_freq(scale='weekly')    == 0.0635
    assert T.mean_freq(scale='monthly')   == 0.25
    assert T.mean_freq(scale='yearly')    == 2.0
    assert T.median_freq(scale='daily')   == 0.0
    assert T.median_freq(scale='weekly')  == 0.0
    assert T.median_freq(scale='monthly') == 0.0
    assert T.median_freq(scale='yearly')  == 2.0
    assert T.stdev_freq(scale='daily')    == 0.095
    assert T.stdev_freq(scale='weekly')   == 0.2458
    assert T.stdev_freq(scale='monthly')  == 0.5774
    assert T.stdev_freq(scale='yearly')   == 1.4142
    assert T.statistics() == {
        'count': 4,
        'max_abs_amount': 64.01,
        'max_abs_balance': 982.33,
        'max_amount': 4.11,
        'max_balance': 982.33,
        'mean_abs_amount': 20.34,
        'mean_abs_balance': 271.29,
        'mean_amount': -18.28,
        'mean_balance': 263.19,
        'mean_freq_daily': 0.0091,
        'mean_freq_monthly': 0.25,
        'mean_freq_weekly': 0.0635,
        'mean_freq_yearly': 2.0,
        'median_abs_amount': 6.79,
        'median_abs_balance': 43.31,
        'median_amount': -6.61,
        'median_balance': 43.31,
        'median_freq_daily': 0.0,
        'median_freq_monthly': 0.0,
        'median_freq_weekly': 0.0,
        'median_freq_yearly': 2.0,
        'min_abs_amount': 3.75,
        'min_abs_balance': 16.18,
        'min_amount': -64.01,
        'min_balance': -16.18,
        'stdev_abs_amount': 29.23,
        'stdev_abs_balance': 474.61,
        'stdev_amount': 30.99,
        'stdev_balance': 480.65,
        'stdev_freq_daily': 0.095,
        'stdev_freq_monthly': 0.5774,
        'stdev_freq_weekly': 0.2458,
        'stdev_freq_yearly': 1.4142,
        'total_abs_amount': 81.34,
        'total_abs_balance': 1085.14,
        'total_amount': -73.12,
        'total_balance': 1052.78
    }

def test_transactions_sorting():
    '''
    Tests the `sort()` function on a list of transactions.
    '''
    assert T.sort().items              == [T3, T1, T2, T4]
    assert T.sort(reverse=True).items     == [T4, T2, T1, T3]
    assert T.sort(key='amount').items  == [T4, T3, T1, T2]
    assert T.sort(key='balance').items == [T3, T4, T1, T2]
