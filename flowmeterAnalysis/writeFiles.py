import pandas as pd
from flowmeterAnalysis import flowMonitor as fm

def createSanitarycsv(snormWKD,snormWKE,dfWKD, dfWKE, gwi,saveDir,fmName):
    df_csv = pd.DataFrame(index=snormWKD.index,columns=['Weekday','Weekend','GWI','Weekday Mean','Weekend Mean'])
    df_csv['Weekday'] = snormWKD
    df_csv['Weekend'] = snormWKE
    sanMeanWKD = fm.findSanMean(df=dfWKD,gwi=gwi)
    sanMeanWKE = fm.findSanMean(df=dfWKE,gwi=gwi)
    df_csv.iloc[0,2:]=[gwi,sanMeanWKD,sanMeanWKE]

    df_csv.index.name = 'Time'
    saveName = "\\" + fmName + '_sanitaryNorm.csv'
    df_csv.to_csv(saveDir+saveName)
    return(df_csv)

def createMeanscsv(dfWKD,dfWKE,fmname,saveDir):
    df = fm.diurnals(dfWKD=dfWKD,dfWKE=dfWKE)
    saveName = "\\" + fmname + '_meanFlows.csv'
    df.to_csv(saveDir+saveName)
    return(df)