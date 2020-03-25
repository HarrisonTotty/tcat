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
    '''
    filtered = []
    for t in transactions:
        if bank and not bank(t['bank']):
            continue
        if account and not account(t['account']):
            continue
        if tags and not tags(set(t['tags'])):
            continue
        if name and not name(t['name']):
            continue
        if desc and not desc(t['desc']):
            continue
        if amount and not amount(t['amount']):
            continue
        if date and not date(t['date']):
            continue
        filtered.append(copy.deepcopy(t))
    return filtered


def tmerge(*args, reverse=False):
    '''
    Merges one or more transaction lists into a single one. The result is then
    sorted by transaction date.
    '''
    merged = []
    for t in args:
        merged.extend(copy.deepcopy(t))
    return sorted(merged, key = lambda x: x['date'], reverse=reverse)


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


def tuncat(transactions):
    '''
    Returns which transactions of the given list of transactions have yet to be
    categorized or which were not tagged when categorized.
    '''
    return [t for t in transactions if not t['tags']]
