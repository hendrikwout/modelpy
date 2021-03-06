# -*- coding: utf-8 -*-

import pandas as pd
import io
import os
import numpy as np
import datetime as dt
import sys
import pytz
import math

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--global-chunk')
    parser.add_argument('--first-station')
    parser.add_argument('--last-station')
    parser.add_argument('--dataset')
    parser.add_argument('--path-soundings')
    parser.add_argument('--experiments')
    parser.add_argument('--split-by',default=-1)# station soundings are split
                                                # up in chunks
    parser.add_argument('--station-chunk')
    parser.add_argument('--c4gl-path',default='')
    args = parser.parse_args()

if args.c4gl_path == '': 
    sys.path.insert(0, '/user/data/gent/gvo000/gvo00090/D2D/software/CLASS/class4gl/')
else:
    sys.path.insert(0, args.c4gl_path)
from class4gl import class4gl_input, data_global,class4gl
from interface_multi import stations,stations_iterator, records_iterator,get_record_yaml,get_records
from class4gl import blh,class4gl_input

# this is a variant of global run in which the output of runs are still written
# out even when the run crashes.

# #only include the following timeseries in the model output
# timeseries_only = \
# ['Cm', 'Cs', 'G', 'H', 'L', 'LE', 'LEpot', 'LEref', 'LEsoil', 'LEveg', 'Lwin',
#  'Lwout', 'Q', 'RH_h', 'Rib', 'Swin', 'Swout', 'T2m', 'dq', 'dtheta',
#  'dthetav', 'du', 'dv', 'esat', 'gammaq', 'gammatheta', 'h', 'q', 'qsat',
#  'qsurf', 'ra', 'rs', 'theta', 'thetav', 'time', 'u', 'u2m', 'ustar', 'uw',
#  'v', 'v2m', 'vw', 'wq', 'wtheta', 'wthetae', 'wthetav', 'wthetae', 'zlcl']



EXP_DEFS  =\
{
  'NOAC':    {'sw_ac' : [],'sw_ap': True,'sw_lit': False},
  'ADV':{'sw_ac' : ['adv',],'sw_ap': True,'sw_lit': False},
  'W':  {'sw_ac' : ['w',],'sw_ap': True,'sw_lit': False},
  'AC': {'sw_ac' : ['adv','w'],'sw_ap': True,'sw_lit': False},
}


#SET = 'GLOBAL'
SET = args.dataset

if 'path-soundings' in args.__dict__.keys():
    path_soundingsSET = args.__dict__['path-soundings']+'/'+SET+'/'
else:
    path_soundingsSET = '/user/data/gent/gvo000/gvo00090/D2D/data/SOUNDINGS/'+SET+'/'

all_stations = stations(path_soundingsSET,suffix='morning',refetch_stations=True).table

all_records_morning = get_records(all_stations,\
                              path_soundingsSET,\
                              subset='morning',
                              refetch_records=False,
                              )

if args.global_chunk is not None:
    totalchunks = 0
    stations_iterator = all_stations.iterrows()
    in_current_chunk = False
    while not in_current_chunk:
        istation,current_station = stations_iterator.__next__()
        all_records_morning_station = all_records_morning.query('STNID == '+str(current_station.name))
        chunks_current_station = math.ceil(float(len(all_records_morning_station))/float(args.split_by))
        in_current_chunk = (int(args.global_chunk) < (totalchunks+chunks_current_station))

        if in_current_chunk:
            run_stations = pd.DataFrame([current_station])# run_stations.loc[(int(args.__dict__['last_station'])]
            run_station_chunk = int(args.global_chunk) - totalchunks 

        totalchunks +=chunks_current_station

else:
    run_stations = pd.DataFrame(all_stations)
    if args.last_station is not None:
        run_stations = run_stations.iloc[:(int(args.__dict__['last_station'])+1)]
    if args.first_station is not None:
        run_stations = run_stations.iloc[int(args.__dict__['first_station']):]
    run_station_chunk = 0
    if args.station_chunk is not None:
        run_station_chunk = args.station_chunk

#print(all_stations)
print(run_stations)
print(args.__dict__.keys())
records_morning = get_records(run_stations,\
                              path_soundingsSET,\
                              subset='morning',
                              refetch_records=False,
                              )
records_afternoon = get_records(run_stations,\
                                path_soundingsSET,\
                                subset='afternoon',
                                refetch_records=False,
                                )

# align afternoon records with the noon records, and set same index
records_afternoon.index = records_afternoon.ldatetime.dt.date
records_afternoon = records_afternoon.loc[records_morning.ldatetime.dt.date]
records_afternoon.index = records_morning.index

experiments = args.experiments.split(';')

