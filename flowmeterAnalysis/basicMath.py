import datetime as dt
import numpy as np
import pandas as pd

# given two data frames with dates as the indices, find the longest overlap in dates
def defineDateRange(df1, df2):
    start1 = df1.index[0]
    start2 = df2.index[0]
    if start1 <= start2:
        start = start2 #pick the later date
    else:
        start = start1
    end1 = df1.index[-1]
    end2 = df2.index[-1]
    if end1 <= end2:
        end = end1
    else:
        end = end2
    return(start,end)

def abstrapz(y, x = None, dx = 1.0):
    y = np.asanyarray(y)
    if x is None:
        d = dx
    else:
        x = np.asanyarray(x)
        d = np.diff(x)
    ret = (d * (y[1:] + y[:-1])/2.0)
    return(ret[ret > 0].sum())

def getTimeDiff(date1, date2, returnState):
    date1 = pd.to_datetime(date1)
    date2 = pd.to_datetime(date2)
    if date2 >= date1:
        dateDiff = date2 - date1
    else:
        dateDiff = date1 - date2
    # convert to days and seconds
    days = dateDiff.days
    seconds = dateDiff.seconds
    # covert to total hours and total minutes
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    returnOptions = {
        'days': days,
        'hours': hours,
        'minutes' : minutes,
        'seconds' : seconds}
    return(returnOptions[returnState])