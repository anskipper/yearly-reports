import datetime as dt
import numpy as np

import pandas as pd

from flowmeterAnalysis import readFiles
from flowmeterAnalysis import rainEvents
from flowmeterAnalysis import basicMath
from flowmeterAnalysis import conversions

### DRY WEATHER ANALYSIS ##

''' 
For the dry weather analysis, days are considered "rainy" if they meet one of two criteria
1) it rains more than the rain threshold
2) the date is within a buffer period either before or after the date that the rain threshold has been exceeded
'''
# given a data frame with dates in the index and rain totals in the column, find which days exceed a rain threshold and a certain amount of "buffer" days before and after that date; ensures that the last after buffer date does not exceed the date range in the original data
# create a new data frame that has the original rain date as the index, a before date column corresponding to the amount of buffer days before, and an after date column corresponding to the amount of buffer dats after
def findRain(df,rainthresh,bufferBefore,bufferAfter):
    startDate = df.index[0]
    endDate = df.index[-1]
    rainDates = df.index[(df > 0.1).values]
    #filter out days before rain
    beforeDates = rainDates - dt.timedelta(days=bufferBefore)
    #filter out days after rain
    afterDates = rainDates + dt.timedelta(days=bufferAfter)
    #assign to new dataframe
    df_rainDates = pd.DataFrame({'Before': beforeDates,
        'After': afterDates})
    #rearrange for some reason...
    df_rainDates = df_rainDates[['Before', 'After']]
    df_rainDates = df_rainDates.set_index(rainDates)
    #check that the rain dates are within the specified range
    if beforeDates[0] < startDate:
        df_rainDates.iloc[0, 0] = startDate
    elif afterDates[-1] > endDate:
        df_rainDates.iloc[-1, 1] = endDate
    return(df_rainDates)

# set the weather of the flow data data frame to either "Dry" or "Rain Event"
def setWeather(df,df_rainDates):
    newdf = df.assign(Weather = 'Dry')
    for j in range(0, len(df_rainDates.index)):
        newdf.loc[df_rainDates.iloc[j, 0]:df_rainDates.iloc[j, 1],
            'Weather']='Rain Event'
    return(newdf)

# find dry days on either the "weekday" or the "weekend"
def findDryDays(df,weekCatagory):
    if weekCatagory == 'weekday':
        df = df[(df.index.dayofweek < 5)]
    elif weekCatagory == 'weekend':
        df = df[df.index.dayofweek >= 5]
    else:
        #PUT AN ERROR HERE
        raise AttributeError()
    df = df[df['Weather']=='Dry']
    return(df)

def weekdaySeries(df,colVal,returnType,weather):
    if returnType == 'weekday':
        mask = ((df.index.dayofweek < 5) 
            and (df['Weather']==weather))
    elif returnType == 'weekend':
        mask = ((df.index.dayofweek >= 5) 
            and (df['Weather']==weather))
    else:
        raise AttributeError(returnType)
    s = df.loc[mask, colVal]
    return(s)    

#find the GWI according to a certain method; for now, only the percent method is supported
def findGWI(m1,m2,method):
    if method == 'percent':
        gwi = 0.75*min(m1.min(), m2.min())
    else:
        raise AttributeError()
    return(gwi)

def findBaseInfiltration(gwi,Qmean):
    return(gwi/Qmean)

# inputs a numpy array of depths in inches, the diameter in inches, and outputs the ratio
def depthOverDiameter(d,diameter):
    return(d/diameter)

def findSanMean(df,gwi):
    dfMean = df.mean(axis=1)
    df_san = (dfMean - gwi)
    sanMean = df_san.mean()
    return(sanMean)

def findNormSanitaryFlow(df,gwi,colName):
    dfMean = df.mean(axis=1)
    df_san = (dfMean - gwi)
    sanMean = df_san.mean()
    ki = np.array([])
    for j in range(1, len(df_san), 4): #4 meas/hr
        s = df_san.iloc[j:j+3]
        smean = s.mean()
        ki = np.append(ki, smean/sanMean)
    snorm = ki*24/sum(ki) #adjust for the fact the sum should be equal to 24 hrs
    #make into a series/dataframe
    l = df.index[range(0, len(df.index), 4)]
    snorm = pd.DataFrame(
        data=snorm, 
        index=l.tolist(), 
        columns=[colName])
    return(snorm)

