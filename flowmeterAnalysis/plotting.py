import numpy as np
import datetime as dt

import pandas as pd
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib

font = {'family' : 'DejaVu Sans',
        'weight' : 'normal',
        'size'   : 10}

matplotlib.rc('font', **font)

def prettyxTime(ax):
    ticks = ax.get_xticks()
    ax.set_xticks(np.linspace(ticks[0],24*3600,5))
    ax.set_xticks(np.linspace(ticks[0],24*3600,25),minor=True)

def constructDict(keyList, keyVals, dictionary = {}):
    for idx, key in enumerate(keyList):
        dictionary[key] = keyVals[idx]
    return(dictionary)

def removeNans(ser):
    return(ser.values[~np.isnan(ser.values)])

def bulletGraph_fms(fmname, basinDryWeather, stormDict, saveDir = []):
    # light yellow, light orange, red-orange
    palette = ['#fed98e', '#fe9929', '#cc4c02']
    metrics = ['d/D Dry', 'd/D Wet', 'Base Infil.','C Coeff']
    limits = [[0.3,0.45,1], [0.5,0.65,1], [0.25,0.5,1],  [0.05,0.1,1]]
    labels = ['Good', 'OK', 'Poor']
    # construct limit dictionary
    limitDict = constructDict(
        keyList = metrics,
        keyVals = limits)
    #find that data
    dD_dry = min(np.quantile(
                    basinDryWeather[fmname]['Overall']['d/D Dry'],
                    0.95),
                 1)
    dD_wet = min(np.quantile(
                    basinDryWeather[fmname]['Overall']['d/D Wet'],
                    0.95),
                 1)
    baseInfil = basinDryWeather[fmname]['Overall']['Base Infiltration']
    #RDII = stormDict[fmname]['RDII'].mean()
    cc = stormDict[fmname]['Capt Coeff'].mean()
    vals = [dD_dry, dD_wet, baseInfil, cc]
    # PLOTTING
    fig, axarr = plt.subplots(
        nrows = len(metrics),
        ncols = 1,
        sharex = True,
        figsize = (4,3))
    for metricIdx, metric in enumerate(metrics):
        h = limitDict[metric][-1] / 10
        ax = axarr[metricIdx]
        # format
        ax.set_aspect('equal')
        ax.set_yticks([1])
        ax.set_yticklabels([metric])
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        prev_limit = 0
        for limIdx, lim in enumerate(limitDict[metric]):
            ax.barh([1], 
                lim - prev_limit, 
                left = prev_limit, 
                height = h, 
                color = palette[limIdx])
            prev_limit = lim
        ax.barh([1], vals[metricIdx], color = 'xkcd:chocolate', height = h / 3)
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = saveDir + '\\' + fmname + '\\' + fmname + '_bullet.png'
        plt.savefig(saveName
            )
        plt.close(fig)

def dryBoxplots(fmname, data, ylabel, title, showyticks, 
                topLim, bottomLim, annotate, 
                saveDir = [], saveName = []):
    fig,ax = plt.subplots(figsize=(2.2,1.75))
    boxwidth = 0.3
    bp = ax.boxplot(data,
                   labels = ['WKD','WKE'],
                   patch_artist = True,
                   showfliers = False,
                   widths = boxwidth,
                   whis = [5,95],
                   showcaps = False)
    plt.setp(bp['boxes'],color = 'xkcd:clay', linewidth = 2.0)
    plt.setp(bp['whiskers'],color = 'xkcd:clay', linewidth = 2.0)
    plt.setp(bp['medians'],color = 'xkcd:charcoal', linewidth = 2.5)
    plt.setp(bp['caps'],color = 'xkcd:clay', linewidth = 3)
    # plot weekend and weekday differently
    colors = ['xkcd:clay', 'xkcd:white']
    for box, color in zip(bp['boxes'],colors):
        box.set(facecolor = color)
    ax.yaxis.grid(True, 
                  linestyle = '-',
                  which = 'major',
                  color = 'xkcd:warm grey',
                  alpha = 0.5)
    ax.set_ylim(top = topLim,
               bottom = min(bottomLim,0))
    ax.set_title(title)
    if showyticks:
        ax.set_ylabel(ylabel)
    else:
        plt.tick_params(
            axis = 'y',        # changes apply to the x-axis
            which = 'both',   # both major and minor ticks are affected
            left = True,       # ticks along the bottom edge are off
            right = False,     # ticks along the top edge are off
            labelleft = False) # labels along the bottom edge are off
    if annotate:
        for values in data:
            labelNums = np.quantile(values,[0.05,0.5,0.95])
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = saveDir + '\\' + fmname + '\\' + fmname + '_' + saveName + '.png'
        plt.savefig(saveName)
        plt.close(fig)            
    plt.show()

