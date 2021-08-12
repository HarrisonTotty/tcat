'''
Contains the definition of a transaction object.
'''

from __future__ import annotations

import copy
import dataclasses
import datetime
import dateutil.relativedelta
import dateutil.rrule
import json
import math
import numpy
import statistics
from typing import Any, Optional, Union

DATE_FORMAT = '%Y/%m/%d'
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

@dataclasses.dataclass
class Transaction:
    '''
    Represents a particular transaction.
    '''

    account: str
    amount: float
    balance: float
    bank: str
    date: datetime.date
    desc: str
    name: Optional[str] = dataclasses.field(compare=False, default=None)
    note: Optional[str] = dataclasses.field(compare=False, default=None)
    tags: list[str] = dataclasses.field(compare=False, default_factory=list)

    def __getitem__(self, key: str) -> Any:
        '''
        Allows one to access fields of a transaction via dictionary syntax.
        '''
        return self.__dict__[key]

    def __hash__(self) -> Any:
        '''
        Returns the hash representation of the transaction.
        '''
        return hash((self.account, self.amount, self.balance, self.bank, self.date, self.desc))

    def __len__(self) -> int:
        '''
        Returns the number of tags associated with this transaction.
        '''
        return len(self.tags)

    def __str__(self) -> str:
        '''
        Returns the string representation of the transaction. This is an alias
        of the `to_json()` method.
        '''
        return self.to_json()

    @staticmethod
    def from_json(jsonstr: str) -> Transaction:
        '''
        Creates a new transaction from the specified JSON string.
        '''
        rep = json.loads(jsonstr)
        return Transaction.from_datestr_dict(rep)

    @staticmethod
    def from_datestr_dict(jsondict: dict) -> Transaction:
        '''
        Creates a new transaction from a dictionary object containing unparsed
        date strings.
        '''
        rep = copy.deepcopy(jsondict)
        rep['date'] = datetime.datetime.strptime(rep['date'], DATE_FORMAT).date()
        return Transaction(**rep)

    def has_note(self) -> bool:
        '''
        Returns whether this transaction has a non-`None` value of the `note`
        field that is also not empty.
        '''
        return (not self.note is None) and self.note

    def is_categorized(self) -> bool:
        '''
        Returns whether this transaction has been categorized (assigned at least
        one tag).
        '''
        return len(self.tags) > 0

    def is_named(self) -> bool:
        '''
        Returns whether this transaction has a `name` that is not `None` and
        not empty.
        '''
        return (not self.name is None) and self.name

    def keys(self) -> list[str]:
        '''
        Returns the keys associated with this class.
        '''
        return self.__dict__.keys()

    def to_datestr_dict(self) -> str:
        '''
        Converts the transaction into a dictionary where the `date` field is set
        to its string representation.
        '''
        rep = copy.deepcopy(self.__dict__)
        rep['date'] = rep['date'].strftime(DATE_FORMAT)
        return rep

    def to_json(self) -> str:
        '''
        Converts this transaction into a JSON string representation.
        '''
        return json.dumps(self.to_datestr_dict())



