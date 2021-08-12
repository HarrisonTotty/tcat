'''
Contains definitions associated with plotting transactions.
'''

import copy
import datetime
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
import statistics

from typing import Any, Optional

from .transaction import Transaction, Transactions


STATFUNC = {
    'max': max,
    'mean': statistics.mean,
    'median': statistics.median,
    'min': min,
    'stdev': statistics.stdev,
    'sum': sum,
    'total': sum
}
STATFUNC_NAME = {
    'max': 'Maximum',
    'mean': 'Mean',
    'median': 'Median',
    'min': 'Minimum',
    'stdev': 'Standard Deviation',
    'sum': 'Total',
    'total': 'Total'
}


def balance_plot(
    transactions: Transactions,
    median: bool = True,
    style: str = 'lines',
    title: Optional[str] = 'Transaction Balance Plot') -> Any:
    '''
    Produces a graphical plot of account balance over time.
    The function accepts the following input arguments:
      * median
        Whether to use median as the statistical smoothing function for balances
        which occur on the same date.
      * style
        The plotting style, being `lines`, `markers`, or `lines+markers`.
      * title
        The title string of the plot.
    '''
    fig = go.Figure()
    for (bank, account), this_account in transactions.group(by='bank-account').items():
        by_date = this_account.group(by='date-daily')
        dates = [d[0] for d in by_date]
        if median:
            balances = [by_date[d].median_balance() for d in by_date]
        else:
            balances = [by_date[d].mean_balance() for d in by_date]
        hovertexts = [by_date[d].hovertext() for d in by_date]
        fig.add_trace(go.Scatter(
            hovertext = hovertexts,
            mode = style,
            name = f'{bank} ({account})',
            x = dates,
            y = balances
        ))
    fig.update_layout(
        showlegend = True,
        title = title,
        xaxis_title = 'Date',
        yaxis_title = 'Median Account Balance ($)' if median else 'Mean Account Balance ($)'
    )
    return fig


def balance_candle_plot(
    transactions: Transactions,
    bank: str,
    account: str,
    title: Optional[str] = 'Transaction Balance Candle Plot') -> Any:
    '''
    Produces a graphical plot of account balance over time, in a candle plot
    format for a single bank/account pair. Accepts the following arguments:
    * account
      The account string to restrict the plot to. If left as none, the function
      will ensu
    * bank
      The bank string to restrict the plot to.
    * title
      The title string of the plot.
    '''
    fig = go.Figure()
    by_date = transactions.filter(account=account, bank=bank).group(by='date-daily')
    dates  = [d[0] for d in by_date]
    vclose = [round(by_date[d].mean_balance() - by_date[d].stdev_balance(), 2) for d in by_date]
    vhigh  = [by_date[d].max_balance() for d in by_date]
    vlow   = [by_date[d].min_balance() for d in by_date]
    vopen  = [round(by_date[d].mean_balance() + by_date[d].stdev_balance(), 2) for d in by_date]
    fig.add_trace(go.Candlestick(
        close = vclose,
        high = vhigh,
        low = vlow,
        open = vopen,
        x = dates
    ))
    fig.update_layout(
        title = title,
        xaxis_title = 'Date',
        yaxis_title = 'Account Balance ($)'
    )
    return fig


def tag_histogram(
    transactions: Transactions,
    hide: list[str] = [],
    statistic: str = 'median',
    title: Optional[str] = 'Tag Histogram') -> Any:
    '''
    Produces a histogram of tags and their median (or mean) transaction amounts.
    Accepts the following arguments:
    * hide
      A list of tags to visually exclude from the histogram.
    * statistic
      Specifies the statistic to be applied to each collection of tag amounts.
      May be one of `max`, `mean`, `median`, `min`, `stdev`, or `sum`/`total`.
    * title
      The title of the plot.
    '''
    fig = go.Figure()
    tags = [tag for tag in transactions.tags() if not tag in hide]
    values = [STATFUNC[statistic]([abs(t.amount) for t in transactions.filter(tags=tag)]) for tag in tags]
    fig.add_trace(go.Bar(
        x = tags,
        y = values
    ))
    fig.update_layout(
        title = title,
        xaxis_tickangle = -45,
        xaxis_title     = 'Tag',
        yaxis_title     = f'{STATFUNC_NAME[statistic]} Transaction Amount ($)'
    )
    return fig


def tag_distribution_plot(
    transactions: Transactions,
    bin_size: Optional[int] = None,
    title: Optional[str] = 'Tag Distribution Plot') -> Any:
    '''
    Produces a layered histgram of tags and their amount distributions. Note
    that the amount of a transaction is taken to be the absolute value of
    itself. Accepts the following arguments:
    * bin_size
      Specifies the delta amount spread within each histogram bin of a tag's
      associated amounts. If not specified, each histogram will have a different
      bin size calculated by dividing their standard deviation by 10.
    * title
      The title of the distribution plot.
    '''
    tags = transactions.tags()
    amounts = [[abs(t.amount) for t in transactions.filter(tags=tag)] for tag in tags]
    if not bin_size is None:
        _bin_size = bin_size
    else:
        _bin_size = [statistics.stdev(chunk) / 20.0 for chunk in amounts]
    fig = ff.create_distplot(
        amounts,
        tags,
        bin_size   = _bin_size,
        curve_type = 'normal'
    )
    fig.update_layout(
        title = title,
        xaxis_title = 'Transaction Amount ($)',
        yaxis_title = 'Proportion'
    )
    return fig


def tag_pie_chart(
    transactions: Transactions,
    statistic: str = 'total',
    title: Optional[str] = 'Tag Pie Chart') -> Any:
    '''
    Produces a pie chart comparing the specified statistic over tags.
    Accepts the following arguments:
    * statistic
      The statistical function to use as the comparison basis. Can be one of
      `max`, `mean`, `median`, `min`, `stdev`, or `sum`/`total`.
    * title
      The title of the plot.
    '''
    tags = transactions.tags()
    amounts = [STATFUNC[statistic]([abs(t.amount) for t in transactions.filter(tags=tag)]) for tag in tags]
    fig = go.Figure(data=[go.Pie(
        labels = tags,
        values = amounts
    )])
    fig.update_layout(title=title)
    return fig
