#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May  9 16:44:16 2017

@author: fleischer
"""
import pandas as pd
import numpy as np
import seaborn as sns
from astral import *

def firstAndLastLight(data, threshold_list, resamp=False):
    ''' firstAndLastLight(data, threshold_list, resamp=False) applies all thresholds in the list to each unique person-day in the data, finding the first and last times as well as total times light intensity is above those thresholds for any non-zero number.  A 0 threshold is a request to calc amount of time spent at 5 lux and under.  Time resampling of the data is done if resamp is of the form [func name,'time'], such as [np.mean,'5T'] or [np.max,'15T'].'''
    ids = data.UID.unique()
    firstlight = []
    lastlight = []
    min2fl = []
    min2ll = []
    timabove = []
    whoswatch = []
    watchperiod = []
    thresholds = []
    datelist = []
    grouplist = []

    for id in ids:
            print(id)
            these_rows = (data.UID == id) & (data['Interval Status'].isin(['ACTIVE','REST'])) & np.logical_not(data['Off-Wrist Status'])
            
            if these_rows.sum() == 0:
                print("OOOPS!!#!#! "+id+" has no ACTIVE rows")
                
                
            daysofdata = set( data[ these_rows ].index.date )
            
            if 'Group' in data.columns:
                group = data[data.UID == id].iloc[0,:].Group
            elif 'Season' in data.columns:
                group = data[data.UID == id].iloc[0,:].Season
            else:
                print("OOOPS!!#!  No group variable??")
                raise ValueError
                
            for a_day in daysofdata:
                nextday = a_day + pd.tseries.offsets.Day()
                nextday = nextday.date().isoformat()
                thisday = a_day.isoformat()
                daylight = data['White Light'][these_rows][thisday + ' 04:00:00' : nextday + ' 03:59:00']
                datelist.append(a_day)
                grouplist.append(group)
                if resamp:
                    daylight = daylight.resample(resamp[1]).apply(resamp[0]) 
                for a_thresh in threshold_list:                                  
                    thresholds.append(a_thresh)
                    if a_thresh==0:
                        abovethresh = daylight.index[ daylight < a_thresh+3]
                    else:
                        abovethresh = daylight.index[ daylight > a_thresh]
                    if len(daylight)>15: # let's make sure we have at least 15min of daytime to work with
                        # sometimes the index skips a few minutes here and there... this might be due to the Interval Status
                        # so we need a way to find the true period in this noisy data...  
                        dperiod = pd.Timedelta(np.min(daylight.index[1:15]-daylight.index[0:14])) # this is the update rate of the watch
                        timeabove = len(abovethresh) * dperiod 
                    else:
                        dperiod = 0
                        timeabove = pd.Timedelta('0 seconds')                        
                    timabove.append(timeabove)
                    watchperiod.append(dperiod)
                    try:
                        timelight = abovethresh[-1] # last time is above threshold
                        mins4am = (timelight.time().hour - 4) * 60 + timelight.time().minute
                        if mins4am<0: # if after midnight, then value above is negative
                            mins4am += 24*60 # fix by adding 24 hours to it
                    except IndexError: # there is no above threshold level all day long
                        timelight = np.nan
                        mins4am = np.nan
                    lastlight.append(timelight)
                    min2ll.append(mins4am)
                    try:
                        timelight = abovethresh[0] # first time is above threshold
                        mins4am = (timelight.time().hour - 4) * 60 + timelight.time().minute
                        if mins4am<0: # if after midnight, then value above is negative
                            mins4am += 24*60 # fix by adding 24 hours to it
                    except IndexError: # there is no above threshold level all day long
                        timelight = np.nan
                        mins4am = np.nan
                    firstlight.append(timelight)
                    min2fl.append(mins4am)
                    whoswatch.append(id)
                    #print("{} {} {} of 0-lux with period {}\n".format(id,a_day,len(daylight[daylight==0])*dperiod,dperiod))
                
                #print( len( whoswatch), len(lastlight), len(firstlight), len(min2ll), len(min2fl))
    return pd.DataFrame( {'UID': whoswatch, 'Date': datelist, 'Threshold': thresholds,
                          'Last Light': lastlight, 'Mins to LL from 4AM': min2ll,
                          'First Light': firstlight, 'Mins to FL from 4AM': min2fl,
                          'Time above threshold': timabove, 
                          'Minutes above threshold': [ el.total_seconds()/60.0 for el in timabove],
                          'Group': grouplist,
                          'Watch period': watchperiod 
                         } )
#%%

def add_astral_data(timingData):

    
    a = Astral()
    tobaloc = Location(('Ingenerio Juarez','Formosa Province, Argentina',  -23.0 - 47.0/60.0, - 61.0 - 48.0/60.0, 'America/Cordoba', 60))
    studloc = a['Seattle']
    daymins = []
    dawns = []
    dusks = []
    moon = []
    for row in range(len(timingData)):
        entry = timingData.iloc[row,:]
        day = entry.iloc[0].date()
    
        if pd.isnull(day): # handle the not-a-time missing date elements
            daymins.append(np.NaN)
            dawns.append(pd.NaT)
            dusks.append(pd.NaT)
            moon.append(np.NaN)
            continue
        
        if entry['UID'].startswith('toba'):
            sundata =  tobaloc.sun(date=day)
        else:
            sundata =  studloc.sun(date=day)
        dt = sundata['sunrise']-sundata['sunset']
        daymins.append( dt.seconds/60.0 )
        dawns.append(sundata['sunrise'])
        dusks.append(sundata['sunset'])
        moon.append(a.moon_phase(day))
    
    timingData['Daylight minutes'] = daymins
    timingData['Sunrise'] = dawns
    timingData['Sunset'] = dusks
    timingData['Moon phase'] = moon
    
    return timingData


def firstAndLastActivity(data, threshold_list, resample=False):
    ids = data.UID.unique()
    firstlight = []
    lastlight = []
    min2fl = []
    min2ll = []
    timabove = []
    whoswatch = []
    watchperiod = []
    thresholds = []

    for id in ids:
            print(id)
            these_rows = (data.UID == id) & (data['Interval Status'] == 'ACTIVE')
            daysofdata = set( data[ these_rows ].index.date )
            for a_day in daysofdata:
                nextday = a_day + pd.tseries.offsets.Day()
                nextday = nextday.date().isoformat()
                thisday = a_day.isoformat()
                daylight = data['Activity'][these_rows][thisday + ' 04:00:00' : nextday + ' 03:59:00']
                if resamp:
                    daylight = daylight.resample(resamp[1]).apply(resamp[0]) 
                for a_thresh in threshold_list:                                  
                    thresholds.append(a_thresh)
                    if a_thresh==0:
                        abovethresh = daylight.index[ daylight < a_thresh+3]
                    else:
                        abovethresh = daylight.index[ daylight > a_thresh]
                    if len(daylight)>15: # let's make sure we have at least 15min of daytime to work with
                        # sometimes the index skips a few minutes here and there... this might be due to the Interval Status
                        # so we need a way to find the true period in this noisy data...  
                        dperiod = pd.Timedelta(np.median(daylight.index[1:15]-daylight.index[0:14])) # this is the update rate of the watch
                        timeabove = len(abovethresh) * dperiod 
                    else:
                        dperiod = 0
                        timeabove = pd.Timedelta('0 seconds')                        
                    timabove.append(timeabove)
                    watchperiod.append(dperiod)
                    try:
                        timelight = abovethresh[-1] # last time is above threshold
                        mins4am = (timelight.time().hour - 4) * 60 + timelight.time().minute
                        if mins4am<0: # if after midnight, then value above is negative
                            mins4am += 24*60 # fix by adding 24 hours to it
                    except IndexError: # there is no above threshold level all day long
                        timelight = np.nan
                        mins4am = np.nan
                    lastlight.append(timelight)
                    min2ll.append(mins4am)
                    try:
                        timelight = abovethresh[0] # first time is above threshold
                        mins4am = (timelight.time().hour - 4) * 60 + timelight.time().minute
                        if mins4am<0: # if after midnight, then value above is negative
                            mins4am += 24*60 # fix by adding 24 hours to it
                    except IndexError: # there is no above threshold level all day long
                        timelight = np.nan
                        mins4am = np.nan
                    firstlight.append(timelight)
                    min2fl.append(mins4am)
                    whoswatch.append(id)
                    #print("{} {} {} of 0-lux with period {}\n".format(id,a_day,len(daylight[daylight==0])*dperiod,dperiod))
                
                #print( len( whoswatch), len(lastlight), len(firstlight), len(min2ll), len(min2fl))
    return pd.DataFrame( {'UID': whoswatch, 'Threshold': thresholds,
                          'Last Activity': lastlight, 'Mins to LA from 4AM': min2ll,
                          'First Activity': firstlight, 'Mins to FA from 4AM': min2fl,
                          'Time above threshold': timabove, 
                          'Minutes above threshold': [ el.total_seconds()/60.0 for el in timabove],
                          'Watch period': watchperiod 
                         } )

