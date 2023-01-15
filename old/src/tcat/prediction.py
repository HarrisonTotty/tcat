'''
Contains definitions useful for the prediction of financial trends.
'''

from __future__ import annotations

import dateutil.relativedelta
import math
import numpy
import statistics

from typing import Optional

from .transaction import Transaction, Transactions


class Simulator:
    '''
    Simulates the continuation of balance trends from a given collection of
    transactions.
    '''

    data: dict[str, dict]

    def __init__(self, transactions: Transactions):
        '''
        Creates a new `Simulator` object with properties derived from the
        specified collection of transactions. The data contained within this
        object is of the form:
        {bank}:
          {account}:
            dstats: {deposit statistics}
            wstats: {withdrawal statistics}
            zero_balance: {last balance day before simulation starting date}
            zero_date: {day before simulation starting date}
        '''
        self.data = {}
        for (bank, account), ts in transactions.group(by='bank-account').items():
            if len(ts) < 2:
                raise Exception(f'the simulator must be provided at least 2 transactions for bank "{bank}", account "{account}"')
            deposits    = ts.filter(amount='+')
            withdrawals = ts.filter(amount='-')
            if not bank in self.data:
                self.data[bank] = { account: {
                    'dstats': deposits.statistics(),
                    'wstats': withdrawals.statistics(),
                    'zero_balance': ts.filter(date=ts[-1].date).mean_balance(),
                    'zero_date': ts[-1].date

                } }
            else:
                self.data[bank][account] = {
                    'dstats': deposits.statistics(),
                    'wstats': withdrawals.statistics(),
                    'zero_balance': ts.filter(date=ts[-1].date).mean_balance(),
                    'zero_date': ts[-1].date
                }

    def multi_run(self, n: int, days: int) -> Transactions:
        '''
        Executes `n` simulator runs each with the specified number of days.
        '''
        res = []
        for i in range(n):
            res.extend(self.run(days, account_suffix = f' - Prediction {i + 1}').items)
        return Transactions(res).sort()

    def run(self, days: int, account_suffix: str = ' - Prediction', max_per_day: Optional[int] = None) -> Transactions:
        '''
        Runs the simulator for the specified number of days, returning the
        collection of simulated transactions. Each simulated transaction will
        have the `simulated` tag added to it. This method supports the following
        arguments:
        * account_suffix
          Specifies a suffix to append to the account, allowing it to be treated
          as a separate account.
        * max_per_day
          Specifies the maximum number of simulated transactions allowed per
          bank-account pair per deposit or withdrawal per day. If set to None,
          this value will be taken to be the mean daily frequency plus two
          standard deviations.
        '''
        generated = {}
        for day in range(days):
            for bank, bank_data in self.data.items():
                if not bank in generated: generated[bank] = {}
                for account, account_data in bank_data.items():
                    # Setup
                    if not account in generated[bank]: generated[bank][account] = []
                    current_date = account_data['zero_date'] + dateutil.relativedelta.relativedelta(days = day + 1)
                    if max_per_day is None:
                        if account_data['dstats']['count'] > 0:
                            dmax = math.ceil(
                                account_data['dstats']['mean_freq_daily'] + (2.0 * account_data['dstats']['stdev_freq_daily'])
                            )
                        if account_data['wstats']['count'] > 0:
                            wmax = math.ceil(
                                account_data['wstats']['mean_freq_daily'] + (2.0 * account_data['wstats']['stdev_freq_daily'])
                            )
                    else:
                        dmax = max_per_day
                        wmax = max_per_day
                    if len(generated[bank][account]) > 1:
                        current_balance = generated[bank][account][-1].balance
                    else:
                        current_balance = account_data['zero_balance']
                    # Deposits
                    if account_data['dstats']['count'] > 0:
                        number_of_deposits = round(numpy.random.normal(
                            loc = account_data['dstats']['mean_freq_daily'],
                            scale = account_data['dstats']['stdev_freq_daily']
                        ))
                        if number_of_deposits < 0: number_of_deposits = 0
                        if number_of_deposits > dmax: number_of_deposits = dmax
                        for i in range(number_of_deposits):
                            amount = -1.0
                            while amount < 0:
                                amount = round(numpy.random.normal(
                                    loc = account_data['dstats']['mean_amount'],
                                    scale = account_data['dstats']['stdev_amount']
                                ), 2)
                            current_balance += amount
                            generated[bank][account].append(Transaction(
                                account = account + account_suffix,
                                amount = amount,
                                balance = current_balance,
                                bank = bank,
                                date = current_date,
                                desc = f'SIMULATED DEPOSIT [{bank}/{account}] {day}-{i}',
                                name = 'Simulated Deposit',
                                tags = ['simulated']
                            ))
                    # Withdrawals
                    if account_data['wstats']['count'] > 0:
                        number_of_withdrawals = round(numpy.random.normal(
                            loc = account_data['wstats']['mean_freq_daily'],
                            scale = account_data['wstats']['stdev_freq_daily']
                        ))
                        if number_of_withdrawals < 0: number_of_withdrawals = 0
                        if number_of_withdrawals > wmax: number_of_withdrawals = wmax
                        for i in range(number_of_withdrawals):
                            amount = 1.0
                            while amount > 0:
                                amount = round(numpy.random.normal(
                                    loc = account_data['wstats']['mean_amount'],
                                    scale = account_data['wstats']['stdev_amount']
                                ), 2)
                            current_balance += amount
                            generated[bank][account].append(Transaction(
                                account = account + account_suffix,
                                amount = amount,
                                balance = current_balance,
                                bank = bank,
                                date = current_date,
                                desc = f'SIMULATED WITHDRAWAL [{bank}/{account}] {day}-{i}',
                                name = 'Simulated Withdrawal',
                                tags = ['simulated']
                            ))
        res = []
        for gbank, gbank_data in generated.items():
            for gaccount, gaccount_data in gbank_data.items():
                res.extend(gaccount_data)
        return Transactions(res).sort()
