'''
Contains the definition of a transaction CSV parser.
'''

import csv
import datetime
import glob
import io
import os
import re

from typing import Any, Optional

from .transaction import Transaction, Transactions

YEAR_FIRST_REGEX = re.compile(r'^\d{4}\/\d{1,2}\/\d{1,2}$')

class Parser:
    '''
    Parses various banking output formats into uncategorized transaction
    objects.
    '''
    def __init__(self):
        '''
        Creates a new instance of a transaction parser.
        '''

    @staticmethod
    def amount_from_str(dstr: str) -> float:
        '''
        Parses the specified dollar amount string into a usable float value.
        '''
        no_currency = dstr.replace('$', '')
        if '(' in dstr and ')' in dstr:
            return round(-1 * float(no_currency.replace('(', '').replace(')', '')), 2)
        else:
            return round(float(no_currency), 2)

    @staticmethod
    def amount_to_str(amount: float) -> str:
        '''
        Converts a monetary amount to its string representation.
        '''
        ra = abs(round(amount, 2))
        if amount < 0: return '-${0:.2f}'.format(ra)
        return '${0:.2f}'.format(ra)

    def parse_transaction_csv(self, path: str, account: Optional[str] = None, bank: Optional[str] = None) -> Transactions:
        '''
        Parses the specified CSV file (or directory of CSV files) into a
        collection of transactions. If `account` or `bank` are set to `None`,
        the function will infer these values based on the name of the CSV file.
        This is of the form `{bank}-{account}.csv`.
        '''
        full_path = os.path.expanduser(path)
        if os.path.isdir(full_path):
            paths = glob.glob(os.path.join(full_path, '*.csv'))
        elif os.path.isfile(full_path):
            paths = [full_path]
        else:
            raise Exception(f'specified path "{path}" does not exist')
        if not paths:
            raise Exception(f'specified path "{path}" does not contain CSV files')
        transaction_sets = []
        for p in paths:
            if account is None and bank is None:
                the_bank, the_account = os.path.basename(p).rsplit('.', 1)[0].split('-', 1)
            elif account is None and not bank is None:
                the_account = os.path.basename(p).rsplit('.', 1)[0]
                the_bank = bank
            elif not account is None and bank is None:
                the_account = account
                the_bank = os.path.basename(p).rsplit('.', 1)[0]
            else:
                the_account = account
                the_bank = bank
            try:
                with open(p, 'r') as f:
                    content = f.read()
            except Exception as e:
                raise Exception(f'unable to read CSV file "{p}" - {e}')
            try:
                transaction_sets.append(
                    self.parse_transaction_csv_content(the_account, the_bank, content)
                )
            except Exception as e:
                raise Exception(f'unable to parse CSV file {p} - {e}')
        return Transactions.merge(*transaction_sets)

    def parse_transaction_csv_content(self, account: str, bank: str, content: str) -> Transactions:
        '''
        A sister method of `parse_transaction_csv()`, this function parses the
        string content read from a single CSV file.
        '''
        try:
            csv_data = csv.DictReader(io.StringIO(content), restkey='misc')
        except Exception as e:
            raise Exception(f'unable to parse CSV content - {e}')
        transactions = []
        for entry in csv_data:
            amount_str  = next(entry[k] for k in entry.keys() if k.lower() in ['amt', 'amount'])
            balance_str = next(entry[k] for k in entry.keys() if k.lower() in ['bal', 'balance'])
            date_str    = next(entry[k] for k in entry.keys() if k.lower() == 'date')
            desc        = next(entry[k] for k in entry.keys() if k.lower() in ['desc', 'description'])
            if 'misc' in entry and entry['misc']:
                note = f'Additional CSV Data: {entry["misc"]}'
            else:
                note = None
            if YEAR_FIRST_REGEX.match(date_str):
                year_format = '%Y/%m/%d'
            else:
                year_format = '%m/%d/%Y'
            transactions.append(Transaction(
                account = account,
                amount  = Parser.amount_from_str(amount_str),
                balance = Parser.amount_from_str(balance_str),
                bank    = bank,
                date    = datetime.datetime.strptime(date_str, year_format).date(),
                desc    = desc,
                note    = note
            ))
        return Transactions(transactions)
