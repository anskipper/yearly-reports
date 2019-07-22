#imports
import math
import datetime as dt 

import numpy as np
import pandas as pd

from flowmeterAnalysis import basicMath
from flowmeterAnalysis import readFiles

'''
INPUTS : 
    * dfDaily: pandas dataframe with daily rain totals over the analysis period
    * dfHourly: pandas dataframe with hourly rain totals over the analysis period
    * gagename: string with the name of the flow monitor's associated rain gage
OUTPUTS:
    * rainDates: a list of dates containing possible storm events that meet the following criteria:
        * daily rain total exceeds 0.1 in
        * hourly rain peak exceeds 0.03 in
        * the peak is within 80% of the daily total'''
def identifyStorms(dfDaily, dfHourly, gagename):
    dailyThresh = 0.1 #in
    peakThresh = 0.05 #in
    intenseThresh = 0.8 #percent
    rainDates = []
    # if the daily rain total exceeds the daily threshold, add the rain date to the list
    mask = dfDaily[gagename] > dailyThresh 
    rainDates.extend(dfDaily.index[mask])
    # PEAK THRESH
    mask = dfDaily[gagename] >= peakThresh
    possPeakDates = dfDaily.index[mask]   
    for date in possPeakDates:
        # only check if we havent already added it to the rain dates from the daily threshold
        if date not in rainDates:
            #check to see if the peak is greater than the peakThresh
            peak = (
                dfHourly.loc[date:date+ dt.timedelta(hours=23), gagename]
                .values
                .max())
            # if the hourly peak is greater than the peak threshold, add the rain date to the list
            if peak >= peakThresh:
                rainDates.extend([date])
            else:
                pass
        else:
            pass   
    #INTENSITY THRESH
    mask =  dfDaily[gagename] > 0
    possIntenseDates = dfDaily.index[mask]
    for date in possIntenseDates:
        if date not in rainDates:
            drt = dfDaily.loc[date,gagename]
            peak = (
                dfHourly.loc[date:date+ dt.timedelta(hours=23), gagename]
                .values
                .max())
            if peak/drt/1.0 > intenseThresh:
                rainDates.extend([date])
            else:
                pass
        else:
            pass
    rainDates.sort()
    return(rainDates)

'''
INPUTS:
    * dfHourly: pandas dataframe with hourly rain totals over the analysis period
    * date: a datetime/timestamp object of a possible storm date
    * gagename: string with the name of the flow monitor's associated rain gage
OUTPUTS:
    * stormInfo: a dictionary containing the following entries:
        * Start: the datetime of the start of the storm
        * Event: duration: in hours, rain total: in inches
        * Storm: duration: in hours, rain total: in inches'''
def stormAnalyzer(dfHourly, date, gagename):
    # find the first value that is on this date and the hourly rain total exceeds 0
    mask = ((dfHourly.index >= date)
        & (dfHourly.index < date + dt.timedelta(days=1))
        & (dfHourly.loc[:,gagename].values > 0))
    tStart = dfHourly.index[mask][0]
    # find the time that it stops raining within a 71 hour period
    # this is the EVENT DURATION
    mask = ((dfHourly.index >= tStart)
        & (dfHourly.index<tStart + dt.timedelta(days=2,hours=23))
        & (dfHourly.loc[:,gagename].values > 0))
    dur = basicMath.getTimeDiff(
        date1=dfHourly.index[mask][-1],
        date2=tStart,
        returnState='hours')
     # the duration has to be at least 1 hour to count
    eventDur = dur
    if dur > 0:
        #find the rain total within the event duration
        eventRT = (
            dfHourly.loc[
                tStart:tStart + dt.timedelta(hours=eventDur), gagename]
            .sum())
        # set the storm duration as the minimum of the event duration and 24 hours
        stormDur = min(eventDur, 24.0)
        #find the rain totals within storm duration
        stormRT = (dfHourly
            .loc[tStart:tStart + dt.timedelta(hours=stormDur), gagename]
            .sum())
    else:
            eventRT = 0
            stormDur = 0
            stormRT = 0
    stormInfo = {
        'Start' : tStart,
        'Event' : {
            'duration' : eventDur,
            'rain total' : eventRT
        },
        'Storm' : {
            'duration' : stormDur,
            'rain total' : stormRT
        },
    }
    return(stormInfo)

