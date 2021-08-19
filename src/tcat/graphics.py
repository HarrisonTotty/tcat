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

STAT_TITLE = {
    'count': 'Number of Transactions',
    'max_abs_amount': 'Maximum Absolute Transaction Amount ($)',
    'max_abs_balance': 'Maximum Absolute Account Balance ($)',
    'max_amount': 'Maximum Transaction Amount ($)',
    'max_balance': 'Maximum Account Balance ($)',
    'mean_abs_amount': 'Mean Absolute Transaction Amount ($)',
    'mean_abs_balance': 'Mean Absolute Account Balance ($)',
    'mean_amount': 'Mean Transaction Amount ($)',
    'mean_balance': 'Mean Transaction Balance ($)',
    'mean_freq_daily': 'Mean Transaction Frequency (per day)',
    'mean_freq_monthly': 'Mean Transaction Frequency (per month)',
    'mean_freq_weekly': 'Mean Transaction Frequency (per week)',
    'mean_freq_yearly': 'Mean Transaction Frequency (per year)',
    'median_abs_amount': 'Median Absolute Transaction Amount ($)',
    'median_abs_balance': 'Median Absolute Account Balance ($)',
    'median_amount': 'Median Transaction Amount ($)',
    'median_balance': 'Median Account Balance ($)',
    'median_freq_daily': 'Mean Transaction Frequency (per day)',
    'median_freq_monthly': 'Median Transaction Frequency (per month)',
    'median_freq_weekly': 'Median Transaction Frequency (per week)',
    'median_freq_yearly': 'Median Transaction Frequency (per year)',
    'min_abs_amount': 'Minimum Absolute Transaction Amount ($)',
    'min_abs_balance': 'Minimum Absolute Account Balance ($)',
    'min_amount': 'Minimum Transaction Amount ($)',
    'min_balance': 'Minimum Account Balance ($)',
    'stdev_abs_amount': 'Standard Deviation of Absolute Transaction Amount ($)',
    'stdev_abs_balance': 'Standard Deviation of Absolute Account Balance ($)',
    'stdev_amount': 'Standard Deviation of Transaction Amount ($)',
    'stdev_balance': 'Standard Deviation of Account Balance ($)',
    'stdev_freq_daily': 'Standard Deviation Transaction Frequency (per day)',
    'stdev_freq_monthly': 'Standard Deviation Transaction Frequency (per month)',
    'stdev_freq_weekly': 'Standard Deviation Transaction Frequency (per week)',
    'stdev_freq_yearly': 'Standard Deviation Transaction Frequency (per year)',
    'total_abs_amount': 'Total Absolute Transaction Amount ($)',
    'total_abs_balance': 'Total Absolute Account Balance ($)',
    'total_amount': 'Total Transaction Amount ($)',
    'total_balance': 'Total Account Balance ($)',
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
    This function is just a convenient wrapper around `statistic_plot()`.
    '''
    return statistic_plot(
        transactions,
        statistic = 'median_balance' if median else 'mean_balance',
        scale = 'daily',
        style = style,
        title = title
    )

def balance_candle_plot(
    transactions: Transactions,
    bank: str,
    account: str,
    scale: str = 'monthly',
    title: Optional[str] = 'Transaction Balance Candle Plot') -> Any:
    '''
    Produces a graphical plot of account balance over time, in a candle plot
    format for a single bank/account pair. Accepts the following arguments:
      * account
        The account string to restrict the plot to.
      * bank
        The bank string to restrict the plot to.
      * scale
        The scale to group each candle box, being `daily`, `weekly`, `monthly`, or
        `yearly`.
      * title
        The title string of the plot.
    A candlestick chart encloses the following bits of information:
      * "low" is the minimum balance within the time range.
      * "high" is the maximum balance within the time range.
      * "open" is the balance before the first transaction within the time
        range.
      * "close" is the balance after the last transaction within the time range.
    '''
    fig = go.Figure()
    by_date = transactions.filter(account=account, bank=bank).group(by=f'date-{scale}')
    dates  = [d[0] for d in by_date]
    vclose = [by_date[d][-1].balance for d in by_date]
    vhigh  = [by_date[d].max_balance() for d in by_date]
    vlow   = [by_date[d].min_balance() for d in by_date]
    vopen  = [round(by_date[d][0].balance - by_date[d][0].amount, 2) for d in by_date]
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

def statistic_plot(
    transactions: Transactions,
    statistic: str = 'median_balance',
    scale: str = 'daily',
    style: str = 'lines',
    title: Optional[str] = None) -> Any:
    '''
    Produces a graphical plot of the specified statistic over time. The
    specified statistic may be any key returned from the
    `Transactions.statistics()` method.
    Accepts the following arguments:
      * statistic
        The specified statistic to plot on the y-axis.
      * scale
        The range of dates associated with each data point. May be specified as
        `daily`, `weekly`, `monthly`, or `yearly`.#!/usr/bin/env python
      * title
        An optional title for the plot.
    '''
    fig = go.Figure()
    for (bank, account), account_trans in transactions.group(by=f'bank-account').items():
        by_date = account_trans.group(by=f'date-{scale}')
        dates = [d[0] for d in by_date]
        stats = [by_date[d].statistics() for d in by_date]
        hovertexts = [by_date[d].hovertext() for d in by_date]
        fig.add_trace(go.Scatter(
            hovertext = hovertexts,
            mode      = style,
            name      = f'{bank} ({account})',
            x         = dates,
            y         = [s[statistic] for s in stats]
        ))
    fig.update_layout(
        showlegend  = True,
        title       = title,
        xaxis_title = 'Date',
        yaxis_title = STAT_TITLE[statistic]
    )
    return fig

def tag_histogram(
    transactions: Transactions,
    hide: list[str] = [],
    statistic: str = 'median_abs_amount',
    title: Optional[str] = 'Tag Histogram') -> Any:
    '''
    Produces a histogram of tags and their median (or mean) transaction amounts.
    Accepts the following arguments:
      * hide
        A list of tags to visually exclude from the histogram.
      * statistic
        Specifies the statistic to be applied to each collection of tag amounts.
        May be one of any key returned by the `Transactions.statistics()`
        method.
      * title
        The title of the plot.
    '''
    fig = go.Figure()
    tags = [tag for tag in transactions.tags() if not tag in hide]
    stats = [transactions.filter(tags=tag).statistics() for tag in tags]
    fig.add_trace(go.Bar(
        x = tags,
        y = [v[statistic] for v in stats]
    ))
    fig.update_layout(
        title = title,
        xaxis_tickangle = -45,
        xaxis_title     = 'Tag',
        yaxis_title     = STAT_TITLE[statistic]
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
        associated amounts. If not specified, each histogram will have a
        different bin size calculated by dividing their standard deviation by
        10.
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
    hide: list[str] = [],
    show: list[str] = [],
    statistic: str = 'total_abs_amount',
    title: Optional[str] = 'Tag Pie Chart') -> Any:
    '''
    Produces a pie chart comparing the specified statistic over tags.
    Accepts the following arguments:
      * hide
        Hides the specified tags from being displayed from the pie chart.
      * show
        Limits the displayed tags to the specified collection of tags.
      * statistic
        The statistical function to use as the comparison basis. Can be any key
        from the `Transactions.statistics()` method.
      * title
        The title of the plot.
    '''
    tags = []
    for tag in transactions.tags():
        if show and not tag in show: continue
        if hide and tag in hide: continue
        tags.append(tag)
    stats = [transactions.filter(tags=tag).statistics() for tag in tags]
    fig = go.Figure(data=[go.Pie(
        labels = tags,
        values = [s[statistic] for s in stats]
    )])
    fig.update_layout(title=title)
    return fig


def tag_trend_plot(
    transactions: Transactions,
    hide: list[str] = [],
    scale: str = 'weekly',
    show: list[str] = [],
    statistic: str = 'total_abs_amount',
    style: str = 'lines',
    title: Optional[str] = 'Tag Trend Plot') -> Any:
    '''
    Produces a plot describing the evolution of the specified statistic for each
    tag.
    Accepts the following arguments:
      * hide
        Hides the specified tags from being displayed on the plot.
      * scale
        Specifies the scale at which the specified statistic will be applied.
        May be set to `daily`, `weekly`, `monthly`, or `yearly`.
      * show
        Limits the displayed tags to the specified list of tags.
      * statistic
        The statistic to plot on the y-axis of the plot. May be any key provided
        by the `Transactions.statistics()` method.
      * style
        The plotting style to use, being `lines`, `markers`, or `lines+markers`.
      * title
        Sets the title of the plot to the specified string.
    '''
    fig = go.Figure()
    tags = []
    for tag in transactions.tags():
        if hide and tag in hide: continue
        if show and not tag in show: continue
        tags.append(tag)
    for tag in tags:
        by_date = transactions.filter(tags=tag).group(by=f'date-{scale}')
        dates = [d[0] for d in by_date]
        stats = [by_date[d].statistics() for d in by_date]
        hovertexts = [by_date[d].hovertext() for d in by_date]
        fig.add_trace(go.Scatter(
            hovertext = hovertexts,
            mode      = style,
            name      = tag,
            x         = dates,
            y         = [s[statistic] for s in stats]
        ))
    fig.update_layout(
        showlegend  = True,
        title       = title,
        xaxis_title = 'Date',
        yaxis_title = STAT_TITLE[statistic]
    )
    return fig