def pltDryGrossQ(basinDryWeather,fmname,saveDir = []):
    # gross Q
    grossQ_wkd = removeNans(basinDryWeather[fmname]['Weekday']['Gross Q'])
    grossQ_wke = removeNans(basinDryWeather[fmname]['Weekend']['Gross Q'])
    dryBoxplots(
        fmname = fmname,
        data = [grossQ_wkd, grossQ_wke],
        ylabel = 'Q (MGD)',
        title = 'Gross Q',
        showyticks = True,
        topLim = round(1.5 * max(
            np.quantile(grossQ_wkd,0.95),
            np.quantile(grossQ_wke,0.95)),1),
        bottomLim = round(1.2 * min(
            np.quantile(grossQ_wkd,0.05),
            np.quantile(grossQ_wke,0.05)),1),
        annotate = False,
        saveDir = saveDir, 
        saveName = 'grossQ')
        
def pltDryNetQ(basinDryWeather,fmname,saveDir = []):
    # net Q
    netQ_wkd = removeNans(basinDryWeather[fmname]['Weekday']['Net Q'])
    netQ_wke = removeNans(basinDryWeather[fmname]['Weekend']['Net Q'])
    dryBoxplots(
        fmname = fmname,
        data = [netQ_wkd, netQ_wke],
        ylabel = 'Q (MGD)',
        title = 'Net Q',
        showyticks = True,
        topLim = round(1.5 * max(
            np.quantile(netQ_wkd,0.95),
            np.quantile(netQ_wke,0.95)),1),
        bottomLim = round(1.2 * min(
            np.quantile(netQ_wkd,0.05),
            np.quantile(netQ_wke,0.05)),1),
        annotate = False,
        saveDir = saveDir, 
        saveName = 'netQ')
        
def pltDrydD(basinDryWeather,fmname,saveDir = []):        
    # d/D
    dD_wkd = basinDryWeather[fmname]['Weekday']['d/D']
    dD_wke = basinDryWeather[fmname]['Weekend']['d/D']
    dryBoxplots(
        fmname = fmname,
        data = [dD_wkd, dD_wke],
        ylabel = 'd/D',
        title = 'Dry Capacity',
        showyticks = True,
        topLim =  round(1.5 * max(
            np.quantile(dD_wkd,0.95),
            np.quantile(dD_wke,0.95)),1),
        bottomLim = 0,
        annotate = False,
        saveDir = saveDir, 
        saveName = 'dD')

def netii_bar(fmname, data, topNum, yLims, saveDir = []):
    df = data.copy()
    # sort in descending order of net I&I
    df.sort_values(
        by='Net Vol',
        ascending=False,
        inplace=True)
    netii = df['Net Vol']
    # take the top number of storms, e.g., 20
    ii = netii[:topNum]
    ii = ii.sort_index(ascending = True)    
    # assign color
    colors = []
    for date in ii.index:
        if ((date >= dt.datetime(date.year,5,1)) 
            & (date < dt.datetime(date.year,10,15))):
            color = 'xkcd:seafoam blue'
        else:
            color = 'xkcd:stormy blue'
        colors.append(color)
    # format the index
    ii.index = ii.index.strftime('%b %d')
    # plot
    fig,ax = plt.subplots(figsize = (7.5,2))
    barPlot = ii.plot.bar(
                     ax = ax,
                     color = colors)
    #ax.xaxis.set_major_formatter(dates.DateFormatter('%b %d'))
    ax.set_ylabel('Net I&I (MG)')
    ax.set_yscale('log')
    ax.set_ylim(top = yLims[1],
                bottom = yLims[0])
    ax.yaxis.grid(True, 
                  linestyle = '-',
                  which = 'major',
                  color = 'xkcd:charcoal',
                  alpha = 0.4)
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = saveDir + '\\' + fmname + '\\' + fmname + '_netIIVol_bar.png'
        plt.savefig(saveName)
        plt.close(fig)