@dataclasses.dataclass
class Transactions:
    '''
    Represents a collection of transactions.
    '''
    items: list[Transaction]

    def __getitem__(self, index: int) -> Transaction:
        '''
        Allows one to access transactions using index notation.
        '''
        return self.items[index]

    def __iter__(self):
        '''
        Iterator implementation.
        '''
        yield from self.items

    def __len__(self) -> int:
        '''
        Returns the number of items within this transaction.
        '''
        return len(self.items)

    def accounts(self, bank: Optional[str] = None) -> list[str]:
        '''
        Returns the set of all accounts associated with this list. Optionally,
        the collection may be limited by those associated with a particular
        bank (case insensitive).
        '''
        acc = []
        for t in self:
            if not bank is None and bank:
                if t.bank.lower() != bank.lower(): continue
            acc.append(t.account)
        return list(set(acc))

    def banks(self) -> list[str]:
        '''
        Returns the set of all banks associated with this list.
        '''
        return list(set(t.bank for t in self))

    def counts(self) -> dict[str, int]:
        '''
        Returns a dictionary of name-count pairs within this collection of transactions.
        '''
        counts = {}
        for t in self:
            if not t.name is None and t.name:
                if t.name in counts:
                    counts[t.name] += 1
                else:
                    counts[t.name] = 1
            else:
                if 'UNKNOWN' in counts:
                    counts['UNKNOWN'] += 1
                else:
                    counts['UNKNOWN'] = 1
        return counts

    def coverage(self) -> float:
        '''
        Returns the percentage of transactions which have been categorized.
        '''
        puncat = len(self.uncategorized()) / len(self.items)
        return round((1 - puncat) * 100, 2)

    def dates(self) -> list[datetime.date]:
        '''
        Returns the set of all dates associated with this list of transactions.
        '''
        return list(set(t.date for t in self.items))

    def descs(self) -> list[str]:
        '''
        Returns the set of all transaction descriptions.
        '''
        return list(set(t.desc for t in self.items))

    def filter(self, **kwargs) -> Transactions:
        '''
        Filters a list of transactions according to a function filtering by:
          * bank
          * account
          * tags (as a set)
          * name
          * description
          * note
          * dollar amount
          * date
          * Some combination of the above (applied in that order)
        In addition to functions/lambdas you can also specify:
          * A string for the `account` or `bank` keyword arguments. These
            comparisons are case-insensitive.
          * A list of tags for the `tags` keyword argument (at least one of those
            specified must be present for the transaction to be included).
          * A single tag string for the `tags` keyword argument. The transaction
            must contain the specified tag to be included.
          * A string for the `name`, `desc`, or `note` keyword argument. These
            comparisons are case-insensitive and will match on substring as well.
          * A string for the `amount` keyword argument, being either `deposit` or
            `withdrawal`, their shorthand forms `d` or `w`, or `+` or `-`.
          * A tuple of integers or floats for the `amount` keyword argument. These
            are taken to constitute a range of amounts (inclusive).
          * A `datetime.date` object for the `date` keyword argument, for which
            all transactions with the same `.date()` will be kept.
          * An integer for the `date` keyword argument, indicating to filter by the
            `n` most recent days.
          * A date string of the form `%Y`, `%Y/%m`, or `%Y/%m/%d` for the `date`
            keyword argument.
          * A tuple of date strings for the `date` keyword argument, each of the
            form above. These are taken to constitute a range of dates (inclusive).
        If `negate` is set to True, then each filter specification is reversed. For
        example, if you specified an array of tag strings for the `tags` keyword
        argument but set `negate` to `True`, then the result of this function would
        be the list of all transactions that did _not_ contain any of the specified
        tags.
        '''
        ALLOWED_KEYS = [
            'account',
            'amount',
            'balance',
            'bank',
            'date',
            'desc',
            'name',
            'negate',
            'note',
            'tags'
        ]
        for key in kwargs:
            if not key in ALLOWED_KEYS:
                raise Exception(f'unknown filter key "{key}"')
        if len(self.items) < 2: return copy.deepcopy(self)
        most_recent_date = max(self.dates())
        filtered = []
        negate = 'negate' in kwargs and kwargs['negate']
        for t in self:
            if 'bank' in kwargs:
                if isinstance(kwargs['bank'], str):
                    if negate:
                        if kwargs['bank'].lower() == t.bank.lower(): continue
                    else:
                        if kwargs['bank'].lower() != t.bank.lower(): continue
                else:
                    if negate:
                        if kwargs['bank'](t.bank): continue
                    else:
                        if not kwargs['bank'](t.bank): continue
            if 'account' in kwargs:
                if isinstance(kwargs['account'], str):
                    if negate:
                        if kwargs['account'].lower() == t.account.lower(): continue
                    else:
                        if kwargs['account'].lower() != t.account.lower(): continue
                else:
                    if negate:
                        if kwargs['account'](t.account): continue
                    else:
                        if not kwargs['account'](t.account): continue
            if 'tags' in kwargs:
                if isinstance(kwargs['tags'], str):
                    if negate:
                        if kwargs['tags'] in t.tags: continue
                    else:
                        if not kwargs['tags'] in t.tags: continue
                elif isinstance(kwargs['tags'], list):
                    if negate:
                        if (True in [(tag in t.tags) for tag in kwargs['tags']]): continue
                    else:
                        if not (True in [(tag in t.tags) for tag in kwargs['tags']]): continue
                else:
                    if negate:
                        if kwargs['tags'](set(t.tags)): continue
                    else:
                        if not kwargs['tags'](set(t.tags)): continue
            if 'name' in kwargs:
                if isinstance(kwargs['name'], str):
                    if negate:
                        if t.is_named() and kwargs['name'].lower() in t.name.lower(): continue
                    else:
                        if not t.is_named() or not kwargs['name'].lower() in t.name.lower(): continue
                else:
                    if negate:
                        if kwargs['name'](t.name): continue
                    else:
                        if not kwargs['name'](t.name): continue
            if 'desc' in kwargs:
                if isinstance(kwargs['desc'], str):
                    if negate:
                        if kwargs['desc'].lower() in t.desc.lower(): continue
                    else:
                        if not kwargs['desc'].lower() in t.desc.lower(): continue
                else:
                    if negate:
                        if kwargs['desc'](t.desc): continue
                    else:
                        if not kwargs['desc'](t.desc): continue
            if 'note' in kwargs:
                if isinstance(kwargs['note'], str):
                    if negate:
                        if t.has_note() and kwargs['note'].lower() in t.note.lower(): continue
                    else:
                        if not t.has_note() or not kwargs['note'].lower() in t.note.lower(): continue
                else:
                    if negate:
                        if kwargs['note'](t.note): continue
                    else:
                        if not kwargs['note'](t.note): continue
            if 'amount' in kwargs:
                if isinstance(kwargs['amount'], str):
                    if kwargs['amount'].lower() in ['+', 'd', 'deposit']:
                        if negate:
                            if t.amount > 0: continue
                        else:
                            if t.amount <= 0: continue
                    if kwargs['amount'].lower() in ['-', 'w', 'withdrawal']:
                        if negate:
                            if t.amount < 0: continue
                        else:
                            if t.amount >= 0: continue
                elif isinstance(kwargs['amount'], tuple):
                    if negate:
                        if t.amount >= kwargs['amount'][0] and t.amount <= kwargs['amount'][1]: continue
                    else:
                        if t.amount < kwargs['amount'][0] or t.amount > kwargs['amount'][1]: continue
                else:
                    if negate:
                        if kwargs['amount'](t.amount): continue
                    else:
                        if not kwargs['amount'](t.amount): continue
            if 'date' in kwargs:
                if isinstance(kwargs['date'], int):
                    if negate:
                        if (most_recent_date - t.date).days <= kwargs['date']: continue
                    else:
                        if (most_recent_date - t.date).days > kwargs['date']: continue
                elif isinstance(kwargs['date'], str):
                    sd = list(map(int, kwargs['date'].split('/')))
                    if negate:
                        if len(sd) >= 1 and t.date.year == sd[0]: continue
                        if len(sd) >= 2 and t.date.month == sd[1]: continue
                        if len(sd) >= 3 and t.date.day == sd[2]: continue
                    else:
                        if len(sd) >= 1 and t.date.year != sd[0]: continue
                        if len(sd) >= 2 and t.date.month != sd[1]: continue
                        if len(sd) >= 3 and t.date.day != sd[2]: continue
                elif isinstance(kwargs['date'], tuple):
                    sd1 = list(map(int, kwargs['date'][0].split('/')))
                    while len(sd1) < 3: sd1.append(1)
                    sd2 = list(map(int, kwargs['date'][1].split('/')))
                    if len(sd2) < 2: sd2.append(12)
                    if len(sd2) < 3: sd2.append(DAYS_IN_MONTH[sd2[1] - 1])
                    lowerbound = datetime.date(*sd1)
                    upperbound = datetime.date(*sd2)
                    if negate:
                        if t.date >= lowerbound and t.date <= upperbound: continue
                    else:
                        if t.date < lowerbound or t.date > upperbound: continue
                elif isinstance(kwargs['date'], datetime.date):
                    if negate:
                        if t.date == kwargs['date']: continue
                    else:
                        if t.date != kwargs['date']: continue
                else:
                    if negate:
                        if kwargs['date'](t.date): continue
                    else:
                        if not kwargs['date'](t.date): continue
            filtered.append(copy.deepcopy(t))
        return Transactions(items = filtered)

    @staticmethod
    def from_json(jsonstr: str) -> Transactions:
        '''
        Creates a new list of transactions given a JSON string representation.
        '''
        ts = []
        data = json.loads(jsonstr)
        for tjson in data:
            ts.append(Transaction.from_datestr_dict(tjson))
        return Transactions(ts)

    def group(self, by: str = 'date-monthly', drange: int = 100.0, include_empty: bool = False, interval: int = 1) -> dict[Any, Transactions]:
        '''
        Groups transactions by one of the following criteria:
          * key = str
            * desc
            * name
          * key = tuple[date, date]
            * date-daily
            * date-monthly
            * date-weekly
            * date-yearly
          * key = tuple[float, float]
            * amount
            * balance
          * key = tuple[str, str]
            * bank-account
          * key = tuple[str, ...]
            * tags
        Depending on the criteria, the collection of transactions will
        automatically be sorted. If `include_empty` is set to `False`, any empty
        groups (typically present when grouping by date) will be removed. The
        `interval` argument may be adjusted to skip time periods when grouping
        by date. For example, an `interval` of `2` when `by` is set to
        `date-weekly` would imply to group by every other week. The `drange`
        argument allows one to specify the dollar range between bins when
        grouping by `amount` or `balance`. In the case of grouping by tags or
        names, all uncategorized transactions will be under the `None` key if
        `include_empty` is set to `True`.
        '''
        if len(self.items) < 1: return {}
        res = {}
        if by == 'amount':
            items = self.sort(key='amount').items
        elif by == 'balance':
            items = self.sort(key='balance').items
        else:
            items = self.sort().items
        if by == 'bank-account':
            for bank in self.banks():
                for account in self.accounts(bank):
                    res[(bank, account)] = Transactions([t for t in items if t.bank == bank and t.account == account])
        elif by.startswith('date-'):
            freq = {
                'date-daily': (dateutil.rrule.DAILY, items[0].date, dateutil.relativedelta.relativedelta(days=1)),
                'date-monthly': (dateutil.rrule.MONTHLY, items[0].date.replace(day=1), dateutil.relativedelta.relativedelta(months=1)),
                'date-weekly': (dateutil.rrule.WEEKLY, items[0].date, dateutil.relativedelta.relativedelta(weeks=1)),
                'date-yearly': (dateutil.rrule.YEARLY, items[0].date.replace(month=1, day=1), dateutil.relativedelta.relativedelta(years=1))
            }
            datesteps = list(dateutil.rrule.rrule(
                freq[by][0],
                dtstart  = freq[by][1],
                interval = interval,
                until    = items[-1].date + freq[by][2],
                wkst     = dateutil.rrule.SU
            ))
            dateranges = [(datesteps[i].date(), datesteps[i+1].date()) for i in range(len(datesteps) - 1)]
            for lower, upper in dateranges:
                selected_items = [t for t in items if t.date >= lower and t.date < upper]
                if not include_empty and not selected_items: continue
                for t in selected_items: items.remove(t)
                res[(lower, upper)] = Transactions(selected_items)
        elif by == 'amount':
            for rl in numpy.arange(math.floor(items[0].amount), math.ceil(items[-1].amount) + drange + 2.0, float(drange)):
                lower = round(rl, 2)
                upper = round(lower + drange, 2)
                selected_items = [t for t in items if t.amount >= lower and t.amount < upper]
                if not include_empty and not selected_items: continue
                for t in selected_items: items.remove(t)
                res[(lower, upper)] = Transactions(selected_items)
        elif by == 'balance':
            for rl in numpy.arange(math.floor(items[0].balance), math.ceil(items[-1].balance) + drange + 2.0, float(drange)):
                lower = round(rl, 2)
                upper = round(lower + drange, 2)
                selected_items = [t for t in items if t.balance >= lower and t.balance < upper]
                if not include_empty and not selected_items: continue
                for t in selected_items: items.remove(t)
                res[(lower, upper)] = Transactions(selected_items)
        elif by == 'desc':
            for desc in self.descs():
                res[desc] = Transactions([t for t in items if t.desc == desc])
        elif by == 'name':
            for name in self.names():
                res[name] = Transactions([t for t in items if t.name == name])
            if include_empty:
                res[None] = Transactions([t for t in items if not t.is_named()])
        elif by == 'tags':
            collections = {}
            for i in items:
                if i.tags:
                    tags = tuple(sorted(i.tags))
                elif include_empty:
                    tags = None
                else:
                    continue
                if not tags in collections:
                    collections[tags] = [i]
                else:
                    collections[tags].append(i)
            res = {k: Transactions(v) for k, v in collections.items()}
        return res

    def hovertext(self, pkey: str = 'name', skey: Optional[str] = 'amount') -> str:
        '''
        Gets the "hovertext" (tooltip) associated with this list of
        transactions. If a secondary key is provided, that key will be shown
        in parentheses next to the primary key.
        '''
        htarray = []
        for t in self.items:
            tstr = '?'
            tdict = dict(t)
            pval = tdict.get(pkey)
            if not pval is None: tstr = f'{pval}'
            if not skey is None:
                sval = tdict.get(skey)
                if not sval is None:
                    tstr = f'{tstr} ({sval})'
                else:
                    tstr = f'{tstr} (?)'
            htarray.append(tstr)
        return ' | '.join(htarray)

    @staticmethod
    def load(file_path: str) -> Transactions:
        '''
        Loads a list of transactions from the specified file path.
        '''
        with open(file_path, 'r') as f:
            return Transactions.from_json(f.read())

    def max_amount(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the maximum amount in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return max([abs(t.amount) for t in self])
        else:
            return max([t.amount for t in self])

    def max_balance(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the maximum balance in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return max([abs(t.balance) for t in self])
        else:
            return max([t.balance for t in self])

    def mean_amount(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the mean amount in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return round(statistics.mean([abs(t.amount) for t in self]), 2)
        else:
            return round(statistics.mean([t.amount for t in self]), 2)

    def mean_balance(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the mean balance in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return round(statistics.mean([abs(t.balance) for t in self]), 2)
        else:
            return round(statistics.mean([t.balance for t in self]), 2)

    def mean_freq(self, scale: str = 'daily') -> Optional[float]:
        '''
        Returns the mean frequency (number of transactions) on a given time
        scale, being `daily`, `weekly`, `monthly`, or `yearly`.
        '''
        if len(self.items) < 1: return None
        if not scale in ['daily', 'weekly', 'monthly', 'yearly']:
            raise Exception('please specify an appropriate time scale')
        grouped = self.group(by=f'date-{scale}', include_empty=True)
        return round(statistics.mean([len(ts) for d, ts in grouped.items()]), 4)

    def median_freq(self, scale: str = 'daily') -> Optional[float]:
        '''
        Returns the median frequency (number of transactions) on a given time
        scale, being `daily`, `weekly`, `monthly`, or `yearly`.
        '''
        if len(self.items) < 1: return None
        if not scale in ['daily', 'weekly', 'monthly', 'yearly']:
            raise Exception('please specify an appropriate time scale')
        grouped = self.group(by=f'date-{scale}', include_empty=True)
        return round(statistics.median([len(ts) for d, ts in grouped.items()]), 4)

    def median_amount(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the mean amount in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return round(statistics.median([abs(t.amount) for t in self]), 2)
        else:
            return round(statistics.median([t.amount for t in self]), 2)

    def median_balance(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the mean balance in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return round(statistics.median([abs(t.balance) for t in self]), 2)
        else:
            return round(statistics.median([t.balance for t in self]), 2)

    @staticmethod
    def merge(*args) -> Transactions:
        '''
        Merges one or more transaction lists into a single one. The result is
        then sorted by transaction date. The merging process will automatically
        delete duplicate entries, but the last arguments have preference.
        '''
        merged = []
        for tlist in args:
            for t in tlist:
                ct = copy.deepcopy(t)
                if not ct in merged:
                    merged.append(ct)
                else:
                    di = merged.index(ct)
                    dc = copy.deepcopy(merged[di])
                    if ct.is_named() or not dc.is_named():
                        dc.name = ct.name
                    if ct.has_note() or not dc.has_note():
                        dc.note = ct.note
                    if ct.is_categorized() or not dc.is_categorized():
                        dc.tags = ct.tags
                    merged[di] = dc
        return Transactions(merged).sort()

    def min_amount(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the minimum amount in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return min([abs(t.amount) for t in self])
        else:
            return min([t.amount for t in self])

    def min_balance(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the minimum balance in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1: return None
        if absolute_value:
            return min([abs(t.balance) for t in self])
        else:
            return min([t.balance for t in self])

    def names(self) -> list[str]:
        '''
        Returns the list of all transaction names. Transactions without a name
        will not be considered.
        '''
        return list(set(t.name for t in self.items if not t.name is None))

    def save(self, file_path: str):
        '''
        Saves the list of transactions to the specified file path.
        '''
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    def sort(self, key: Any = 'date', reverse: bool = False) -> Transactions:
        '''
        Sorts the collection of transactions, returning a new, sorted collection.

        The `key` parameter may be specified as:
          * A function/lambda on each transaction.
          * A string corresponding to the field to sort by (for example: `date`).
        '''
        if isinstance(key, str):
            return Transactions(sorted(copy.deepcopy(self.items), key = lambda x: x[key], reverse=reverse))
        else:
            return Transactions(sorted(copy.deepcopy(self.items), key=key, reverse=reverse))

    def statistics(self) -> dict[str, Optional[Union[int, float]]]:
        '''
        Computes helpful statistics associated with this collection of
        transactions. The result is a dictionary containing the following
        keys:
        * count
        * max_[abs_amount, abs_balance, amount, balance]
        * mean_[abs_amount, abs_balance, amount, balance]
        * mean_freq_[daily, monthly, weekly, yearly]
        * median_[abs_amount, abs_balance, amount, balance]
        * median_freq_[daily, monthly, weekly, yearly]
        * min_[abs_amount, abs_balance, amount, balance]
        * stdev_[abs_amount, abs_balance, amount, balance]
        * stdev_freq_[daily, monthly, weekly, yearly]
        * total_[abs_amount, abs_balance, amount, balance]
        '''
        return {
            'count': len(self.items),
            'max_abs_amount': self.max_amount(absolute_value=True),
            'max_abs_balance': self.max_balance(absolute_value=True),
            'max_amount': self.max_amount(),
            'max_balance': self.max_balance(),
            'mean_abs_amount': self.mean_amount(absolute_value=True),
            'mean_abs_balance': self.mean_balance(absolute_value=True),
            'mean_amount': self.mean_amount(),
            'mean_balance': self.mean_balance(),
            'mean_freq_daily': self.mean_freq(scale='daily'),
            'mean_freq_monthly': self.mean_freq(scale='monthly'),
            'mean_freq_weekly': self.mean_freq(scale='weekly'),
            'mean_freq_yearly': self.mean_freq(scale='yearly'),
            'median_abs_amount': self.median_amount(absolute_value=True),
            'median_abs_balance': self.median_balance(absolute_value=True),
            'median_amount': self.median_amount(),
            'median_balance': self.median_balance(),
            'median_freq_daily': self.median_freq(scale='daily'),
            'median_freq_monthly': self.median_freq(scale='monthly'),
            'median_freq_weekly': self.median_freq(scale='weekly'),
            'median_freq_yearly': self.median_freq(scale='yearly'),
            'min_abs_amount': self.min_amount(absolute_value=True),
            'min_abs_balance': self.min_balance(absolute_value=True),
            'min_amount': self.min_amount(),
            'min_balance': self.min_balance(),
            'stdev_abs_amount': self.stdev_amount(absolute_value=True),
            'stdev_abs_balance': self.stdev_balance(absolute_value=True),
            'stdev_amount': self.stdev_amount(),
            'stdev_balance': self.stdev_balance(),
            'stdev_freq_daily': self.stdev_freq(scale='daily'),
            'stdev_freq_monthly': self.stdev_freq(scale='monthly'),
            'stdev_freq_weekly': self.stdev_freq(scale='weekly'),
            'stdev_freq_yearly': self.stdev_freq(scale='yearly'),
            'total_abs_amount': self.total_amount(absolute_value=True),
            'total_abs_balance': self.total_balance(absolute_value=True),
            'total_amount': self.total_amount(),
            'total_balance': self.total_balance()
        }

    def stdev_amount(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the standard deviation of amounts in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1:
            return None
        elif len(self.items) == 1:
            return 0.0
        if absolute_value:
            return round(statistics.stdev([abs(t.amount) for t in self]), 2)
        else:
            return round(statistics.stdev([t.amount for t in self]), 2)

    def stdev_balance(self, absolute_value: bool = False) -> Optional[float]:
        '''
        Returns the standard deviation of balances in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1:
            return None
        elif len(self.items) == 1:
            return 0.0
        if absolute_value:
            return round(statistics.stdev([abs(t.balance) for t in self]), 2)
        else:
            return round(statistics.stdev([t.balance for t in self]), 2)

    def stdev_freq(self, scale: str = 'daily') -> Optional[float]:
        '''
        Returns the standard deviation of frequency (number of transactions) on
        a given time scale, being `daily`, `weekly`, `monthly`, or `yearly`.
        '''
        if not scale in ['daily', 'weekly', 'monthly', 'yearly']:
            raise Exception('please specify an appropriate time scale')
        grouped = self.group(by=f'date-{scale}', include_empty=True)
        if len(grouped) < 1:
            return None
        elif len(grouped) == 1:
            return 0.0
        return round(statistics.stdev([len(ts) for d, ts in grouped.items()]), 4)

    def tags(self) -> list[str]:
        '''
        Returns the list of all tags present in this list of transactions.
        '''
        tgs = []
        for t in self:
            tgs.extend(t.tags)
        return sorted(list(set(tgs)))

    def to_json(self) -> str:
        '''
        Converts the list of transactions into a JSON object.
        '''
        ts = []
        for t in self:
            ts.append(t.to_datestr_dict())
        return json.dumps(ts)

    def to_structured_dict(self) -> dict[str, dict]:
        '''
        Converts this collection of transactions into a structured dictionary of
        the form:
        bank.account.date.[amounts, balances, descs, names, tags]

        for example:
        {
          'bank1': {
            'checking': {
              date(2020, 04, 03): {
                'amounts': [1.23, -9.65, 8.33],
                'balances': [100.000, 90.35, 98.68]
                # ...
              }
            },
            'savings': {
              # ...
            }
          }
        }
        '''
        raise NotImplementedError()


    def total_amount(self, absolute_value: bool = False) -> float:
        '''
        Returns the total (sum) of amounts in this collection.
        If `absolute_value` is set to true, the "sign" of each amount will be
        ignored.
        '''
        if len(self.items) < 1:
            return 0.0
        if absolute_value:
            return round(sum([abs(t.amount) for t in self]), 2)
        else:
            return round(sum([t.amount for t in self]), 2)

    def total_balance(self, absolute_value: bool = False) -> float:
        '''
        Returns the total (sum) of balances in this collection.
        If `absolute_value` is set to true, the "sign" of each balance will be
        ignored.
        '''
        if len(self.items) < 1:
            return 0.0
        if absolute_value:
            return round(sum([abs(t.balance) for t in self]), 2)
        else:
            return round(sum([t.balance for t in self]), 2)

    def uncategorized(self) -> Transactions:
        '''
        Returns which transactions have yet to be categorized.
        '''
        return Transactions(items = [t for t in self if not t.is_categorized()])
