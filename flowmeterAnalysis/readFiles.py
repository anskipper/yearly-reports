import pandas as pd
import numpy as np
from os import walk

def readFlowviewcsv(filename):
    df = pd.read_csv(filename,
        index_col = 0,
        header = 2,
        usecols = [0, 1, 2, 3],
        names = ['Datetime','y (in)','v (ft/s)','Q (MGD)'],
        parse_dates = True,
        infer_datetime_format = True,
        dtype = {
            'y (in)' : np.float64,
            'v (ft/s)' : np.float64,
            'Q (MGD)' : np.float64
        })
    df.index = pd.to_datetime(df.index)
    return(df)

def findDiameter(filename, fmname):
    df = pd.read_csv(filename,
        index_col=0,
        sep='\t')
    diameter = df.loc[fmname,'Diameter']
    return(diameter)

#input diameter of pipe and water level (h) in feet; returns cross sectional area in ft**2
def fluidArea(D, h):
    r = D/2.0
    area = r**2*np.arccos((r-h)/r)-(r-h)*np.sqrt(2*r*h-h**2)
    return(area)

def formatFlowFile(df, diameter_in, fmname):
    if df['sdepth (in)'].isna().all():
        pass
    else:
        diameter_ft = diameter_in/12.0
        depth = df.loc[:, 'sdepth (in)'].values/12.0
        area = fluidArea(
            D = diameter_ft, 
            h = depth)
        conv = 7.48 * 3600 * 24/1e6
        df['Q (MGD)'] = conv * area * df['v (ft/s)']
    return(df)

def readRGfile(filename):
    df = pd.read_csv(filename,
        index_col = 0,
        sep = '\t')
    return(df)

def findRainGage(filename, fmName):
    df = readRGfile(filename = filename)
    rg = df.loc[fmName][0]
    return(rg)

def constructdtypes(useColList, col_dtypes):
    dtypes = {}
    for column, dtype in zip(useColList,col_dtypes):
        dtypes[column] = dtype
    return(dtypes)

def readRaintxt(filename, useColList, col_dtypes):
    dtypes = constructdtypes(
        useColList = useColList[1:],
        col_dtypes = col_dtypes)
    df = pd.read_csv(filename,
        sep = '\t',
        usecols = useColList,
        index_col = 0,
        parse_dates = True,
        infer_datetime_format = True,
        dtype = dtypes)
    df.index = pd.to_datetime(df.index)
    return(df)

def readFMdetails(filename):
    #column names: 'Rain Gage', 'Diameter', 'Linear Feet', 'Basin Area (Ac)', 'Basin Footprint (in-mi)', 'Total Footage (LF)'
    df = pd.read_csv(filename,
        index_col=0,
        dtype = {
            'Flow Monitor' : 'object',
            'Rain Gage' : 'object',
            'Diameter' : np.float64,
            'Linear Feet' : np.float64,
            'Basin Area (Ac)' : np.float64,
            'Bassin Footprint (in-mi)' : np.float64,
            'Total Footage (LF)' : np.float64
        })
    df[df==9999.0] = float('NaN')
    return(df)

# reorganize the data such that the index is time of day, the columns represent different days, and the values are whichever is specified (e.g., Q)
def reorganizeByTime(df, colVal):
    df['date']=df.index.date
    df['time']=df.index.time
    df = df.pivot(
        index = 'time',
        columns = 'date',
        values = colVal)
    return(df)

def weekdaySeries(df, colVal, returnType, weather):
    if returnType == 'weekday':
        mask = ((df.index.dayofweek < 5) 
            and (df['Weather'] == weather))
    elif returnType == 'weekend':
        mask = ((df.index.dayofweek >= 5) 
        and (df['Weather'] == weather))
    else:
        raise AttributeError(returnType)
    s = df.loc[mask, colVal]
    return(s)

def findTextFiles(readDir):
    d = []
    f = []
    t = []
    c = []
    for (root, dirs, files) in walk(readDir, topdown=True):
        d.extend(dirs)
        f.extend(files)
        for x in f:
            if x.endswith('.txt'):
                t.extend([x])
            elif x.endswith('csv'):
                 c.extend([x])                   
        d = sorted(d)
        t = sorted(t)
        c = sorted(c)
        return(d, t, c)

# give a list of files, find a particular one that starts with the key
def findFileInList(fileList, key):
    for f in fileList:
        if f.startswith(key):
            return(f)

def readTotalFlow(filename):
    df= pd.read_csv(filename,
        index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.time
    return(df)

def readUpstreamFile(filename):
        df = pd.read_csv(filename,
        index_col=0)
        return(df)

# locates the flow monitor in the file, finds the upstream flow monitors (if they exist), and returns a list of those flow monitors as strings
def findUpstreamFMs(df, fmname):
    usfms = df.loc[fmname, 'USFM']
    if usfms=='None':
        usfms = [] #return an empty list
    else:
        usfms = usfms.split(',') # return the list of upstream flow monitors   
    return(usfms)

def readStormData(fmname, flowDir):
    stormFile = flowDir + '\\' + fmname + '\\' + fmname + '_stormData.csv'
    # does the file exist?
    dfStorm = pd.read_csv(stormFile,
        index_col=0)
    sGrossII = dfStorm.loc[:, 'Gross Vol']
    return(dfStorm,sGrossII)