def df_rainComp(stormDict, fmname, col, ylabel,
             saveDir = [], fitData = {}, fit = True):   
    df = stormDict[fmname].copy()
    df = df.loc[df.loc[:,col] > 0]
    colors = []
    summer_ii = []
    summer_rain = []
    winter_ii = []
    winter_rain = []
    for date, value, rain in zip(
        df.index, 
        df[col].values, 
        df['Storm Rain'].values):
        if ((date >= dt.datetime(date.year,5,1)) 
            & (date < dt.datetime(date.year,10,15))):
            color = 'xkcd:seafoam blue'
            summer_ii.append(value)
            summer_rain.append(rain)
        else:
            color = 'xkcd:stormy blue'
            winter_ii.append(value)
            winter_rain.append(rain)
        colors.append(color)
    fig,ax = plt.subplots(figsize = (7.5,2))
    # plot data points
    ax.scatter(
        x = df['Storm Rain'].values,
        y = df[col].values,
        c = colors,
        alpha = 0.8)
    ax.set_yscale('linear')
    ax.set_ylabel(ylabel)
    topLim = round(1.2 * max(df[col].values),1)
    ax.set_ylim(top = topLim,
                bottom = 0)
    ax.set_xscale('linear')
    ax.set_xlabel('Rain (in)')
    rightLim = round(1.2 * max(df['Storm Rain'].values))
    ax.set_xlim(right = rightLim,
                left = 0)
    if fit:
        # summer fit
        m_summer, b_summer, r_summer, p, err = stats.linregress(
            x = summer_rain, 
            y = summer_ii)
        # winter fit
        m_winter, b_winter, r_winter, p, err = stats.linregress(
            x = winter_rain, 
            y = winter_ii)
        # update dictionary
        fitData[fmname] = {
            'Winter' : {
                'slope' : m_winter,
                'intercept' : b_winter,
                'r-squared' : r_winter},
            'Summer' : {
                'slope' : m_summer,
                'intercept' : b_summer,
                'r-squared' : r_summer}
            }
        # plot fits
        x = np.array([0,rightLim])
        y_summer = m_summer * x + b_summer
        y_winter = m_winter * x + b_winter
        ax.plot(x,
               y_summer,
               linewidth = 2.0,
               linestyle = '-',
               color = 'xkcd:seafoam blue',
               label = 'summer')
        ax.plot(x,
               y_winter,
               linewidth = 2.0,
               linestyle = '-',
               color = 'xkcd:stormy blue',
               label = 'winter')
        ax.legend(loc = 'upper left')
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = saveDir + '\\' + fmname + '\\' + fmname + '_netIIvsi.png'
        plt.savefig(saveName)
        plt.close(fig)
    return(fitData)

def plotUpstreamFlows(fmname, basinDryWeather, usfmList, saveDir = []):
    fmMean = basinDryWeather[fmname]['Weekday']['DataFrame'].mean(axis = 1)
    df_down = pd.DataFrame(
        data = {fmname: fmMean},
        index = fmMean.index)
    data = {}
    colors = sns.color_palette('Set2',
                               len(usfmList))[::-1]
    for usfm in usfmList:
        data[usfm] = basinDryWeather[usfm]['Weekday']['DataFrame'].mean(axis = 1)
    df_up = pd.DataFrame(data = data, index = fmMean.index)
    # plot
    fig, ax = plt.subplots(figsize = (7.5,3))
    df_up.plot.area(ax = ax,
             stacked = True,
             color = colors)
    ax.set_ylabel('Q (MGD)')
    prettyxTime(ax)
    df_down.plot(kind = 'line',
              color = 'xkcd:charcoal',
              linestyle = ':',
                 linewidth = 2.0,
                ax = ax)
    ax.set_ylim(top = 1.2 * fmMean.max())
    ax.set_xlabel('Time of Day')
    ax.legend(loc = 'lower right')
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = saveDir + '\\' + fmname + '\\' + fmname + '_wUpstream.png'
        plt.savefig(saveName)
        plt.close(fig)

def cumulativeHist(fmname, data, nbins, saveDir = []):
    maxBinEdge = 1.1 * round(data.max(),2)
    minBinEdge = np.min(1.1 * round(data.min(),2), 0)
    binEdges = np.linspace(minBinEdge, maxBinEdge, nbins)
    fig,ax = plt.subplots(figsize = (3,4))
    cc_hist = ax.hist(x = data,
                  bins = binEdges,
                 facecolor = 'xkcd:light grey',
                 edgecolor = 'xkcd:charcoal',
                 density = True,
                 cumulative = True,
                 align = 'right')
    ax.yaxis.grid(True, 
                  linestyle = '-',
                  which = 'major',
                  color = 'xkcd:charcoal',
                  alpha = 0.4)
    ax.set_xlabel('Net Q (MGD)')
    ax.set_title(fmname)
    ax.set_ylabel('% Less Than')
    for patch, binEdge in zip(cc_hist[2],cc_hist[1][1:]):
        if binEdge < 0:
            patch.set_fc(color = 'xkcd:cornflower')
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = (saveDir + '\\' + fmname + '\\' 
                    + fmname + '_cumulativeHist.png')
        plt.savefig(saveName)
        plt.close(fig)

