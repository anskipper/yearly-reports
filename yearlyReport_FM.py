import time
import numpy as np

from os import walk
from os import makedirs
from datetime import datetime
from datetime import timedelta
import pickle

from flowmeterAnalysis import flowMonitor
from flowmeterAnalysis import readFiles

##### SET DIRECTORIES, FILES, ETC. #####
homeDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
flowDir = homeDir + '\\2018\\Big Creek Data'
gageFile = homeDir + '\\2018\\Rain\\FMtoRG.txt'
dailyFile = homeDir + '\\2018\\Rain\\RG_daily_20180101-20190331.txt'
hourlyFile = homeDir + '\\2018\\Rain\\RG_hourly_20180101-20190331.txt'
upstreamFile = homeDir + '\\FMtoUpstream.csv'
fmdataFile = homeDir + '\\FMdata.csv'

##### set variables #####
rainThresh = 0.1
dfFlows = {}
basinDryWeather = {}
analysisDates = (datetime(2018,1,1),datetime(2018,12,31))
rgList = ['BCRG01','BCRG02','BCRG03','BCRG04','JCRG03']
rain_dtypes = []
for k in range(0,len(rgList)):
    rain_dtypes.append(np.float64)
gageStorms = {}
stormsDict = {}
systemII = {}

##### set test values #####
fmname = 'BC19'
flowFile = flowDir + '\\BC19_28660533.csv'

##### read in relevant files as dataframes #####
# DAILY RAIN TOTALS
dailyUseCols = rgList.copy()
dailyUseCols.insert(0, 'Date')
# DAILY RAIN FILE
dfDaily = readFiles.readRaintxt(
    filename = dailyFile,
    useColList = dailyUseCols,
    col_dtypes = rain_dtypes)
# slice with analysis dates
dfDaily = dfDaily.loc[analysisDates[0].date():analysisDates[1].date()]
# HOURLY RAIN FILE
hourlyUseCols = rgList.copy()
hourlyUseCols.insert(0, 'DateTime')
dfHourly = readFiles.readRaintxt(
    filename = hourlyFile,
    useColList = hourlyUseCols,
    col_dtypes = rain_dtypes)
# slice  with analysis dates
dfHourly = dfHourly.loc[analysisDates[0]:analysisDates[1]+timedelta(hours=23), :]
# DETAILS ABOUT FLOW MONITORS
dfmDetails = readFiles.readFMdetails(
    filename=fmdataFile)
# UPSTREAM FLOW MONITORS
dfUpstream = readFiles.readUpstreamFile(
    filename = upstreamFile)

# find the flow files
flow_folders,flow_txt,flow_csv = readFiles.findTextFiles(readDir=flowDir)

tic = time.process_time()
 # DRY WEATHER
for fmData in flow_csv:
    fmname = fmData.split('_')[0]
    flowFile = flowDir + "\\" + fmData
    # read in the flow file as a data frame
    dfFlow = readFiles.readFlowviewcsv(filename = flowFile)
    dfFlows[fmname] = dfFlow.loc[analysisDates[0]:analysisDates[1] + timedelta(hours=23,minutes=45), :]
    ######## DRY WEATHER ##############
    basinDryWeather[fmname] = flowMonitor.dryWeather(
        dfFlow = dfFlows[fmname], 
        fmname = fmname, 
        dfDailyRain = dfDaily, 
        dfmDetails = dfmDetails, 
        analysisDates = analysisDates,
        rainThresh = rainThresh)
toc = time.process_time()
print(toc - tic)

tic = time.process_time()
# get net dry Q
for fmname in basinDryWeather:
    basinDryWeather = flowMonitor.netDryQ(
        basinDryWeather = basinDryWeather,
        dfUpstream = dfUpstream,
        fmname = fmname)
toc = time.process_time()
print(toc - tic)

########### WET WEATHER ############
tic = time.process_time()
for fmname in basinDryWeather:
    meanFile = homeDir + '\\2018\\Big Creek' + '\\' + fmname + '\\' + fmname + '_meanFlows.csv' 
    gageStorms, stormsDict[fmname], systemII[fmname] = flowMonitor.grossII(
        dfFlow = dfFlows[fmname], 
        gagename = dfmDetails.loc[fmname, 'Rain Gage'], 
        dfDaily = dfDaily, 
        dfHourly = dfHourly,
        fmname = fmname, 
        D = dfmDetails.loc[fmname, 'Diameter'], 
        dryWeatherDict = basinDryWeather[fmname],
        gageStorms = gageStorms, 
        meanFile = meanFile)
toc = time.process_time()
print(toc - tic)

tic = time.process_time()
for fmname in stormsDict:
    stormsDict[fmname], systemII[fmname]['Net'] = flowMonitor.netII(
        fmname = fmname, 
        systemGrossQ = systemII, 
        dfUpstream = dfUpstream, 
        dfDaily = dfDaily,
        dfHourly = dfHourly, 
        gagename = dfmDetails.loc[fmname, 'Rain Gage'],
        stormsDict = stormsDict)
toc = time.process_time()
print(toc - tic)

tic = time.process_time()
for fmname in stormsDict:
    stormsDict[fmname] = flowMonitor.findCaptureCoeff(
        basinArea = dfmDetails.loc[fmname, 'Basin Area (Ac)'],
        dfStorms = stormsDict[fmname])
    stormsDict[fmname] = flowMonitor.rdiiRanking(
        basinFootprint = dfmDetails.loc[fmname, 'Basin Footprint (in-mi)'],
        dfStorms = stormsDict[fmname])
toc = time.process_time()
print(toc - tic)

# save basinDryWeather, stormsDict, and systemII using pickle
saveDir = homeDir + '\\2018\\Python Objects\\'
saveObjs = [basinDryWeather, stormsDict, systemII, gageStorms, dfFlows]
filenames = ['basinDryWeather','stormsDict','systemII', 'gageStorms', 'flowDict']

for saveObj, filename in zip(saveObjs,filenames):
    with open(saveDir + filename + '.pickle','wb') as handle:
        pickle.dump(saveObj, handle,
        protocol = pickle.HIGHEST_PROTOCOL)
