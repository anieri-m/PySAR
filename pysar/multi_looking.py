#! /usr/bin/env python
############################################################
# Program is part of PySAR v1.0                            #
# Copyright(c) 2013, Heresh Fattahi                        #
# Author:  Heresh Fattahi                                  #
############################################################
# Yunjun, Oct 2015: Merge timeseries/velocity into one
#                   Merge all non-hdf5 into one
# Yunjun, Nov 2015: Support geomap*.trans file
# Yunjun, May 2015: add multilook() and multilook_attributes()

import sys
import os
import getopt
import warnings

import h5py
import numpy as np

import pysar._readfile as readfile
import pysar._writefile as writefile


######################################## Sub Functions ############################################
def multilook(ifg,lksy,lksx):
    rows,cols=ifg.shape
    lksx = int(lksx)
    lksy = int(lksy)
    rows_lowres=int(np.floor(rows/lksy))
    cols_lowres=int(np.floor(cols/lksx))
    #thr = np.floor(lksx*lksy/2)
    ifg_Clowres=np.zeros((rows,       cols_lowres))
    ifg_lowres =np.zeros((rows_lowres,cols_lowres))
  
    #for c in range(lksx):   ifg_Clowres = ifg_Clowres +         ifg[:,range(c,cols_lowres*lksx,lksx)]
    #for r in range(lksy):   ifg_lowres  = ifg_lowres  + ifg_Clowres[  range(r,rows_lowres*lksy,lksy),:]
    #for c in range(int(cols_lowres)):  ifg_Clowres[:,c]=np.nansum(ifg[:,(c)*lksx:(c+1)*lksx],1)
    #for r in range(int(rows_lowres)):  ifg_lowres[r,:] =np.nansum(ifg_Clowres[(r)*lksy:(r+1)*lksy,:],0)
    #ifg_lowres=ifg_lowres/(lksy*lksx)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        for c in range(cols_lowres):  ifg_Clowres[:,c] = np.nanmean(ifg[:,(c)*lksx:(c+1)*lksx],1)
        for r in range(rows_lowres):  ifg_lowres[r,:]  = np.nanmean(ifg_Clowres[(r)*lksy:(r+1)*lksy,:],0)
  
    return ifg_lowres


def multilook_attributes(atr_dict,lks_az,lks_rg):
    #####
    atr = dict()
    for key, value in atr_dict.iteritems():  atr[key] = str(value)
  
    ##### calculate new data size
    length = int(atr['FILE_LENGTH'])
    width  = int(atr['WIDTH'])
    length_mli = int(np.floor(length/lks_az))
    width_mli  = int(np.floor(width/lks_rg))
  
    ##### Update attributes
    atr['FILE_LENGTH'] = str(length_mli)
    atr['WIDTH']       = str(width_mli)
    try:
        atr['Y_STEP'] = str(lks_az*float(atr['Y_STEP']))
        atr['X_STEP'] = str(lks_rg*float(atr['X_STEP']))
    except: pass
    try:
        atr['AZIMUTH_PIXEL_SIZE'] = str(lks_az*float(atr['AZIMUTH_PIXEL_SIZE']))
        atr['RANGE_PIXEL_SIZE']   = str(lks_rg*float(atr['RANGE_PIXEL_SIZE']))
    except: pass
  
    try:
        atr['ref_y'] = str(int(int(atr['ref_y'])/lks_az))
        atr['ref_x'] = str(int(int(atr['ref_x'])/lks_rg))
    except: pass
    try:
        atr['subset_y0'] = str(int(int(atr['subset_y0'])/lks_az))
        atr['subset_y1'] = str(int(int(atr['subset_y1'])/lks_az))
        atr['subset_x0'] = str(int(int(atr['subset_x0'])/lks_rg))
        atr['subset_x1'] = str(int(int(atr['subset_x1'])/lks_rg))
    except: pass
  
    return atr


