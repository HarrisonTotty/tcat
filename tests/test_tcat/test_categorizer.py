'''
Tests categorizer objects and associated definitions.
'''

from tcat import Categorizer, Transaction, Transactions

from . import (
    DATA_CONTENT,
    T1U,
    T2U,
    T3U,
    T4U,
    TU
)


def test_categorizer_data():
    '''
    Tests the categorizer using the `data_content` argument.
    '''
    c = Categorizer(data_content=DATA_CONTENT)
    assert len(c.raw_data) == 2
    assert len(c.data) == 2
    T1U_cat = c.cat(T1U)
    assert T1U_cat.name == 'Pizza Planet'
    assert set(T1U_cat.tags) == set(['food', 'pizza'])
    assert T1U_cat.is_categorized()
    assert T1U_cat.is_named()
    T2U_cat = c.cat(T2U)
    assert T2U_cat.name is None
    assert len(T2U_cat.tags) == 0
    assert not T2U_cat.is_categorized()
    assert not T2U_cat.is_named()
    T3U_cat = c.cat(T3U)
    assert T3U_cat.name == 'Pizza Planet'
    assert set(T3U_cat.tags) == set(['food', 'pizza'])
    assert T3U_cat.is_categorized()
    assert T3U_cat.is_named()
    T4U_cat = c.cat(T4U)
    assert T4U_cat.name == 'Sub Shop'
    assert set(T4U_cat.tags) == set(['food', 'subs'])
    assert T4U_cat.is_categorized()
    assert T4U_cat.is_named()
    TU_cat  = c.cat(TU)
    assert [t.is_categorized() for t in TU_cat] == [True, False, True, True]
