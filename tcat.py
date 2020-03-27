#!/usr/bin/env python3
'''
tcat

Banking transaction categorization library for Python.
'''

import copy
import csv
import datetime
import glob
import os
import re
import statistics
import sys
import yaml

class Categorizer:
    '''
    An object that can translate a raw bank transaction.
    '''
    def __init__(self, data_directory):
        '''
        Creates a new transaction `Categorizer` built from the specified data
        directory.
        '''
        full_data_directory = os.path.expanduser(data_directory)
        if not os.path.isdir(full_data_directory):
            raise Exception('specified data directory does not exist')
        data_files = glob.glob(os.path.join(full_data_directory, '*.yaml'))
        if not data_files:
            raise Exception(
                'specified data directory does not contain any data files'
            )
        self.raw_data = []
        for data_file in data_files:
            try:
                with open(data_file, 'r') as f:
                    self.raw_data.append(yaml.safe_load(f.read()))
            except Exception as e:
                raise Exception(
                    'unable to parse data file "{d}" - {e}'.format(
                        d = data_file,
                        e = str(e)
                    )
                )
        self.data = []
        for pdata in self.raw_data:
            if not 'data' in pdata:
                raise Exception(
                    'one or more parsed data files does not have a "data" key'
                )
            rendered_pdata = copy.deepcopy(pdata)
            for i, d in enumerate(pdata['data']):
                if not 'name' in d or not 'match' in d:
                    raise Exception(
                        'one or more parsed data files has invalid data'
                    )
                rendered_pdata['data'][i]['match'] = re.compile(d['match'].strip())
            self.data.append(rendered_pdata)

    def cat(self, desc):
        '''
        An alias for `categorize`.
        '''
        return self.categorize(desc)

    def categorize(self, desc):
        '''
        Categorizes a transaction description, returning a "pretty" name for the
        transaction, as well as a collection of tags to assign the transaction.
        '''
        cat = {}
        ldesc = desc.lower()
        found = False
        for d1 in self.data:
            if found: break
            for d2 in d1['data']:
                if found: break
                if d2['match'].search(ldesc):
                    cat['name'] = copy.deepcopy(d2['name'])
                    if 'tags' in d1:
                        cat['tags'] = copy.deepcopy(d1['tags'])
                    if 'tags' in d2:
                        cat['tags'].extend(copy.deepcopy(d2['tags']))
                    found = True
        if 'tags' in cat:
            cat['tags'] = list(set(cat['tags']))
        return cat

    def categorize_transactions(self, transactions):
        '''
        Categorizes a list of transaction dictionaries.
        '''
        cat = []
        for t in transactions:
            tc = copy.deepcopy(t)
            if cdesc := self.categorize(t['desc']):
                tc['name'] = cdesc['name']
                tc['tags'] = cdesc['tags']
            cat.append(tc)
        return cat

    def tcat(self, transactions):
        '''
        An alias for `categorize_transactions`.
        '''
        return self.categorize_transactions(transactions)


def dstr(amount):
    '''
    Converts a monetary amount to a string.
    '''
    ra = abs(round(amount, 2))
    if amount < 0: return '-${0:.2f}'.format(ra)
    return '${0:.2f}'.format(ra)


def parse_csv(csv_file, bank=None, account=None):
    '''
    Parses the specified bank CSV file, optionally specifying the bank and
    account the file represents. If the bank and account are not specified, it
    is constructed from the file name assuming the format: BANK-ACCOUNT.csv

    The resulting transactions are not automatically categorized.
    '''
    cf = os.path.expanduser(csv_file)
    cname = os.path.basename(csv_file).split('.', 1)[0]
    if '-' in cname:
        cname_split = cname.split('-', 1)
        if not bank:
            the_bank = cname_split[0]
        else:
            the_bank = bank
        if not account:
            the_account = cname_split[1]
        else:
            the_account = account
    else:
        the_bank = bank
        the_account = account
    with open(cf, 'r') as f:
        init_parse = [x for x in csv.DictReader(f)]
    parsed = []
    if the_bank.lower() == 'alliant':
        for d in init_parse:
            parsed.append({
                'account': the_account,
                'amount': float(d['Amount'].replace('$', '')),
                'bal': float(d['Balance'].replace('$', '')),
                'bank': the_bank,
                'date': datetime.datetime.strptime(d['Date'], '%m/%d/%Y'),
                'desc': d['Description'].replace('&#39;', "'").replace('&amp;', '&'),
                'tags': []
            })
    return parsed


def tags(transactions):
    '''
    Returns the list of all tags present in the specified list of transactions.
    '''
    tags = []
    for t in transactions:
        tags.extend(t['tags'])
    return sorted(list(set(tags)))


def tcounts(transactions):
    '''
    Returns a dictionary of transaction name-count pairs given the specified list of transactions.
    '''
    counts = {}
    for t in transactions:
        if 'name' in t and t['name']:
            if t['name'] in counts:
                counts[t['name']] += 1
            else:
                counts[t['name']] = 1
        else:
            if 'UNKNOWN' in counts:
                counts['UNKNOWN'] += 1
            else:
                counts['UNKNOWN'] = 1
    return {k: counts[k] for k in sorted(counts, key=counts.get, reverse=True)}


