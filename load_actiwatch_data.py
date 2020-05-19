#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(summaryData, rawData) = load_actiwatch_data(path)
Loads in raw data from a Spectrum Actiwatch for all *.csv files in path. 
Returns a tuple consisting of two DataFrames, the first being the summary
and the second being the raw data.

Finds all .csv files in the directory given by the argument path.  Assumes 
each file represents a unique individual, and parses the filename to create a 
unique identifier for that individual. Loads the raw data into one panda
DataFrame, and the summary statistics into another. 

NOTE the summary statistics seems to be broken currently (in 2019). I believe that
updates to Philips Actiware changed the output format

Created on Tue May  2 09:17:37 2017

@author: fleischer
"""
import pandas
import glob
import sys

def load_actiwatch_data(path,uidprefix=''):
     
    if path[-1]!='/':    # make sure path has a trailing slash
        path = path + '/'        
    files = glob.glob(path+'*.csv') # gets all .csv filenames in directory 
    if not files: # let us know if there's no .csv files in path!
        print('Oops! No csv files in ' + path)
        raise OSError
    else:
        print('Found {} csv files in {}. Pass #1, raw data'.format(len(files),path)) 
        for _ in range(len(files)):
            sys.stdout.write('.')            
        sys.stdout.write('\n')

    frames = [] # list of data frames we will get from processing the files
    for afile in files:
        sys.stdout.write('.')
        sys.stdout.flush()
        with open(afile,'r') as f:
            # we need to skip any previous analysis that's at the top of the 
            # file and get to the raw data below it
            while True:
                currentFilePosition = f.tell()
                line = f.readline()
                if line == '': #empty line read if EOF
                    print('EOF without retrieving raw data: ' + afile)
                    break # get out of this loop so we can go on to next file
                cells = line.split(',') # comma seperated values (CSV)            
                columns = tuple(filter( None, [el.strip().strip('\"') for el in cells])) #need tuple because in python3 filter is evaluated in lazy fasion
                # DEBUG print len(columns),': ', columns
                # the raw data has a 12 element long header line:
                # Line , Date , Time , Off-wrist status , ....
                if ( (len(columns)==12) and (columns[0] == 'Line') ):
                    break
                    
            
            if line == '': #empty line read if EOF
                continue # go on to the next file
                
            # move the file pointer back to the beginning of the header line 
            # so we can read it in as a header for the DataFrame          
            f.seek(currentFilePosition) 
            
            # generate unique identifier for this individual based on filename
            # assumes filename has format: 
            # /path/to/file/UID_Month_Date_Year_Time_*.csv 
            UID = uidprefix + afile.split('/')[-1].split('_')[0]

            # grab the data, ignore the first column which just has line numbers
            # stuff the two Date/Time columns into a single Date variable 
            fileData = pandas.read_csv(f, index_col=False, usecols=columns[1:],
                                       parse_dates={'DateTime': [0,1]})
            fileData['UID'] = UID
            
            frames.append(fileData)
            
    rawWatchData = pandas.concat(frames) # make one big dataframe  
    rawWatchData.index = rawWatchData['DateTime']
    del rawWatchData['DateTime']
#%%
    print('\nPass #2, data summary') 
    for _ in range(len(files)):
        sys.stdout.write('.')
    sys.stdout.write('\n')

    frames = [] # list of data frames we will get from processing the files
    for afile in files:
        sys.stdout.write('.')
        sys.stdout.flush()
        with open(afile,'r') as f:
            # we need to skip to the summary statistics
            while True:
                summaryFilePosition = f.tell()
                line = f.readline()
                if line == '': #empty line read if EOF
                    print('EOF without retrieving summary data: ' + afile)
                    break # get out of this loop so we can go on to next file
                cells = line.split(',') # comma seperated values (CSV)            
                columns = tuple(filter( None, [el.strip().strip('\"') for el in cells])) #need tuple because in python3 filter is evaluated in lazy fasion
                # print len(columns), columns[0]
                # the raw data has a 35 element long header line:
                # Interval Type , Interval #, Start Date, ....
                if ( (len(columns)==35) and (columns[0] == 'Interval Type') ):
                    break
            
            if line == '': #empty line read if EOF
                continue # go on to the next file
                
            # advance to find out how many lines the summary includes
            # since we don't care about excluded intervals and they 
            # also don't have a full set of columns, we stop there
            nlines = 0
            toskip = [1] # we skip the line after the header, it has units
            while True:
                line = f.readline()
                if line == '': #empty line read if EOF
                    print('EOF without retrieving summary data: ' + afile)
                    break # get out of this loop so we can go on to next file
                cells = line.split(',') # comma seperated values (CSV)            
                columns = tuple(filter( None, [el.strip().strip('\"') for el in cells])) #need tuple because in python3 filter is evaluated in lazy fasion
                nlines += 1
                
                if columns:
                    if columns[0].find('Summary'):
                        toskip.append(nlines)
                    
                    if columns[0] == 'EXCLUDED':
                        break
            
            if line == '': #empty line read if EOF
                continue # go on to the next file
                
            # move the file pointer back to the beginning of the header line 
            # so we can read it in as a header for the DataFrame          
            f.seek(summaryFilePosition) 
            
            # generate unique identifier for this individual based on filename
            # assumes filename has format: 
            # /path/to/file/UID_Month_Date_Year_Time_*.csv 
            UID = uidprefix + afile.split('/')[-1].split('_')[0]

            # grab the data, ignore the first column which just has line numbers
            # stuff the two Date/Time columns into a single Date variable 
            fileData = pandas.read_csv(f, index_col=False, skiprows=toskip,
                                       nrows=nlines, skip_blank_lines=True)
            fileData['UID'] = UID
            
            frames.append(fileData)
    
    if frames:        
        summaryWatchData = pandas.concat(frames)
    else:
        summaryWatchData = None
    #%%        
            
    return (rawWatchData, summaryWatchData)