def diurnals(dfWKD,dfWKE):
    wkdMean =dfWKD.mean(axis=1)
    wkeMean = dfWKE.mean(axis=1)
    df = pd.DataFrame(
        data={
            'Weekday': wkdMean, 
            'Weekend': wkeMean
            },
        index=wkdMean.index,
        columns=['Weekday', 'Weekend'])
    df.index.name = 'Time'
    return(df)

'''
INPUTS:
    * flowFile: string containing the file path of a particular flow file for a single monitor
    * fmname: string of the flow monitor name (e.g., BC01)
    * dfDailyRain: pandas dataframe with dates as the indices and rain gages as columns
    * dfmDetails: pandas dataframe with details about each flow monitor, such as rain gage, diameter, etc.
    * analysisDates: tuple of analysis dates (begin,end)
    * rainThresh: a float of inches of rain used to determine which days are rainy
OUTPUTS:
    * dryWeatherDict: a dictionary the following keys:
        * Weekday: a dictionary containing the following keys: 
            * d/D: a numpy array containing the depth over diameter values
            * Gross Q: a pandas series with datetimes as indices containing the gross flow rates
            * DataFrame: a pandas dataframe with time as the index, dates for the columns, and values corresponding to measured flow rates
        * Weekend: a dictionary containing the following keys: 
            * d/D: a numpy array containing the depth over diameter values
            * Gross Q: a pandas series with datetimes as indices containing the gross flow rates
            * DataFrame: a pandas dataframe with time as the index, dates for the columns, and values corresponding to measured flow rates
        * Overall: a dictionary containing the following keys: 
            * BI: a float of the base infiltration, defined as the groundwater infiltration as a percentage of the overall mean flow rate
            * d/D: a numpy array containing the depth over diameter values'''
def dryWeather(dfFlow, fmname, dfDailyRain, 
               dfmDetails, analysisDates,rainThresh):
    # find the rain gage for this flow monitor
    gagename = dfmDetails.loc[fmname, 'Rain Gage']
    # find the rain totals of this rain gage
    dfRain = dfDailyRain[gagename]
    #find dates on which the rain threshold was exceeded
    bufferBefore = 2 # days
    bufferAfter = 3 # days
    dfRainDates = findRain(
        df=dfRain, 
        rainthresh=rainThresh,
        bufferBefore=bufferBefore,
        bufferAfter=bufferAfter)
    # set the weather to either 'Dry' or 'Rain Event'
    dfFlow = setWeather(
        df=dfFlow,
        df_rainDates=dfRainDates)
    # separate into weekdays and weekends
    df_dryWeekday = findDryDays(
        df=dfFlow,
        weekCatagory='weekday')
    df_dryWeekend = findDryDays(
        df=dfFlow,
        weekCatagory='weekend')
    # create depth series for boxplot (d/D) and overall d/D (dry weather)
    D = dfmDetails.loc[fmname, 'Diameter']
    dD = depthOverDiameter(
        d = dfFlow.loc[dfFlow['Weather'] == 'Dry', 'y (in)'].values,
        diameter=D)
    dD_wkd = depthOverDiameter(
        d = df_dryWeekday.loc[:, 'y (in)'].values,
        diameter = D)
    dD_wke = depthOverDiameter(
        d = df_dryWeekend.loc[:, 'y (in)'].values,
        diameter = D)
    # create flowrate series for boxplot (gross Q)
    Qgross_wkd = df_dryWeekday.loc[:, 'Q (MGD)']
    Qgross_wke = df_dryWeekend.loc[:, 'Q (MGD)']
    # overall mean
    Qmean = np.array(
        [Qgross_wkd.mean(), 
        Qgross_wke.mean()]).mean()
    #reorganize the flow data such that the indices are time of day, the columns are dates, the values are flow rate
    df_dryWeekday = readFiles.reorganizeByTime(
        df = df_dryWeekday,
        colVal = 'Q (MGD)')
    df_dryWeekend = readFiles.reorganizeByTime(
        df = df_dryWeekend,
        colVal = 'Q (MGD)')
    # create a dictionary to return
    ################# OUTPUT #################
    dryWeatherDict = {
        'Weekday' : {
            'd/D' : dD_wkd[~np.isnan(dD_wkd)], # type: numpy array, units: %
            'Gross Q' : Qgross_wkd, #type: numpy array, units: MGD
            'DataFrame' : df_dryWeekday, #type: pandas dataframe
            'Gross Diurnal' : df_dryWeekday.mean(axis = 1)
        },
        'Weekend' : {
            'd/D' : dD_wke[~np.isnan(dD_wke)],
            'Gross Q' : Qgross_wke,
            'DataFrame' : df_dryWeekend,
            'Gross Diurnal' : df_dryWeekday.mean(axis = 1)
        },
        'Overall' : {
            'd/D' : dD
        }
    }
    return(dryWeatherDict)