##################################################################################################
def Usage():
    print '''
***************************************************************

  Usage:

     multi_looking.py  file  azimuth_looks  range_looks  [output_name]

     file: PySAR h5 files [interferogram, time-series, velocity] 
           ROI_PAC  files [.dem .unw .cor .hgt .trans]
           Image    files [jpeg, jpg, png]
     azimuth_looks: number of multilooking in azimuth/y direction
     range_looks  : number of multilooking in range/x   direction
     output_name  : optional, file_a*lks_r*lks.$ext by default.

  Example:
       
     multi_looking.py  velocity.h5        15 15
     multi_looking.py  velocity.h5        15 15 velocity_mli.h5
     multi_looking.py  LoadedData.h5      15 20
     multi_looking.py  timeseries.h5      15 15
     multi_looking.py  filt*.unw          10 10
     multi_looking.py  srtm30m.dem        10 10 srtm30m_300m.dem
     multi_looking.py  srtm30m.dem.jpeg   10 10
     multi_looking.py  geomap_4rlks.trans 10 10

***************************************************************
    '''


##################################################################################################

def main(argv):

    try:  
        File = argv[0]
        alks = int(argv[1])
        rlks = int(argv[2])
    except:
        Usage();sys.exit(1)
  
    ext = os.path.splitext(File)[1]
    try:     outName = argv[3]
    except:  outName = File.split('.')[0]+'_a'+str(int(alks))+'lks_r'+str(int(rlks))+'lks'+ext
  
    ################################################################################
    atr = readfile.read_attributes(File)
    k = atr['FILE_TYPE']
    print '\n***************** Multilooking *********************'
    print 'number of multilooking in azimuth / latitude  direction: '+str(alks)
    print 'number of multilooking in range   / longitude direction: '+str(rlks)
    print 'input file: '+k
  
    if k in ['interferograms','coherence','wrapped','timeseries']:
        h5file     = h5py.File(File,'r')
        h5file_mli = h5py.File(outName,'w')
  
        print 'writing >>> '+outName 
  
        if k in ['interferograms','coherence','wrapped']:
            gg = h5file_mli.create_group(k)
            igramList = h5file[k].keys()
            igramList = sorted(igramList)
  
            for igram in igramList:
                print igram
                unw = h5file[k][igram].get(igram)[:]
                unwlks = multilook(unw,alks,rlks)
                group = gg.create_group(igram)
                dset = group.create_dataset(igram, data=unwlks, compression='gzip')
  
                atr = h5file[k][igram].attrs
                atr = multilook_attributes(atr,alks,rlks)
                for key, value in atr.iteritems():   group.attrs[key] = value
  
        elif k == 'timeseries':
            dateList=h5file[k].keys()
            dateList = sorted(dateList)
  
            group = h5file_mli.create_group(k)
            for d in dateList:
                print d
                unw = h5file[k].get(d)[:]
                unwlks=multilook(unw,alks,rlks)
                dset = group.create_dataset(d, data=unwlks, compression='gzip')
  
            ## Update attributes
            atr = h5file[k].attrs
            atr = multilook_attributes(atr,alks,rlks)
            for key, value in atr.iteritems():   group.attrs[key] = value
  
        h5file.close()
        h5file_mli.close()

    ################################################################################
    else:
        ####### To multi_look geomap*.trans file, both its file size and value need to be reduced.
        if k == '.trans':
            rg,az,atr = readfile.read(File)
            rgmli = multilook(rg,alks,rlks);    #rgmli = rgmli/float(rlks)
            azmli = multilook(az,alks,rlks);    #azmli = azmli/float(alks)
            atr = multilook_attributes(atr,alks,rlks)
            writefile.write(rgmli,azmli,atr,outName)
        else:
            data,atr = readfile.read(File)
            data_mli = multilook(data,alks,rlks)
            atr = multilook_attributes(atr,alks,rlks)
            writefile.write(data_mli,atr,outName)


###################################################################################################
if __name__ == '__main__':
    main(sys.argv[1:])



