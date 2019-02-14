"""Some helpful functions for working with TAP-exported data"""

import sys
import warnings
import datetime as dt
import pandas as pd
import numpy as np
from collections import OrderedDict

# warnings.simplefilter('ignore')

mask_values = (1, 96, 112, 160, 176, 224, 352, 368, 416, 432, 480, 864, 880, 928, 944, 992)


def assemble(timeseries, ind, bands):
    """
    Populate n-number of arrays using appropriate row and column locations

    Args:
        timeseries (array_like): A series of tuples, each containing a chip of data in the time series
        bands (Iterable): Collection of band names that matches chipmunk bands
        ind (int): The index location for the target date in each array_like object within the time series

    Returns:
        Dict[str: np.ndarray]

    """
    out = {b: np.zeros(shape=(100, 100), dtype=np.int) for b in bands}

    for t in timeseries:
        coord_x = t[0][2]
        coord_y = t[0][3]

        chip_coord_x = t[0][0]
        chip_coord_y = t[0][1]

        col = int((coord_x - chip_coord_x) / 30)
        row = int((chip_coord_y - coord_y) / 30)

        for b in bands:
            out[b][row][col] = t[1][b][ind]

    return out


def temporal(df, ascending=True, field='dates'):
    """
    Sort the input data frame based on time
    Args:
        df (pd.DataFrame): The input data
        ascending (bool): Whether or not to sort in ascending order
        field (str): The data frame field containing datetime objects

    Returns:
        pd.DataFrame

    """
    return df.sort_values(field, ascending).reset_index(drop=True)


def sort_on(df, field, ascending=True):
    """
    A more open-ended sorting function, may be used on a specified field

    Args:
        df (pd.DataFrame): The input data
        field (str): The field to sort on
        ascending (bool): Whether or not to sort in ascending order

    Returns:
        pd.DataFrame

    """
    return df.sort_values(field, ascending).reset_index(drop=True)


def dates(df, params, field='dates'):
    """
    Return an inclusive sliced portion of the input data frame based on a min and max date

    Args:
        df (pd.DataFrame): The input data
        params (Tuple[dt.datetime, dt.datetime]): Dates, must be in order of MIN, MAX
        field (str): The date field used to find matching values

    Returns:
        pd.DataFrame

    """
    _min, _max = params

    return df[(df[field] >= _min) & (df[field] <= _max)].reset_index(drop=True)


def years(df):
    """
    Get an array of unique years in the current time series

    Args:
        df (pd.DataFrame): The input data frame

    Returns:
        np.ndarray

    """
    return df['dates'].apply(lambda x: (x.timetuple()).tm_year).unique()


def date_range(params):
    """
    Generate date ranges for a seasonal time series

    Args:
        params (dict): Arguments for the pandas date_range function

    Returns:

    """
    return pd.date_range(**params)


def seasons(df, start_mon, start_day, end_mon, end_day, periods=None, freq='D', **kwargs):
    """

    Args:
        df:
        start_mon:
        start_day:
        end_mon:
        end_day:
        periods:
        freq:
        **kwargs:

    Returns:

    """
    return OrderedDict([(y,
                         date_range({'start': dt.datetime(y, start_mon, start_day),
                                     'end': dt.datetime(y, end_mon, end_day),
                                     'periods': periods,
                                     'freq': freq}))

                        for y in years(df)])


def stats(arr):
    """
    Return the statistics for an input array of values

    Args:
        arr (np.ndarray)

    Returns:
        OrderedDict

    """
    try:
        return OrderedDict([('min', arr.mean()),
                            ('max', arr.max()),
                            ('mean', arr.mean()),
                            ('std', arr.std())])

    except ValueError:  # Can happen if the input array is empty
        return OrderedDict([('min', None),
                            ('max', None),
                            ('mean', None),
                            ('std', None)])


def get_seasonal_info(df, params):
    """
    A wrapper function for easily returning the statistics on a seasonal basis for a given field of the data frame

    Args:
        df (pd.DataFrame)
        params (dict)

    Returns:
        OrderedDict

    """

    __seasons = seasons(df, **params)

    return OrderedDict([
        (y, stats(
            values(
                mask(
                    dates(df, (__seasons[y][0], __seasons[y][-1])), **params
                ), **params
            )
        )
         )
        for y in years(df)
    ])


def values(df, field, **kwargs):
    """
    Return values from a specific field of the data frame within a given time extent

    Args:
        df (pd.DataFrame): The exported TAP tool data
        field (str): The field representing the column name

    Returns:
        np.ndarray: An array of the time-specified values

    """
    return df[field].values


def plot_data(d, field):
    """
    Return the x and y series to be used for plotting

    Args:
        d (OrderedDict)
        field (str)

    Returns:
        Tuple[list, list]:
            [0] The x-series
            [1] The y-series

    """
    return ([year for year in d.keys() if d[year][field] is not None],
            [i[field] for k, i in d.items() if i[field] is not None])


def mask(df, vals=mask_values, mask_field='qa', **kwargs):
    """
    Remove rows from the data frame that match a condition

    Args:
        df (pd.DataFrame): The input data
        vals (List[Number[int, float]]): The values used to filter the data frame, rows == value will be removed!
        mask_field (str): The field to use for filtering

    Returns:
        pd.DataFrame

    """
    return df[~df[mask_field].isin(np.array(vals))].reset_index(drop=True)


def nearest_date(array, date):
    """
    Find the index value in the array to the nearest matching date, date may therefore not be a value
    within the array

    Args:
        array (array_like): The input data
        date (Tuple[int, int, int]): The date to look for given as (Year, Month, M-day)

    Returns:
        int

    """
    date = dt.datetime(*date).toordinal()

    array = np.asarray(array)

    return (np.abs(array - date)).argmin()


def spectral_signature(df, date):
    """

    Args:
        df:
        date:

    Returns:

    """
    index = nearest_date(df.dates.apply(lambda x: x.toordinal()), date)

    return df.iloc[index]


def load_csv(csv_file, dates_field='dates', use_datetime=True):
    """

    Args:
        csv_file (str): The full path to the input csv file
        dates_field (str): The name of the dates column
        use_datetime (bool): Whether or not to use datetime format

    Returns:
        pd.DataFrame

    """
    return pd.read_csv(csv_file,
                       parse_dates=[dates_field],
                       infer_datetime_format=use_datetime).drop(columns='Unnamed: 0')