'''
INPUTS:
    * basinDryWeather: a dictionary containing flow monitors as keys to dryWeatherDict
        * dryWeatherDict: a dictionary containing info about the weekday and weekend d/D, gross Q, and ensemble average dataframes as well as overall values for d/D and base infiltration (BI)
    * dfUpstream: a pandas dataframe with the flow monitor as an index with all the immediate upstream monitors identified
    * fmname: string of the flow monitor name (e.g., BC01)
OUTPUTS:
    * basinDryWeather: updated to contain the weekday and weekend net Q'''
def netDryQ(basinDryWeather,dfUpstream,fmname):
    # get the dry weather values for this flow monitor
    dryWeatherDict = basinDryWeather[fmname]
    # find the upstream flow monitors
    usfmList = readFiles.findUpstreamFMs(dfUpstream, fmname)
    dryWeatherDict['Weekday']['Net Q'] = dryWeatherDict['Weekday']['Gross Q']
    dryWeatherDict['Weekend']['Net Q'] = dryWeatherDict['Weekend']['Gross Q']
    dryWeatherDict['Weekday']['Net Diurnal'] = dryWeatherDict['Weekday']['Gross Diurnal']
    dryWeatherDict['Weekend']['Net Diurnal'] = dryWeatherDict['Weekend']['Gross Diurnal']
    if not usfmList: # if the list is empty
        # then net and gross are the same
        pass
    else:
        for usfm in usfmList:
            up_dryWeatherDict = basinDryWeather[usfm]
            dryWeatherDict['Weekday']['Net Q'] += (
                - up_dryWeatherDict['Weekday']['Gross Q'])
            dryWeatherDict['Weekend']['Net Q'] += (
                - up_dryWeatherDict['Weekend']['Gross Q'])    
            dryWeatherDict['Weekday']['Net Diurnal'] += (
                - up_dryWeatherDict['Weekday']['Gross Diurnal'])
            dryWeatherDict['Weekend']['Net Diurnal'] += (
                - up_dryWeatherDict['Weekend']['Gross Diurnal'])
    # create flowrate series for boxplot (gross Q)
    Qgross_wkd = dryWeatherDict['Weekday']['Net Q']
    Qgross_wke = dryWeatherDict['Weekend']['Net Q']
    # overall mean
    Qmean = np.array(
        [Qgross_wkd.mean(), 
        Qgross_wke.mean()]).mean()
        # find the groundwater infiltration
    gwi = findGWI(
        m1 = dryWeatherDict['Weekday']['Net Diurnal'],
        m2 = dryWeatherDict['Weekend']['Net Diurnal'],
        method = 'percent')
    # find base infiltratio as a percentage
    bi = findBaseInfiltration(
        gwi = gwi,
        Qmean = Qmean)
    dryWeatherDict['Overall']['Base Infiltration'] = bi
    # update basinDryWeather
    basinDryWeather[fmname] = dryWeatherDict
    return(basinDryWeather)

### WET WEATHER ANALYSIS ##

