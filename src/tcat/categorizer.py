'''
Contains the definition of the `Categorizer` class and any helpful utility
functions.
'''

from __future__ import annotations

import copy
import csv
import glob
import os
import re
import yaml

from typing import Any, Optional, Union

from .transaction import Transaction, Transactions

class Categorizer:
    '''
    Represents a banking transaction categorizer.
    '''
    def __init__(self, data_path: Optional[str] = None, data_content: Optional[list[dict]] = None):
        '''
        Creates a new transaction categorizer built from the specified data
        file or directory. Optionally, raw dictionary data may be fed to the
        categorizer by specifying a value for `data_content` instead.
        '''
        if not data_path is None:
            full_data_path = os.path.expanduser(data_path)
            if os.path.isdir(full_data_path):
                data_files = glob.glob(os.path.join(full_data_path, '*.yaml'))
            elif os.path.isfile(full_data_path):
                data_files = [full_data_path]
            else:
                raise Exception(f'specified data path "{data_path}" does not exist')
            if not data_files:
                raise Exception(f'specified data path "{data_path}" does not contain any data files')
            self.raw_data = []
            for df in data_files:
                try:
                    with open(df, 'r') as f:
                        self.raw_data.append(yaml.safe_load(f.read()))
                except Exception as e:
                    raise Exception(f'unable to parse data file "{df}" - {e}')
        elif not data_content is None:
            self.raw_data = copy.deepcopy(data_content)
        else:
            raise Exception('please specify either `data_path` or `data_content`')
        self.data = []
        for pdata in self.raw_data:
            if not 'data' in pdata:
                raise Exception('one or more data files doesn\'t specify the "data" key')
            rendered = copy.deepcopy(pdata)
            for i, d in enumerate(pdata['data']):
                if not 'name' in d or not 'match' in d:
                    raise Exception('you need to specify "name" and "match"')
                rendered['data'][i]['match'] = re.compile(d['match'].strip())
            self.data.append(rendered)

    def cat(
        self,
        arg: Union[Transaction, Transactions],
        merge: bool = True,
        tags: list[str] = []) -> Union[Transaction, Transactions]:
        '''
        Categorizes a transaction or collection of transactions, returning
        a categorized version of the input. If `merge` is set to `False`, any
        previously existing tags will be discarded instead of merged into the
        new list of tags. Additional tags defined by the `tags` argument will
        be added to all transactions.
        '''
        if isinstance(arg, Transaction):
            cp = copy.deepcopy(arg)
            desc = cp.desc.lower()
            for d1 in self.data:
                for d2 in d1['data']:
                    if d2['match'].search(desc):
                        ntags = cp.tags if merge else []
                        if tags: ntags.extend(tags)
                        if 'tags' in d1: ntags.extend(d1['tags'])
                        if 'tags' in d2: ntags.extend(d2['tags'])
                        return Transaction(
                            account = cp.account,
                            amount  = cp.amount,
                            balance = cp.balance,
                            bank    = cp.bank,
                            date    = cp.date,
                            desc    = cp.desc,
                            name    = d2['name'],
                            note    = cp.note,
                            tags    = list(set(ntags))
                        )
            return cp
        elif isinstance(arg, Transactions):
            return Transactions([self.cat(t, merge=merge) for t in arg.items])
        else:
            raise Exception('unsupported input type')