def uptime(flowDict, col, saveDir = []):
    percentRunning = []
    for fm in flowDict:
        df = flowDict[fm]
        percentRunning.append((len(flowDict[fm].index) 
                        - sum(np.isnan(flowDict[fm][col].values)))
                     /len(flowDict[fm].index))
    y = range(0,4 * len(percentRunning),4)
    leftLim = round(0.9 * min(percentRunning),1)
    xticks = list(np.arange(leftLim,1,0.1))
    xticks.append(1)
    fig, ax = plt.subplots(figsize=(2,10.5))
    ax.plot(percentRunning,
        y,
        marker = '.',
        markersize = 9,
        linewidth = 0,
        alpha = 0.7,
        color = 'xkcd:stormy blue')
    for xval, yval in zip(percentRunning, y):
        ax.plot([0, xval],[yval, yval],
            color = 'xkcd:stormy blue')
    plt.xticks(
        ticks = xticks)
    plt.yticks(
        ticks = y, 
        labels = list(flowDict.keys()))
    ax.xaxis.grid(
        True, 
        linestyle = '-',
        which = 'major',
        color = 'xkcd:charcoal',
        alpha = 0.4)
    ax.yaxis.grid(
        True, 
        linestyle = '-',
        which = 'major',
        color = 'xkcd:charcoal',
        alpha = 0.4)
    ax.set_xlim(left = leftLim)
    ax.invert_yaxis()
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = (saveDir + '\\' + 'uptime' 
                    + df.index[0].strftime('%m%d%y') + '-'
                    + df.index[-1].strftime('%m%d%y') 
                    + '.png')
        plt.savefig(saveName)
        plt.close(fig)

def colorbarSetup(df, colorbarFreq):
    # get colorbar data together
    if colorbarFreq == 'monthly':
        # assign colorbar values
        cv = np.linspace(
        df.index[0].month,
        df.index[-1].month,
        len(df.index))
        colorMap = matplotlib.cm.get_cmap(
            name = 'tab20b',
            lut = (list(set(df.index.month))[-1]
                  - list(set(df.index.month))[0] + 1))
        cbTicks = list(set(df.index.month))
        title = 'Month'
    elif colorbarFreq == 'daily':
        cv = np.linspace(
        df.index[0].day,
        df.index[-1].day,
        len(df.index))
        colorMap = matplotlib.cm.get_cmap(
            name = 'tab20b',
            lut = (list(set(df.index.day))[-1]
                  - list(set(df.index.day))[0] + 1))
        cbTicks = list(set(df.index.day))
        title = 'Day'
    elif colorbarFreq == 'yearly':
        cv = np.linspace(
        df.index[0].year,
        df.index[-1].year,
        len(df.index))
        colorMap = matplotlib.cm.get_cmap(
            name = 'tab20b',
            lut = (list(set(df.index.year))[-1]
                  - list(set(df.index.year))[0] + 1))
        cbTicks = list(set(df.index.year))
        title = 'Year'
    else:
        raise TypeError()
    colorBarAtt = {
        'cv' : cv,
        'cm' : colorMap,
        'ticks': cbTicks,
        'title': title}
    return(colorBarAtt)

def scattergraph(df, fmname, diameter, colorbarFreq, saveDir = []):
    # get colorbar data together
    colorBarAtt = colorbarSetup(df, colorbarFreq)
    fig, ax = plt.subplots(figsize=(5,4))
    ax.set_title(fmname)
    # scatter plot of data
    plt.scatter(
        df['v (ft/s)'].values,
        df['y (in)'].values,
        marker = '.',
        alpha = 1,
        c = colorBarAtt['cv'],
        cmap = colorBarAtt['cm'])
    # set up axis limits
    rightLim = np.ceil(df['v (ft/s)'].max())
    topLim = np.ceil(max(df['y (in)'].max(), diameter))
    ax.set_ylim(
        top = 1.1 * topLim,
        bottom = 0)
    ax.set_xlim(
        left = 0,
        right = 1.05 * rightLim)
    # plot colorbar
    cb = plt.colorbar(
        ticks = colorBarAtt['ticks'])
    cb.ax.set_title(colorBarAtt['title'])
    # plot diameter
    ax.plot(
        [0, 1.05 * rightLim],
        [diameter, diameter],
        linewidth = 2.0,
        linestyle = '-',
        color = 'xkcd:charcoal')
    ax.text(0.1, diameter + 0.02 * topLim, 
            s = 'Diameter = ' + str(diameter) + '"')
    ax.set_xlabel('Velocity (ft/s)')
    ax.set_ylabel('Depth (in)')
    ax.xaxis.grid(
        True, 
        linestyle = '-',
        which = 'major',
        color = 'xkcd:charcoal',
        alpha = 0.25)
    ax.yaxis.grid(
        True, 
        linestyle = '-',
        which = 'major',
        color = 'xkcd:charcoal',
        alpha = 0.25)
    plt.tight_layout()
    if not saveDir:
        plt.show()
    else:
        saveName = (saveDir + '\\' + fmname  + '\\' 
                    + fmname + 'scattergraph_' 
                    + df.index[0].strftime('%m%d%y') + '-'
                    + df.index[-1].strftime('%m%d%y') 
                    + '.png')
        plt.savefig(saveName)
        plt.close(fig)
