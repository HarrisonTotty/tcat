'''
Contains the definition of a transaction object.
'''

import copy
import dataclasses
import datetime
import statistics

@dataclasses.dataclass
class Transaction:
    '''
    Represents a particular transaction.
    '''

    account: str
    amount: float
    balance: float
    bank: str
    date: datetime.datetime
    desc: str
    name: str = None
    notes: str = None
    tags: list[str] = []

    def is_categorized(self) -> bool:
        '''
        Returns whether this transaction has been categorized (assigned at least
        one tag).
        '''
        return len(tags) > 0


@dataclasses.dataclass
class Transactions:
    '''
    Represents a collection of transactions.
    '''
    items: list[Transaction]

    def __iter__(self):
        '''
        Iterator implementation.
        '''
        yield from self.items

    def counts(self) -> dict:
        '''
        Returns a dictionary of name-count pairs within this collection of transactions.
        '''
        counts = {}
        for t in self:
            if t.name:
                if t.name in counts:
                    counts[t.name] += 1
                else:
                    counts[t.name] = 1
            else:
                if 'UNKNOWN' in counts:
                    counts['UNKNOWN'] += 1
                else:
                    counts['UNKNOWN'] = 1

    def coverage(self) -> float:
        '''
        Returns the percentage of transactions which have been categorized.
        '''
        puncat = len(self.uncategorized()) / len(self.items)
        return round((1 - puncat) * 100, 2)

    def filter(self, **kwargs) -> Transactions:
        '''
        Filters a list of transactions according to a function filtering by:
          * bank
          * account
          * tags (as a set)
          * name
          * description
          * notes
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
          * A string for the `name`, `desc`, or `notes` keyword argument. These
            comparisons are case-insensitive and will match on substring as well.
          * A string for the `amount` keyword argument, being either `deposit` or
            `withdrawal`, their shorthand forms `d` or `w`, or `+` or `-`.
          * A tuple of integers or floats for the `amount` keyword argument. These
            are taken to constitute a range of amounts (inclusive).
          * A `datetime.datetime` object for the `date` keyword argument, for which
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
        most_recent_date = max([t.date for t in self])
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
                        if kwargs['name'].lower() in t.name.lower(): continue
                    else:
                        if not kwargs['name'].lower() in t.name.lower(): continue
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
            if 'notes' in kwargs:
                if isinstance(kwargs['notes'], str):
                    if negate:
                        if kwargs['notes'].lower() in t.notes.lower(): continue
                    else:
                        if not kwargs['notes'].lower() in t.notes.lower(): continue
                else:
                    if negate:
                        if kwargs['notes'](t.notes): continue
                    else:
                        if not kwargs['notes'](t.notes): continue
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
                    while len(sd1) < 3: sd1.append(1)
                    lowerbound = datetime.datetime(*sd1)
                    upperbound = datetime.datetime(*sd2)
                    if negate:
                        if t.date >= lowerbound and t.date <= upperbound: continue
                    else:
                        if t.date < lowerbound or t.date > upperbound: continue
                elif isinstance(kwargs['date'], datetime.datetime):
                    if negate:
                        if t.date.date() == kwargs['date'].date(): continue
                    else:
                        if t.date.date() != kwargs['date'].date(): continue
                else:
                    if negate:
                        if kwargs['date'](t.date): continue
                    else:
                        if not kwargs['date'](t.date): continue
            filtered.append(copy.deepcopy(t))
        return Transactions(items = filtered)

    def max_amount(self) -> float:
        '''
        Returns the maximum amount in this collection.
        '''
        return max([t.amount for t in self])

    def max_balance(self) -> float:
        '''
        Returns the maximum balance in this collection.
        '''
        return max([t.balance for t in self])

    def mean_amount(self) -> float:
        '''
        Returns the mean amount in this collection.
        '''
        return round(statistics.mean([t.amount for t in self]), 2)

    def mean_balance(self) -> float:
        '''
        Returns the mean balance in this collection.
        '''
        return round(statistics.mean([t.balance for t in self]), 2)

    def median_amount(self) -> float:
        '''
        Returns the mean amount in this collection.
        '''
        return round(statistics.median([t.amount for t in self]), 2)

    def median_balance(self) -> float:
        '''
        Returns the mean balance in this collection.
        '''
        return round(statistics.median([t.balance for t in self]), 2)

    def min_amount(self) -> float:
        '''
        Returns the minimum amount in this collection.
        '''
        return min([t.amount for t in self])

    def min_balance(self) -> float:
        '''
        Returns the minimum balance in this collection.
        '''
        return min([t.balance for t in self])

    def sorted_by(self, key='date', reverse=False):
        '''
        Sorts the collection of transactions, returning a new, sorted collection.

        The `key` parameter may be specified as:
          * A function/lambda on each transaction.
          * A string corresponding to the field to sort by (for example: `date`).
        '''
        return []

    def tags(self):
        '''
        Returns the list of all tags present in this list of transactions.
        '''
        tgs = []
        for t in self:
            tgs.extend(t.tags)
        return sorted(list(set(tgs)))

    def stdev_amount(self) -> float:
        '''
        Returns the standard deviation of amounts in this collection.
        '''
        return round(statistics.stdev([t.amount for t in self]), 2)

    def stdev_balance(self) -> float:
        '''
        Returns the standard deviation of balances in this collection.
        '''
        return round(statistics.stdev([t.balance for t in self]), 2)

    def uncategorized(self) -> Transactions:
        '''
        Returns which transactions have yet to be categorized.
        '''
        return Transactions(items = [t for t in self if not t.is_categorized()])