'''
INPUTS:
    * dfDaily: pandas dataframe with daily rain totals over the analysis period
    * dfHourly: pandas dataframe with hourly rain totals over the analysis period
    * gagename: string with the name of the flow monitor's associated rain gage
OUTPUTS:
    * df: a pandas dataframe containing the storm information for all the rain dates for a single rain gage'''
def getStormData(dfDaily, dfHourly, gagename):
    # define start and end ranges
    startDate = dfDaily.index[0]
    endDate = dfDaily.index[-1]
    # find that dates that meet the storm criteria
    rainDates = identifyStorms(
        dfDaily=dfDaily,
        dfHourly=dfHourly,
        gagename=gagename)
    # check to see if any of the storm analysis period will be outside the date range; if so, delete that date from the list
    if rainDates[0] - dt.timedelta(days=1) < startDate:
        del rainDates[0]
    elif rainDates[-1] + dt.timedelta(days=2) > endDate:
        del rainDates[-1]
    else:
        pass
    # find the time that the rain starts for each date
    tStart = []
    eventDur = []
    eventRT = []
    stormDur = []
    stormRT = []
    for date in rainDates:
        stormInfo = stormAnalyzer(
            dfHourly = dfHourly,
            date = date,
            gagename = gagename)
        # the duration has to be at least 1 hour to count
        if stormInfo['Event']['duration'] > 0 and stormInfo['Storm']['rain total'] > 0.2:
            tStart.extend([stormInfo['Start']])
            eventDur.extend([stormInfo['Event']['duration']])
            eventRT.extend([stormInfo['Event']['rain total']])
            stormDur.extend([stormInfo['Storm']['duration']])
            stormRT.extend([stormInfo['Storm']['rain total']])
        else:
            pass
    # create data frame of all the storms for this rain gage
    df = pd.DataFrame(
        data = {
            'Storm Dur': stormDur, 
            'Storm Rain': stormRT, 
            'Event Dur': eventDur, 
            'Event Rain': eventRT},
        index=tStart)
    return(df)

'''
INPUTS:
    * tStart: time of the start of the storm
    * stormDur: duration of the storm
    * dfMeans: pandas dataframe containing the weekday and weekend mean flows
OUTPUTS:
    * df: a pandas with the mean flows for the storm period 
    * color: a list of colors to plot each day, colored by weekday or weekend'''
# tStart is a datetime object (e.g., 01/01/2018 13:00:00) and stormDur is an integer of hours (e.g., 6) that will be within a range [0,24]
def constructMeanFlow(tStart, stormDur, dfMeans):
    colorWkd = 'xkcd:leaf green'
    colorWke = 'xkcd:hunter green'
    # pre-compensation
    pc = tStart - dt.timedelta(days = 1)
    # end of storm
    stormEnd = tStart + dt.timedelta(hours = stormDur)
    # recovery 1
    r1 = stormEnd + dt.timedelta(days = 1) 
    # recovery 2
    r2 = r1 + dt.timedelta(days = 1)
    # if the storm goes into the nexxt day
    if (stormEnd.date() - tStart.date()).days > 0:
        # weekday values
        wVals = [pc.weekday(),
            tStart.weekday(),
            stormEnd.weekday(),
            r1.weekday(),
            r2.weekday()]
    else:
        wVals = [pc.weekday(),
            tStart.weekday(),
            r1.weekday(),
            r2.weekday()]
    # set up empty lists
    meanFlow = []
    color = []
    for k in range(0, len(wVals)):
        if wVals[k] > 4: #WEEKEND
            col = 'Weekend'
            colorVal = colorWke
        else:
            col = 'Weekday'
            colorVal = colorWkd
        # add the appropriate color to the list
        color.extend([colorVal])
        if k == 0: # pre-comp period
            meanFlow.extend(dfMeans.loc[pc.time():, col])
        elif k == len(wVals) - 1: # end of r2
            meanFlow.extend(dfMeans.loc[:r2.time(), col])
        else:
            meanFlow.extend(dfMeans.loc[:, col])
    # construct the dataframe for plotting
    hours = basicMath.getTimeDiff(
        date1=pc,
        date2=r2,
        returnState='hours')
    dateTimes = pd.date_range(pc,
        periods=hours * 60/15 + 1,
        freq = '15min')
    df = pd.Series(
        data=meanFlow,
        index=dateTimes,
        name='Mean Flow')
    df.index = pd.to_datetime(df.index)
    return (df,color)
    