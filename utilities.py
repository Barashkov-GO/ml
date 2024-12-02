def date_range(start_str, stop_str, freq, is_str=False):
    """Generates list of tuples of periods

    Args:
        start_str (str): from date (in str format)
        stop_str (str): till date (in str format)
        freq (str|int): 'M' or integer number of days
        is_str (bool, optional): is returning type needs to be str or dates. Defaults to False.

    Returns:
        list[tuple(str, str)|tuple(datetime, datetime)]
    """
    from datetime import timedelta
    import pandas as pd

    res = []
    while pd.to_datetime(start_str) < pd.to_datetime(stop_str):
        if type(freq) is str and freq.upper() == 'M':
            start = pd.to_datetime(start_str)
            start_str = str((pd.to_datetime(start_str) + timedelta(days=31)).date())
            start_str = f'{start_str[:-1]}1'
            end = pd.to_datetime(start_str) - timedelta(days=1)
            if not is_str:
                res.append((start, end))
            else:
                res.append((str(start.date()), str(end.date())))
        else:

            if not is_str:
                res.append((pd.to_datetime(start_str), pd.to_datetime(start_str) + timedelta(days=freq)))
            else:
                res.append((str(pd.to_datetime(start_str).date, str(pd.to_datetime(start_str) + timedelta(days=freq).date()))))
            start_str = str((pd.to_datetime(start_str) + timedelta(days=freq)).date())
    
    return res