'''
INPUTS:
    * dfFlow: pandas dataframe with flow monitor data (depth, velocity, flow rate) at 15 minute intervals over the analysis period
    * gagename: string with the name of the flow monitor's associated rain gage
    * dfDaily: pandas dataframe with daily rain totals over the analysis period
    * dfHourly: pandas dataframe with hourly rain totals over the analysis period
    * fmname: the flow monitor name (e.g., BC01)
    * saveDir: the directory to save files, images, etc.
    * gageStorms:
        * default: an empty dictionary
        * otherwise: a dictionary with rain gages as keys to pandas dataframes of storm information for the entire analysis period
    * dfMeans: 
        * default: an empty list
        * otherwise: a pandas dataframe with the weekday and weekend values of the dry weather mean flow
    * meanFile:
        * default: an empty list
        * otherwise: a string with the filepath to read the mean data into a pandas dataframe
OUTPUTS:
    * gageStorms: a dictionary with rain gages as keys to pandas dataframes of storm information for the entire analysis period (dfStorms)
        * dfStorms: a pandas dataframe containing all the information about storms and the gross volume of I&I for that storm
    * stormQ: a dictionary with the storm date as the key containing an array of the positive difference between recorded flow rate and the mean flow rate'''
def grossII(dfFlow, gagename, dfDaily, dfHourly,fmname,  
            saveDir = [], gageStorms = {}, dfmeans = [], meanFile = []):
    # create empty dictionary stormQ
    stormQ = {'Gross' : {}}
    # check to see if this gage has already been processed
    if gagename in gageStorms:
        dfStorms = gageStorms[gagename]
    else:
        dfStorms = rainEvents.getStormData(
            dfDaily = dfDaily,
            dfHourly = dfHourly,
            gagename = gagename)
        # update gageStorms
        gageStorms[gagename] = dfStorms
    # check to see if the meanfile is unassigned
    # if the dfmeans i empty
    if not dfmeans:
        if isinstance(meanFile, str):           
            dfmeans = readFiles.readTotalFlow(filename = meanFile)
    elif not meanFile:
        if not dfmeans:
            raise AttributeError()
    # for every storm
    grossVol = []
    # conversion from measurement increments to days for volume calculation
    delta = 15.0/24/60 
    for k in range(0, len(dfStorms.index)):
        # construct the mean flow for the storm period
        tStart = dfStorms.index[k]
        sMeanFlow, meanColor = rainEvents.constructMeanFlow(
            tStart = tStart,
            stormDur = dfStorms.loc[tStart, 'Storm Dur'],
            dfMeans = dfmeans)    
        # pre-compensation period
        pc = tStart - dt.timedelta(days=1)
        # end of recovery period 2
        r2 = (tStart 
            + dt.timedelta(days = 2, 
                hours=dfStorms.loc[tStart, 'Storm Dur']))
        # pull the instantaneous flow data for the storm period
        sFlow = dfFlow.loc[pc:r2, 'Q (MGD)']
        # calculate the precompensation amount
        pcAdjust = (
            (sFlow[pc:tStart - dt.timedelta(minutes = 15)]
            - sMeanFlow[pc:tStart - dt.timedelta(minutes = 15)]
            )
            .values
            .mean())
        # shift mean Flows by this amount
        sMeanFlow += pcAdjust
        # integrate from storm period to end of r2
        grossQ = sFlow[tStart:r2] - sMeanFlow[tStart:r2]
        grossVol.extend(
                [delta * basicMath.abstrapz(grossQ.values)])
        grossQ[grossQ < 0]=0
        # add to dictionary stormQ
        stormQ['Gross'][tStart] = grossQ
    # add grossVol to storms
    dfStorms['Gross Vol'] = grossVol
    #dfStorms = dfStorms[dfStorms['Gross Vol'] > 0]  
    #saveName = saveDir + '\\' + fmname + '_stormData.csv'
    #dfStorms.to_csv(saveName)
    return(gageStorms,dfStorms,stormQ)

