import pickle
import time

from os import makedirs
import pandas as pd

from flowmeterAnalysis import readFiles
from flowmeterAnalysis import plotting

homeDir = 'P:\\PW-WATER SERVICES\\TECHNICAL SERVICES\\Anna'
pickleLocation = homeDir + '\\2018\\Python Objects\\'
fmdataFile = homeDir + '\\FMdata.csv'
saveDir = homeDir + '\\2018\\Yearly Report'
upstreamFile = homeDir + '\\FMtoUpstream.csv'

dfUpstream = readFiles.readUpstreamFile(
    filename = upstreamFile)
folders, txt, csv = readFiles.findTextFiles(saveDir)

tic = time.process_time()
'''
basinDryWeather is a dictionary with flow monitors names as keys that
    contain the following dictionaries:
    * 'Weekday' : {
                    'd/D' : a numpy array
                    'Gross Q' : a pandas series (index: datetime, values: Q)
                    'DataFrame' : pandas data frame (index:time, columns: date,
                                  values: q)
                    'Gross Diurnal' : pandas series (index: time, values: Q)
                    'Net Diurnal' : pandas series (index: time, values: Q)
                    }
    * 'Weekend' : {
                    'd/D' : a numpy array
                    'Gross Q' :
                    'DataFrame' : pandas data frame (index:time, columns: date,
                                  values: q)
                    'Gross Diurnal' : pandas series (index: time, values: Q)
                    'Net Diurnal' : pandas series (index: time, values: Q)
                    }
    * 'Overall' : {
                    'd/D' : a numpy array
                    'Base Infiltration' : numpy float
                    }'''
with open(pickleLocation + 'basinDryWeather.pickle', 'rb') as handle:
    basinDryWeather = pickle.load(handle)
    
'''
stormsDict is a dictionary with flow monitors as keys that contain a pandas
    dataframe, dfStorms, with storm start times as indices and the following 
    columns:
    * Storm RT : storm rain total in inches
    * Storm Dur : storm duration in hours
    * Event RT : event rain total in inches
    * Event Dur : event duration in hours
    * Gross Vol: gross I&I volume in MG
    * Net Vol : net I&I volume in MG
    * Capt Coeff : capture coefficient (vol I&I/vol rainfall)
    * RDII : rain dependent I&I ranking (gal/in(rain)/in-mi(pipe))'''
with open(pickleLocation + 'stormsDict.pickle', 'rb') as handle:
    stormDict = pickle.load(handle)
    
'''gageStorms is a dictionary with rain gages as keys that contain a pandas 
    dataframe, dfStorms, with storm start tiems as indices and the following
    columns:
    * Storm RT : storm rain total in inches
    * Storm Dur : storm duration in hours
    * Event RT : event rain total in inches
    * Event Dur : event duration in hours'''
with open(pickleLocation + 'gageStorms.pickle', 'rb') as handle:
    gageStorms = pickle.load(handle)
toc = time.process_time()
print(toc - tic)

fitDict = {}
tic = time.process_time()
for fmname in stormDict:
    if fmname not in folders:
        #make the directory
        makedirs(saveDir + "\\" + fmname)
    plotting.bulletGraph_fms(
        fmname = fmname, 
        basinDryWeather = basinDryWeather, 
        stormDict = stormDict, 
        saveDir = saveDir)
    plotting.pltDryGrossQ(
        basinDryWeather = basinDryWeather,
        fmname = fmname,
        saveDir = saveDir)
    plotting.pltDryNetQ(
        basinDryWeather = basinDryWeather,
        fmname = fmname,
        saveDir = saveDir)
    plotting.pltDrydD(
        basinDryWeather = basinDryWeather,
        fmname = fmname,
        saveDir = saveDir)
    plotting.netii_bar(
        fmname = fmname,
        data = stormDict[fmname],
        topNum = 12,
        yLims = (.01,50),
        saveDir = saveDir)
    fitDict[fmname] = plotting.df_rainComp(
        stormDict = stormDict, 
        fmname = fmname, 
        col = 'Net Vol', 
        ylabel =  'Net I&I (MG)',
        fit = True,
        saveDir = saveDir,
        fitData = fitDict)
    usfmList = readFiles.findUpstreamFMs(
        df = dfUpstream, 
        fmname = fmname)
    if not usfmList:
        pass
    else:
        plotting.plotUpstreamFlows(
            fmname = fmname, 
            basinDryWeather = basinDryWeather, 
            usfmList = usfmList,
            saveDir = saveDir)
toc = time.process_time()
print(toc - tic)