for expname in experiments:
    exp = EXP_DEFS[expname]
    path_exp = '/kyukon/data/gent/gvo000/gvo00090/D2D/data/C4GL/'+SET+'_'+expname+'/'

    os.system('mkdir -p '+path_exp)
    for istation,current_station in run_stations.iterrows():
        records_morning_station = records_morning.query('STNID == '+str(current_station.name))
        if (int(args.split_by) * int(run_station_chunk)) >= (len(records_morning_station)):
            print("warning: outside of profile number range for station "+\
                  str(current_station)+". Skipping chunk number for this station.")
        else:
            file_morning = open(path_soundingsSET+'/'+format(current_station.name,'05d')+'_morning.yaml')
            file_afternoon = open(path_soundingsSET+'/'+format(current_station.name,'05d')+'_afternoon.yaml')
            fn_ini = path_exp+'/'+format(current_station.name,'05d')+'_'+\
                     str(int(run_station_chunk))+'_ini.yaml'
            fn_mod = path_exp+'/'+format(current_station.name,'05d')+'_'+\
                     str(int(run_station_chunk))+'_mod.yaml'
            file_ini = open(fn_ini,'w')
            file_mod = open(fn_mod,'w')

            #iexp = 0
            onerun = False

            records_morning_station_chunk = records_morning_station[(int(args.split_by)*run_station_chunk):(int(args.split_by)*(run_station_chunk+1))]
            print(records_morning_station_chunk)

            for (STNID,chunk,index),record_morning in records_morning_station_chunk.iterrows():
                
            
                    c4gli_morning = get_record_yaml(file_morning, 
                                                    record_morning.index_start, 
                                                    record_morning.index_end,
                                                    mode='ini')
                    
                    #print('c4gli_morning_ldatetime',c4gli_morning.pars.ldatetime)
                    
                    
                    record_afternoon = records_afternoon.loc[(STNID,chunk,index)]
                    c4gli_afternoon = get_record_yaml(file_afternoon, 
                                                      record_afternoon.index_start, 
                                                      record_afternoon.index_end,
                                                    mode='ini')
            
                    c4gli_morning.update(source='pairs',pars={'runtime' : \
                                        int((c4gli_afternoon.pars.datetime_daylight - 
                                             c4gli_morning.pars.datetime_daylight).total_seconds())})
                    c4gli_morning.update(source=expname, pars=exp)

                    c4gl = class4gl(c4gli_morning)
                    try:
                        c4gl.run()
                    except:
                        print('run not succesfull')
                    onerun = True

                    c4gli_morning.dump(file_ini)
                    
                    
                    c4gl.dump(file_mod,\
                              include_input=False,\
                              #timeseries_only=timeseries_only,\
                             )
                    onerun = True

                #iexp = iexp +1
            file_ini.close()
            file_mod.close()
            file_morning.close()
            file_afternoon.close()
    
            if onerun:
                records_ini = get_records(pd.DataFrame([current_station]),\
                                                           path_exp,\
                                                           getchunk = int(run_station_chunk),\
                                                           subset='ini',
                                                           refetch_records=True,
                                                           )
                records_mod = get_records(pd.DataFrame([current_station]),\
                                                           path_exp,\
                                                           getchunk = int(run_station_chunk),\
                                                           subset='mod',\
                                                           refetch_records=True,\
                                                           )
            else:
                # remove empty files
                os.system('rm '+fn_ini)
                os.system('rm '+fn_mod)
    
    # # align afternoon records with initial records, and set same index
    # records_afternoon.index = records_afternoon.ldatetime.dt.date
    # records_afternoon = records_afternoon.loc[records_ini.ldatetime.dt.date]
    # records_afternoon.index = records_ini.index
    
    # stations_for_iter = stations(path_exp)
    # for STNID,station in stations_iterator(stations_for_iter):
    #     records_current_station_index = \
    #             (records_ini.index.get_level_values('STNID') == STNID)
    #     file_current_station_mod = STNID
    # 
    #     with \
    #     open(path_exp+'/'+format(STNID,"05d")+'_ini.yaml','r') as file_station_ini, \
    #     open(path_exp+'/'+format(STNID,"05d")+'_mod.yaml','r') as file_station_mod, \
    #     open(path_soundings+'/'+format(STNID,"05d")+'_afternoon.yaml','r') as file_station_afternoon:
    #         for (STNID,index),record_ini in records_iterator(records_ini):
    #             c4gli_ini = get_record_yaml(file_station_ini, 
    #                                         record_ini.index_start, 
    #                                         record_ini.index_end,
    #                                         mode='ini')
    #             #print('c4gli_in_ldatetime 3',c4gli_ini.pars.ldatetime)
    # 
    #             record_mod = records_mod.loc[(STNID,index)]
    #             c4gl_mod = get_record_yaml(file_station_mod, 
    #                                         record_mod.index_start, 
    #                                         record_mod.index_end,
    #                                         mode='mod')
    #             record_afternoon = records_afternoon.loc[(STNID,index)]
    #             c4gl_afternoon = get_record_yaml(file_station_afternoon, 
    #                                         record_afternoon.index_start, 
    #                                         record_afternoon.index_end,
    #                                         mode='ini')

