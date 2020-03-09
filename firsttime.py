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
    whoswatch = []
    watchperiod = []
    thresholds = []
    datelist = []
    grouplist = []
    totalact=[]
    tabvlight=[]
    tabvlightAM=[]
    tluxmin = []
    tluxminAM = []

    for uid in ids:
            print(uid)
            these_rows = (data.UID == uid) & (data['Interval Status'].isin(['ACTIVE','REST'])) & np.logical_not(data['Off-Wrist Status'])
            
            assert (these_rows.sum() > 0),"OOOPS!!#!#! "+uid+" has no ACTIVE rows"
                
                
            daysofdata = set( data[ these_rows ].index.date )
            
            if 'Group' in data.columns:
                group = data[data.UID == uid].iloc[0,:].Group
            elif 'Season' in data.columns:
                group = data[data.UID == uid].iloc[0,:].Season
            else:
                print("OOOPS!!#!  No group variable??")
                raise ValueError
                
            for a_day in daysofdata:
                nextday = a_day + pd.tseries.offsets.Day()
                nextday = nextday.date().isoformat()
                thisday = a_day.isoformat()
                daylight = data[these_rows][thisday + ' 04:00:00' : nextday + ' 03:59:00']['White Light']
                if resamp: # resample if the function argument is set
                    daylight = daylight.resample(resamp[1]).apply(resamp[0]) 
                
                # watch update period for todays data
                dperiod = daylight.index.to_series().diff().min() 
                dpmult = dperiod/pd.Timedelta('1 min') # multiplier to get lux-minutes later
                
                lxmin =  dpmult * daylight.sum()
                lxminAM = dpmult * daylight[:thisday + ' 12:00'].sum()
                
                for a_thresh in threshold_list:                                  
                    thresholds.append(a_thresh)
                    if a_thresh==0:
                        abovethresh = daylight.index[ daylight < 5] # 0 theshold is a request to calculate under 5 lux
                        abovethreshAM = daylight[:thisday + ' 12:00'].index[ daylight[:thisday + ' 12:00'] < 5]
                    else:
                        abovethresh = daylight.index[ daylight > a_thresh]
                        abovethreshAM = daylight[:thisday + ' 12:00'].index[ daylight[:thisday + ' 12:00'] > a_thresh]         
                    tabvlight.append( dperiod * len(abovethresh))
                    tabvlightAM.append( dperiod * len(abovethreshAM))
                    tluxmin.append( lxmin )
                    tluxminAM.append( lxminAM )
                    watchperiod.append(dperiod)
                    datelist.append(a_day)
                    grouplist.append(group)
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
                    whoswatch.append(uid)
                    #print("{} {} {} of 0-lux with period {}\n".format(uid,a_day,len(daylight[daylight==0])*dperiod,dperiod))
                
                #print( len( whoswatch), len(lastlight), len(firstlight), len(min2ll), len(min2fl))
    return pd.DataFrame( {'UID': whoswatch, 'Date': datelist, 'Threshold': thresholds,
                          'Last Light': lastlight, 'Mins to LL from 4AM': min2ll,
                          'First Light': firstlight, 'Mins to FL from 4AM': min2fl,
                          'Time above threshold': tabvlight, 'Time above threshold AM': tabvlightAM,
                          'Minutes above threshold': [ el.total_seconds()/60.0 for el in tabvlight],
                          'Minutes above threshold AM': [ el.total_seconds()/60.0 for el in tabvlightAM],
                          'Lux minutes': tluxmin, 'Lux minutes AM': tluxminAM,
                          'Group': grouplist,
                          'Watch period': watchperiod 
                         } )
