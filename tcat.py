#!/usr/bin/env python3
'''
tcat

Banking transaction categorization library for Python.
'''

import copy
import csv
import datetime
import glob
import json
import os
import plotly.figure_factory as ff
import plotly.graph_objects as go
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

    def categorize_transactions(self, transactions, macro=True, micro=True):
        '''
        Categorizes a list of transaction dictionaries. Also has the ability of
        categorizing any transaction with an absolute value <= $1 as a micro
        transaction and any >= $1000 as a macro transaction.
        '''
        cat = []
        for t in transactions:
            tc = copy.deepcopy(t)
            if cdesc := self.categorize(t['desc']):
                tc['name'] = cdesc['name']
                tc['tags'] = cdesc['tags']
            if macro and abs(t['amount']) >= 1000:
                if not 'name' in tc:
                    tc['name'] = 'Macrotransaction'
                tc['tags'].append('macro')
            if micro and abs(t['amount']) <= 1:
                if not 'name' in tc:
                    tc['name'] = 'Microtransaction'
                tc['tags'].append('micro')
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

    Additionally, a directory may instead be provided, in which all `.csv`
    files within it will be parsed and then merged.

    The resulting transactions are not automatically categorized.
    '''
    cf = os.path.expanduser(csv_file)
    if os.path.isdir(cf):
        csv_files = glob.glob(os.path.join(cf, '*.csv'))
        if not csv_files:
            raise Exception('specified csv directory does not contain any data files')
        return tmerge(*[parse_csv(f) for f in csv_files])
    if not os.path.isfile(cf):
        raise Exception('specified csv file does not exist')
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
    elif the_bank.lower() == 'eglin':
        for d in init_parse:
            parsed.append({
                'account': the_account,
                'amount': float(d['Amount']),
                'bal': float(d['Balance']),
                'bank': the_bank,
                'date': datetime.datetime.strptime(d['Date'], '%m/%d/%Y'),
                'desc': d['Description'],
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


def texport(transactions, file_path):
    '''
    Exports the specified list of transactions to the specified file path.
    '''
    exportform = copy.deepcopy(transactions)
    for t in exportform:
        t['date'] = t['date'].strftime('%Y/%m/%d')
    with open(os.path.expanduser(file_path), 'w') as f:
        json.dump(exportform, f)


def tfilter(transactions, account=None, amount=None, bank=None, date=None, desc=None, name=None, negate=False, notes=None, tags=None):
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
    most_recent_date = max([t['date'] for t in transactions])
    filtered = []
    for t in transactions:
        if bank:
            if isinstance(bank, str):
                if negate:
                    if bank.lower() == t['bank'].lower():
                        continue
                else:
                    if bank.lower() != t['bank'].lower():
                        continue
            else:
                if negate:
                    if bank(t['bank']):
                        continue
                else:
                    if not bank(t['bank']):
                        continue
        if account:
            if isinstance(account, str):
                if negate:
                    if account.lower() == t['account'].lower():
                        continue
                else:
                    if account.lower() != t['account'].lower():
                        continue
            else:
                if negate:
                    if account(t['account']):
                        continue
                else:
                    if not account(t['account']):
                        continue
        if tags:
            if isinstance(tags, str):
                if negate:
                    if tags in t['tags']:
                        continue
                else:
                    if not tags in t['tags']:
                        continue
            elif isinstance(tags, list):
                if negate:
                    if (True in [(tag in t['tags']) for tag in tags]):
                        continue
                else:
                    if not (True in [(tag in t['tags']) for tag in tags]):
                        continue
            else:
                if negate:
                    if tags(set(t['tags'])):
                        continue
                else:
                    if not tags(set(t['tags'])):
                        continue
        if name:
            if not 'name' in t:
                if not negate: continue
            if isinstance(name, str):
                if negate:
                    if name.lower() in t['name'].lower():
                        continue
                else:
                    if not name.lower() in t['name'].lower():
                        continue
            else:
                if negate:
                    if name(t['name']):
                        continue
                else:
                    if not name(t['name']):
                        continue
        if desc:
            if isinstance(desc, str):
                if negate:
                    if desc.lower() in t['desc'].lower():
                        continue
                else:
                    if not desc.lower() in t['desc'].lower():
                        continue
            else:
                if negate:
                    if desc(t['desc']):
                        continue
                else:
                    if not desc(t['desc']):
                        continue
        if notes:
            if not 'notes' in t:
                if not negate: continue
            if isinstance(notes, str):
                if negate:
                    if notes.lower() in t['notes'].lower():
                        continue
                else:
                    if not notes.lower() in t['notes'].lower():
                        continue
            else:
                if negate:
                    if notes(t['notes']):
                        continue
                else:
                    if not notes(t['notes']):
                        continue
        if amount:
            if isinstance(amount, str):
                if amount.lower() in ['+', 'd', 'deposit']:
                    if negate:
                        if t['amount'] > 0:
                            continue
                    else:
                        if t['amount'] <= 0:
                            continue
                if amount.lower() in ['-', 'w', 'withdawal']:
                    if negate:
                        if t['amount'] < 0:
                            continue
                    else:
                        if t['amount'] >= 0:
                            continue
            if isinstance(amount, tuple):
                if negate:
                    if t['amount'] >= amount[0] and t['amount'] <= amount[1]:
                        continue
                else:
                    if t['amount'] < amount[0] or t['amount'] > amount[1]:
                        continue
            else:
                if negate:
                    if amount(t['amount']):
                        continue
                else:
                    if not amount(t['amount']):
                        continue
        if date:
            if isinstance(date, int):
                if negate:
                    if (most_recent_date - t['date']).days <= date:
                        continue
                else:
                    if (most_recent_date - t['date']).days > date:
                        continue
            elif isinstance(date, str):
                sd = list(map(int, date.split('/')))
                if negate:
                    if len(sd) >= 1 and t['date'].year == sd[0]:
                        continue
                    if len(sd) >= 2 and t['date'].month == sd[1]:
                        continue
                    if len(sd) >= 3 and t['date'].day == sd[2]:
                        continue
                else:
                    if len(sd) >= 1 and t['date'].year != sd[0]:
                        continue
                    if len(sd) >= 2 and t['date'].month != sd[1]:
                        continue
                    if len(sd) >= 3 and t['date'].day != sd[2]:
                        continue
            elif isinstance(date, tuple):
                sd1 = list(map(int, date[0].split('/')))
                while len(sd1) < 3: sd1.append(1)
                sd2 = list(map(int, date[1].split('/')))
                while len(sd2) < 3: sd2.append(1)
                lowerbound = datetime.datetime(*sd1)
                upperbound = datetime.datetime(*sd2)
                if negate:
                    if t['date'] >= lowerbound and t['date'] <= upperbound:
                        continue
                else:
                    if t['date'] < lowerbound or t['date'] > upperbound:
                        continue
            else:
                if negate:
                    if date(t['date']):
                        continue
                else:
                    if not date(t['date']):
                        continue
        filtered.append(copy.deepcopy(t))
    return filtered


def tgroup(transactions, by='date-weekly'):
    '''
    Groups the specified list of transactions according to a quantifier.
    '''
    if 'date' in by:
        sortedt = tsort(transactions, reverse=True)
    elif by == 'tags':
        sortedt = copy.deepcopy(transactions)
        for t in sortedt:
            t['tags'] = sorted(t['tags'])
        sortedt = tsort(sortedt, key='tags')
    groups = [[]]
    gi = 0
    for i, t in enumerate(sortedt):
        if i == 0:
            groups[0].append(sortedt[0])
            continue
        prev = sortedt[i - 1]
        if by == 'date-daily':
            if t['date'] == prev['date']:
                groups[gi].append(sortedt[i])
                continue
        elif by == 'date-weekly':
            if t['date'].isocalendar()[1] == prev['date'].isocalendar()[1]:
                groups[gi].append(sortedt[i])
                continue
        elif by == 'date-monthly':
            if t['date'].year == prev['date'].year and t['date'].month == prev['date'].month:
                groups[gi].append(sortedt[i])
                continue
        elif by == 'date-yearly':
            if t['date'].year == prev['date'].year:
                groups[gi].append(sortedt[i])
                continue
        elif by == 'tags':
            if t['tags'] == prev['tags']:
                groups[gi].append(sortedt[i])
                continue
        groups.append([sortedt[i]])
        gi += 1
    return groups


def timport(file_path):
    '''
    Imports pre-parsed transaction data from the specified file path.
    '''
    with open(os.path.expanduser(file_path), 'r') as f:
        exportform = json.load(f)
    importform = copy.deepcopy(exportform)
    for t in importform:
        t['date'] = datetime.datetime.strptime(t['date'], '%Y/%m/%d')
    return importform


def tmax(transactions):
    '''
    Computes the maximum of the amounts of the specified list of transactions.
    '''
    return max([t['amount'] for t in transactions])


def tmean(transactions):
    '''
    Computes the mean of the amounts of the specified list of transactions.
    '''
    return round(statistics.mean([t['amount'] for t in transactions]), 2)


def tmedian(transactions):
    '''
    Computes the median of the amounts of the specified list of transactions.
    '''
    return round(statistics.median([t['amount'] for t in transactions]), 2)


def tmerge(*args, reverse=False):
    '''
    Merges one or more transaction lists into a single one. The result is then
    sorted by transaction date with the most recent entries at the beginning of
    the list by default. The merging process will automatically delete duplicate
    entries, but preferres the last arguments to have preferrence.
    '''
    merged = []
    for ts in args:
        for t in ts:
            ct = copy.deepcopy(t)
            if not merged:
                merged.append(ct)
            else:
                duplicate_index = -1
                for i, m in enumerate(merged):
                    if ct['date'] != m['date']:
                        continue
                    if ct['bank'] != m['bank']:
                        continue
                    if ct['account'] != m['account']:
                        continue
                    if ct['desc'] != m['desc']:
                        continue
                    if ct['amount'] != m['amount']:
                        continue
                    if ct['bal'] != m['bal']:
                        continue
                    duplicate_index = i
                    break
                if duplicate_index == -1:
                    merged.append(ct)
                else:
                    dedup = copy.deepcopy(merged[duplicate_index])
                    if (not 'name' in dedup or not dedup['name']) and ('name' in ct):
                        dedup['name'] = ct['name']
                    elif 'name' in dedup and ('name' in ct and ct['name']):
                        dedup['name'] = ct['name']
                    if (not 'notes' in dedup or not dedup['notes']) and ('notes' in ct):
                        dedup['notes'] = ct['notes']
                    elif 'notes' in dedup and ('notes' in ct and ct['notes']):
                        dedup['notes'] = ct['notes']
                    if (not 'tags' in dedup or not dedup['tags']) and ('tags' in ct):
                        dedup['tags'] = ct['tags']
                    elif 'tags' in dedup and ('tags' in ct and ct['tags']):
                        dedup['tags'] = ct['tags']
                    merged[duplicate_index] = dedup
    return tsort(merged, reverse=reverse)


def tmin(transactions):
    '''
    Computes the minimum of the amounts of the specified list of transactions.
    '''
    return min([t['amount'] for t in transactions])


def tplot(transactions, absval=False, key='bal', rolling=0, slider=False, smooth=False, statistic='median', style='lines+markers', title=None):
    '''
    Produces a graphical plot of the specified list of transactions. By default,
    this function will produce a line plot of the balance over time. Each
    bank+account combination will be given its own line.
    '''
    fig = go.Figure()
    if statistic == 'mean':
        statfunc = statistics.mean
    elif statistic == 'median':
        statfunc = statistics.median
    elif statistic == 'stdev':
        statfunc = statistics.stdev
    elif statistic == 'total' or statistic == 'sum':
        statfunc = sum
    banks = set([t['bank'] for t in transactions])
    for bank in banks:
        bt = tfilter(transactions, bank=bank)
        accounts = set([t['account'] for t in bt])
        for account in accounts:
            at = tfilter(bt, account=account)
            if len(banks) == 1 and len(accounts) == 1:
                tname = None
            elif len(banks) == 1 and len(accounts) > 1:
                tname = account
            else:
                tname = '{b} ({a})'.format(b=bank, a=account)
            dates = sorted(list(set([t['date'] for t in at])))
            balances = []
            hovertext = []
            for date in dates:
                ht = []
                ts = [t for t in at if (date - t['date']).days >= 0 and (date - t['date']).days <= rolling]
                for t in ts:
                    namestr = t['name'] if 'name' in t else t['desc']
                    valstr = dstr(t['amount'])
                    ht.append(namestr + ' (' + valstr + ')')
                val = statfunc([t[key] for t in ts])
                balances.append(abs(val) if absval else val)
                hovertext.append(' | '.join(ht))
            fig.add_trace(go.Scatter(
                x = dates,
                y = balances,
                hovertext = hovertext,
                line_shape='spline' if smooth else 'linear',
                mode = style,
                name = tname,
            ))
    if key == 'amount':
        yt = 'Transaction Amount ($)'
    elif key == 'bal':
        yt = 'Account Balance ($)'
    if statistic == 'mean':
        yt = 'Mean ' + yt
    elif statistic == 'median':
        yt = 'Median ' + yt
    elif statistic == 'stdev':
        yt = 'Standard Deviation of ' + yt
    elif statistic in ['sum', 'total']:
        yt = 'Total ' + yt
    if rolling:
        yt = 'Rolling ' + yt
    fig.update_layout(
        title = title,
        xaxis_rangeslider_visible = slider,
        xaxis_title = 'Date',
        yaxis_title = yt
    )
    return fig


def tplot_candle(transactions, absval=False, dt='day', key='bal', log=False, statistic='median', title=None):
    '''
    Produces a candlestick plot of the specified list of transactions.
    '''
    if statistic == 'median':
        statfunc = statistics.median
    else:
        statfunc = statistics.mean
    fig = go.Figure()
    dopen = []
    dhigh = []
    dlow = []
    dclose = []
    dates = sorted(list(set([t['date'] for t in transactions])))
    for d in dates:
        data = [t[key] for t in transactions if t['date'] == d]
        if absval:
            data = list(map(abs, data))
        dhigh.append(max(data))
        dlow.append(min(data))
        if len(data) == 1:
            dopen.append(data[0])
            dclose.append(data[0])
        elif len(data) == 2:
            dopen.append(max(data))
            dclose.append(min(data))
        else:
            data_avg = statfunc(data)
            data_stdev = statistics.stdev(data)
            dopen.append(data_avg + (data_stdev / 2))
            dclose.append(data_avg - (data_stdev / 2))
    fig.add_trace(go.Candlestick(
        x = dates,
        high = dhigh,
        open = dopen,
        close = dclose,
        low = dlow
    ))
    if key == 'amount':
        yt = 'Transaction Amount ($)'
    elif key == 'bal':
        yt = 'Account Balance ($)'
    fig.update_layout(
        title = title,
        xaxis_title = 'Date',
        yaxis_title = yt,
        yaxis_type = 'log' if log else 'linear'
    )
    return fig


def tplot_sratio(transactions, style='lines+markers', title='Spending Ratio'):
    '''
    Plots the overall spending ratio over time.
    '''
    fig = go.Figure()
    banks = set([t['bank'] for t in transactions])
    for bank in banks:
        bt = tfilter(transactions, bank=bank)
        accounts = set([t['account'] for t in bt])
        for account in accounts:
            at = tfilter(bt, account=account)
            if len(banks) == 1 and len(accounts) == 1:
                tname = None
            elif len(banks) == 1 and len(accounts) > 1:
                tname = account
            else:
                tname = '{b} ({a})'.format(b=bank, a=account)
            dates = sorted(list(set([t['date'] for t in at])))
            balances = []
            filtered_dates = []
            hovertext = []
            for date in dates:
                ht = []
                ts = [t for t in at if t['date'] == date]
                for t in ts:
                    namestr = t['name'] if 'name' in t else t['desc']
                    valstr = dstr(t['amount'])
                    ht.append(namestr + ' (' + valstr + ')')
                trans = [t['amount'] for t in at if t['date'] <= date]
                pos = [a for a in trans if a >= 0]
                neg = [a for a in trans if a < 0]
                if pos and neg:
                    filtered_dates.append(date)
                    balances.append(sum(pos) / abs(sum(neg)))
                    hovertext.append(' | '.join(ht))
            fig.add_trace(go.Scatter(
                x = filtered_dates,
                y = balances,
                hovertext = hovertext,
                mode = style,
                name = tname,
            ))
    fig.update_layout(
        title = title,
        xaxis_title = 'Date',
        yaxis_title = 'Rolling Transaction Spending Ratio',
        yaxis_type = 'log'
    )
    return fig


def tplot_tagbar(transactions, hide=['macro', 'micro'], log=False, ftags=None, statistic='median', thres=1000, title='Transaction Amounts by Tag'):
    '''
    Plots a series of bar charts grouped by tag.
    '''
    if statistic == 'mean':
        statfunc = statistics.mean
    elif statistic == 'median':
        statfunc = statistics.median
    elif statistic == 'stdev':
        statfunc = statistics.stdev
    elif statistic == 'total' or statistic == 'sum':
        statfunc = sum
    fig = go.Figure()
    all_tags = tags(transactions)
    filtered_tags = []
    all_values = []
    others = []
    for tag in all_tags:
        if hide and tag in hide:
            continue
        if ftags and not tag in ftags:
            continue
        ts = tfilter(transactions, tags=tag)
        ts_total = sum([abs(t['amount']) for t in ts])
        if ts_total < thres:
            others = tmerge(others, ts)
        else:
            filtered_tags.append(tag)
            if statistic == 'total' or statistic == 'sum':
                all_values.append(ts_total)
            else:
                all_values.append(statfunc([abs(t['amount']) for t in ts]))
    if others:
        filtered_tags.append('(other)')
        all_values.append(statfunc([abs(t['amount']) for t in others]))
    fig.add_trace(go.Bar(
        x = filtered_tags,
        y = all_values,
    ))
    yt = 'Transaction Amount ($)'
    if statistic == 'mean':
        yt = 'Mean ' + yt
    elif statistic == 'median':
        yt = 'Median ' + yt
    elif statistic == 'stdev':
        yt = 'Standard Deviation of ' + yt
    elif statistic in ['sum', 'total']:
        yt = 'Total ' + yt
    fig.update_layout(
        title = title,
        xaxis_tickangle = -45,
        xaxis_title = 'Tag',
        yaxis_title = yt,
        yaxis_type = 'log' if log else 'linear'
    )
    return fig


def tplot_tagdist(transactions, absval=False, bin_size=2, ftags=None, log=False, title='Transaction Tag Amount Distribution'):
    '''
    Plots the amount distribution of each tag in the specified list of
    transactions.
    '''
    hist_data = []
    all_tags = tags(transactions)
    filtered_tags= []
    for tag in all_tags:
        if ftags and not tag in ftags:
            continue
        with_tag = [t['amount'] for t in tfilter(transactions, tags=tag)]
        if absval:
            with_tag = list(map(abs, with_tag))
        if len(with_tag) > 1:
            filtered_tags.append(tag)
            hist_data.append(with_tag)
    fig = ff.create_distplot(
        hist_data,
        filtered_tags,
        bin_size = bin_size,
        curve_type = 'normal'
    )
    fig.update_layout(
        title = title,
        xaxis_title = 'Transaction Amount ($)',
        xaxis_type = 'log' if log else 'linear',
        yaxis_title = 'Proportion'
    )
    return fig


def tplot_tagpie(transactions, ftags=None, statistic='total', title=None):
    '''
    Creates a pie chart of the tags associated with the specified list of
    transactions.
    '''
    if statistic == 'mean':
        statfunc = statistics.mean
    elif statistic == 'median':
        statfunc = statistics.median
    elif statistic == 'stdev':
        statfunc = statistics.stdev
    elif statistic in ['sum', 'total']:
        statfunc = sum
    all_tags = tags(transactions)
    filtered_tags = []
    pie_data = []
    for tag in all_tags:
        if ftags and not tag in ftags:
            continue
        with_tag = [abs(t['amount']) for t in tfilter(transactions, tags=tag)]
        filtered_tags.append(tag)
        pie_data.append(statfunc(with_tag))
    fig = go.Figure(data=[go.Pie(
        labels = filtered_tags,
        values = pie_data
    )])
    fig.update_layout(title=title)
    return fig


def tprint(transaction, extended=False):
    '''
    Prints the specified transaction, but by default only the most useful
    information.

    In addition, if a list of transactions is specified, then they are printed
    with one transaction per line.
    '''
    if isinstance(transaction, list):
        max_account = max(map(len, [t['account'] for t in transaction]))
        max_amount = max(map(len, [dstr(t['amount']) for t in transaction]))
        max_bal = max(map(len, [dstr(t['bal']) for t in transaction]))
        max_bank = max(map(len, [t['bank'] for t in transaction]))
        max_desc = max(map(len, [t['desc'] for t in transaction]))
        has_names = ['name' in t for t in transaction]
        has_notes = ['notes' in t for t in transaction]
        if True in has_names:
            max_name = max(map(len, [t['name'] for t in transaction if 'name' in t]))
        else:
            max_name = 0
        if True in has_notes:
            max_notes = max(map(len, [t['notes'] for t in transaction if 'notes' in t]))
        else:
            max_notes = 0
        if not False in has_names:
            max_namedesc = max_name
        elif max_name >= max_desc:
            max_namedesc = max_name
        else:
            max_namedesc = max_desc
        header_line = 'DATE        '
        if extended:
            header_line += 'BANK' + (' ' * (max_bank - 4)) + '  '
            header_line += 'ACCOUNT' + (' ' * (max_account - 7)) + '  '
        if max_namedesc < 16:
            header_line += 'NAME/DESC' + (' ' * (max_namedesc - 9)) + '  '
        else:
            header_line += 'NAME/DESCRIPTION' + (' ' * (max_namedesc - 16)) + '  '
        if extended:
            if max_notes:
                header_line += 'NOTES' + (' ' * (max_notes - 5)) + '  '
            else:
                header_line += 'NOTES  '
        if max_amount < 6:
            header_line += 'AMT' + (' ' * (max_amount - 3)) + '  '
        else:
            header_line += 'AMOUNT' + (' ' * (max_amount - 6)) + '  '
        if extended:
            if max_bal < 7:
                header_line += 'BAL' + (' ' * (max_bal - 3)) + '  '
            else:
                header_line += 'BALANCE' + (' ' * (max_bal - 7)) + '  '
        print(header_line)
        print('-' * len(header_line))
        for t in transaction:
            pamount = dstr(t['amount'])
            pname = t['name'] if 'name' in t else t['desc']
            pnotes = t['notes'] if 'notes' in t else 'N/A'
            if max_notes:
                notespad = (' ' * (max_notes - pnotes))
            else:
                notespad = '  '
            if extended:
                pt = '{date}  {bank}  {account}  {name}  {notes}  {amount}  {bal}'.format(
                    date = t['date'].strftime('%Y/%m/%d'),
                    bank = t['bank'] + (' ' * (max_bank - len(t['bank']))),
                    account = t['account'] + (' ' * (max_account - len(t['account']))),
                    name = pname + (' ' * (max_namedesc - len(pname))),
                    notes = pnotes + notespad,
                    amount = pamount + (' ' * (max_amount - len(pamount))),
                    bal = dstr(t['bal'])
                )
            else:
                pt = '{date}  {name}  {amount}'.format(
                    date = t['date'].strftime('%Y/%m/%d'),
                    name = pname + (' ' * (max_namedesc - len(pname))),
                    amount = pamount + (' ' * (max_amount - len(pamount)))
                )
            print(pt)
        return
    if extended:
        print('Bank:        ' + transaction['bank'])
        print('Account:     ' + transaction['account'])
    if 'name' in transaction and transaction['name']:
        print('Name:        ' + transaction['name'])
        if extended:
            print('Description: ' + transaction['desc'])
    else:
        print('Description: ' + transaction['desc'])
    if extended and 'notes' in transaction and transaction['notes']:
        print('Notes:       ' + transaction['notes'])
    print('Date:        ' + transaction['date'].strftime('%Y/%m/%d'))
    print('Amount:      ' + dstr(transaction['amount']))
    print('Balance:     ' + dstr(transaction['bal']))
    print('Tags:        ' + str(transaction['tags']))


def tsort(transactions, key='date', reverse=False):
    '''
    Sorts the specified list of transactions according to a certain "key",
    optionally reversing the default sort order.

    The `key` parameter may be specified as:
      * A function/lambda on each transaction option.
      * A string corresponding to the name of a key within each transaction (for
        example: `date`).

    Note that when sorting by the `date` key, the most recent dates will be
    moved to the beginning of the list.
    '''
    if isinstance(key, str):
        if key == 'date':
            return sorted(transactions, key = lambda x: x['date'], reverse = not reverse)
        else:
            return sorted(transactions, key = lambda x: x[key], reverse = reverse)
    else:
        return sorted(transactions, key=key, reverse=reverse)


def tstdev(transactions):
    '''
    Computes the standard deviation of the amounts of the specified list of
    transactions.
    '''
    return round(statistics.stdev([t['amount'] for t in transactions]), 2)


def tsum(transactions):
    '''
    Computes the sum of the amounts of the specified list of transactions.
    '''
    return round(sum([t['amount'] for t in transactions]), 2)


def tuncat(transactions):
    '''
    Returns which transactions of the given list of transactions have yet to be
    categorized or which were not tagged when categorized.
    '''
    return [t for t in transactions if not t['tags']]
