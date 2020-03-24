#!/usr/bin/env python3
'''
tcat

Banking transaction categorization library for Python.
'''

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
        parsed_data_files = []
        for data_file in data_files:
            try:
                with open(data_file, 'r') as f:
                    parsed_data_files.append(yaml.safe_load(f.read()))
            except Exception as e:
                raise Exception(
                    'unable to parse data file "{d}" - {e}'.format(
                        d = data_file,
                        e = str(e)
                    )
                )
        self.data = []
        for pdata in parsed_data_files:
            if not 'data' in pdata:
                raise Exception(
                    'one or more parsed data files does not have a "data" key'
                )
            rendered_pdata = pdata.copy()
            for i, d in enumerate(pdata['data']):
                if not 'name' in d or not 'match' in d:
                    raise Exception(
                        'one or more parsed data files has invalid data'
                    )
                rendered_pdata['data'][i]['match'] = re.compile(d['match'])
            self.data.append(rendered_pdata)

    def categorize(self, desc):
        '''
        Categorizes a transaction description, returning a "pretty" name for the
        transaction, as well as a collection of tags to assign the transaction.
        '''
        cat = {}
        ldesc = desc.lower()
        found = False
        for d1 in self.data:
            for d2 in d1['data']:
                if d2['match'].search(ldesc):
                    cat['name'] = d2['name']
                    if 'tags' in d1:
                        cat['tags'] = d1['tags']
                    if 'tags' in d2:
                        cat['tags'].extend(d2['tags'])
                    found = True
                    break
            if found: break
        return cat

    def categorize_transactions(self, transactions):
        '''
        Categorizes a list of transaction dictionaries.
        '''
        cat = []
        for t in transactions:
            if cdesc := self.catagorize(t['desc']):
                tc = t.copy()
                tc['name'] = cdesc['name']
                tc['tags'] = cdesc['tags']
                cat.append(tc)
        return cat


def dstr(amount):
    '''
    Converts a monetary amount to a string.
    '''
    ra = abs(round(amount, 2))
    if amount < 0: return '-${0:.2f}'.format(ra)
    return '${0:.2f}'.format(ra)


def tfilter(transactions, amount=None, date=None, desc=None, name=None, tags=None):
    '''
    Filters a collection of transaction according to:
      * A function filtering by tags (as a set)
      * A function filtering by name
      * A function filtering by description
      * A function filtering by dollar amount
      * A function filtering by date
      * Some combination of the above (applied in that order)
    '''
    filtered = []
    for t in transactions:
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
        filtered.append(t)
    return filtered


def tprint(transaction):
    '''
    Prints the specified transaction.
    '''
    if 'name' in transaction:
        print('Name:        ' + transaction['name'])
    print('Description: ' + transaction['desc'])
    print('Date:        ' + transaction['date'].strftime('%Y/%m/%d'))
    print('Amount:      ' + dstr(transaction['amount']))
    print('Balance:     ' + dstr(transaction['bal']))
    print('Tags:        ' + str(transaction['tags']))