'''
INPUTS:
    * fmname: the flow monitor name (e.g., BC01)
    * systemGrossQ: a dictionary with the flow monitors as keys containing a dictionary (storm Q)
        * stormQ: a dictionary with the storm date as the key containing an array of the positive difference between recorded flow rate and the mean flow rate
    * gageStorms: a dictionary with the gagename as keys containing all the identified storm dates
    * dfUpstream: a pandas dataframe with the flow monitor as an index with all the immediate upstream monitors identified
    * dfDaily: pandas dataframe with daily rain totals over the analysis period
    * dfHourly: pandas dataframe with hourly rain totals over the analysis period
    * gagename: string with the name of the flow monitor's associated rain gage
    * stormDict: a dictionary with the flow monitors as keys containing a pandas dataframe (dfStorms)
        * dfStorms: a pandas dataframe containing all the information about storms that had a positive gross volume
OUTPUTS:
    * dfStorms: a pandas dataframe containing all the information about storms and the gross and net volumes of I&I for that storm
    * stormNetQ'''
def netII(fmname, systemGrossQ, dfUpstream, dfDaily,
    dfHourly, gagename,stormsDict):
    stormNetQ = {}
    # set up empty list
    netVol = []
    # get the gross Q's for this flow monitor
    stormQ = systemGrossQ[fmname]['Gross']
    # get the storm dataframe for this flow monitor
    dfStorms = stormsDict[fmname]
    # conversion from measurement increments to days for volume calculations
    delta = 15.0/24/60 
    # check to see if this gage has already been processed
    # set the default
    dfStorms['Net Vol'] = dfStorms['Gross Vol']
    # find the upstream flow monitors
    usfmList = readFiles.findUpstreamFMs(dfUpstream, fmname)
    if not usfmList: # if the list is empty
        pass # then net and gross are the same
    else:
        for tStart in pd.to_datetime(dfStorms.index.values):
            rain_usfmList = []
            # is this date in all the upstream flow monitors?
            for usfm in usfmList:
                # if this rain date is captured upstream
                if tStart in systemGrossQ[usfm]['Gross']:
                    rain_usfmList.append(usfm)
                else:
                    pass
            # if all the upstream rain gages recorded storms
            if len(rain_usfmList)==len(usfmList): 
                # set up the new Q as a copy of the gross Q values
                netQ = stormQ[tStart].copy()
                for usfm in usfmList:
                    # go find the upstream gross Q's 
                    up_stormQ = systemGrossQ[usfm]['Gross'][tStart]
                    # subtract the upstream flow rate to get the net flow rate
                    netQ += -up_stormQ
                stormNetQ[tStart] = netQ
                netVol.extend(
                    [delta * basicMath.abstrapz(netQ.values)])
            else:
                netVol.extend([float('NaN')])
        dfStorms['Net Vol'] = netVol
    return(dfStorms,stormNetQ)

'''
INPUTS:
    * basinArea: recorded basin area for a certain flow monitors (from dfmDetails, from fmData file)
    * dfStorms: a pandas dataframe containing all the information about storms and the gross and net volumes of I&I for that storm
OUTPUTS:
    * cc: capture coefficient for each storm, defined as the volume of net I&I over the rainfall volume (rain depth * basin area)'''
def findCaptureCoeff(basinArea,dfStorms):
    netIIVol = dfStorms.loc[:,'Net Vol'].values
    eventRT = dfStorms.loc[:,'Event Rain'].values
    volRain = (conversions.gal_ft3(
                x=(conversions.acre_ft2(
                    x=basinArea,
                    x_unit='Ac'
                   ) * eventRT/12.0),
                x_unit='ft3')) # IN GALLONS
    cc = 1e6 * netIIVol / volRain
    dfStorms['Capt Coeff'] = cc
    return(dfStorms)

'''
INPUTS:
    * basinFootprint: recorded basin footprint for a certain flow monitors (from dfmDetails, from fmData file)
    * dfStorms: a pandas dataframe containing all the information about storms and the gross and net volumes of I&I for that storm    
OUTPUTS:
    * rdii: rain dependent I&I, measured as gallons of I&I per in per in-mi of pipe'''
def rdiiRanking(basinFootprint,dfStorms):
    netIIVol = dfStorms.loc[:,'Net Vol'].values # MG
    eventRT = dfStorms.loc[:,'Event Rain'].values # in
    rdii = 1e6 * netIIVol / eventRT / basinFootprint #gal/in/in-mi
    dfStorms['RDII'] = rdii
    return(dfStorms)