def tcoverage(transactions):
    '''
    Returns the percentage of transactions which have been categorized.
    '''
    puncat = len(tuncat(transactions)) / len(transactions)
    return round((1 - puncat) * 100, 2)


def tfilter(transactions, account=None, amount=None, bank=None, date=None, desc=None, name=None, tags=None):
    '''
    Filters a list of transactions according to a function filtering by:
      * bank
      * account
      * tags (as a set)
      * name
      * description
      * dollar amount
      * date
      * Some combination of the above (applied in that order)
    In addition to functions/lambdas you can also specify:
      * a string for the `account` or `bank` keyword arguments. These
        comparisons are case-insensitive.
      * a list of tags for the `tags` keyword argument (at least one of those
        specified must be present for the transaction to be included).
      * a single tag string for the `tags` keyword argument. The transaction
        must contain the specified tag to be included.
      * a string for the `name` keyword argument.
      * a string for the `desc` keyword argument. This comparison is
        case-insensitive and will match on substring as well.
      * a date string of the form `%Y`, `%Y/%m`, or `%Y/%m/%d` for the `date`
        keyword argument.
      * a tuple of date strings, each of the form above. These are taken to
        constitute a range of dates. TODO implement this.
    '''
    filtered = []
    for t in transactions:
        if bank:
            if isinstance(bank, str):
                if bank.lower() != t['bank'].lower():
                    continue
            elif not bank(t['bank']):
                continue
        if account:
            if isinstance(account, str):
                if account.lower() != t['account'].lower():
                    continue
            elif not account(t['account']):
                continue
        if tags:
            if isinstance(tags, str):
                if not tags in t['tags']:
                    continue
            elif isinstance(tags, list):
                if not True in [(tag in t['tags']) for tag in tags]:
                    continue
            elif not tags(set(t['tags'])):
                continue
        if name:
            if isinstance(name, str):
                if t['name'] != name:
                    continue
            elif not name(t['name']):
                continue
        if desc:
            if isinstance(desc, str):
                if not desc.lower() in t['desc'].lower():
                    continue
            elif not desc(t['desc']):
                continue
        if amount and not amount(t['amount']):
            continue
        if date:
            if isinstance(date, str):
                sd = list(map(int, date.split('/')))
                if len(sd) >= 1 and t['date'].year != sd[0]:
                    continue
                if len(sd) >= 2 and t['date'].month != sd[1]:
                    continue
                if len(sd) >= 3 and t['date'].day != sd[2]:
                    continue
            elif not date(t['date']):
                continue
        filtered.append(copy.deepcopy(t))
    return filtered


def tmax(transactions):
    '''
    Computes the maximum of the amounts of the specified list of transactions.
    '''
    return max([t['amount'] for t in transactions])


def tmean(transactions):
    '''
    Computes the mean of the amounts of the specified list of transactions.
    '''
    return statistics.mean([t['amount'] for t in transactions])


def tmedian(transactions):
    '''
    Computes the median of the amounts of the specified list of transactions.
    '''
    return statistics.median([t['amount'] for t in transactions])


def tmerge(*args, reverse=False):
    '''
    Merges one or more transaction lists into a single one. The result is then
    sorted by transaction date.
    '''
    merged = []
    for t in args:
        merged.extend(copy.deepcopy(t))
    return sorted(merged, key = lambda x: x['date'], reverse=reverse)


def tmin(transactions):
    '''
    Computes the minimum of the amounts of the specified list of transactions.
    '''
    return min([t['amount'] for t in transactions])


def tprint(transaction, extended=False):
    '''
    Prints the specified transaction, but by default only the most useful
    information.
    '''
    if extended:
        print('Bank:        ' + transaction['bank'])
        print('Account:     ' + transaction['account'])
    if 'name' in transaction and transaction['name']:
        print('Name:        ' + transaction['name'])
        if extended:
            print('Description: ' + transaction['desc'])
    else:
        print('Description: ' + transaction['desc'])
    print('Date:        ' + transaction['date'].strftime('%Y/%m/%d'))
    print('Amount:      ' + dstr(transaction['amount']))
    print('Balance:     ' + dstr(transaction['bal']))
    print('Tags:        ' + str(transaction['tags']))


def tstdev(transactions):
    '''
    Computes the standard deviation of the amounts of the specified list of
    transactions.
    '''
    return statistics.stdev([t['amount'] for t in transactions])


def tsum(transactions):
    '''
    Computes the sum of the amounts of the specified list of transactions.
    '''
    return sum([t['amount'] for t in transactions])


def tuncat(transactions):
    '''
    Returns which transactions of the given list of transactions have yet to be
    categorized or which were not tagged when categorized.
    '''
    return [t for t in transactions if not t['tags']]
