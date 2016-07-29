#! /usr/bin/env python


import sys
import numpy as np
import applyDelay as s
import pickle
import matplotlib.pyplot as plt
from time import time
from lofasm import filter
plt.ion()

centertime_bin = s.cable_offset_bins

def getLightCurve(data, timestamps, RA, DEC, winsize=0):
    '''
    apply tdelay shift to data for each timestamp in timestamps
    '''

    assert( winsize % 2 == 0), 'winsize must be an even number'
    assert( winsize >= 0), 'winsize must be positive'

    N = len(timestamps)

    start_dcalc = time()
#    print "Calculating Delays...",
    sys.stdout.flush()
    delays = s.calcDelays(RA, DEC, s.rot_ang, timestamps)
    end_dcalc = time()
#    print "\t done in {} s".format(end_dcalc - start_dcalc)
    
    dbins = -1 * delays / s.calcBinWidth(100000000.0)

    start_curve = time()

    #initialize data array
    lightcurve = np.zeros(N)

    w = winsize/2
    
    for i in range(N):
        k = centertime_bin+int(dbins[i])
        lightcurve[i] = data[k-w:k+w+1, i].sum()
    end_curve = time()

    return filter.medfilt(lightcurve, 101)
   

if __name__ == "__main__":
    import argparse
    import os, sys
    from time import time
    from lofasm import filter

    parser = argparse.ArgumentParser()
    parser.add_argument('ra', help='ra in radians', type=float)
    parser.add_argument('dec', help='dec in radians', type=float)
    parser.add_argument('input', help="path to input lofasm2d file")
    parser.add_argument('output', help='name of output', type=str)
    parser.add_argument('windowsize', help='number of nearby bins to consider, default is 0', default=0, type=int)
    parser.add_argument('--target', help='name of the target', default='None')
    
    args = parser.parse_args()

    assert os.path.exists(args.input)
    assert args.windowsize >= 0
    
    #import loadfiles as lf

    infile = args.input
    RA = args.ra
    DEC = args.dec
    winsize = args.windowsize

    
    #load file
    start_load = time()
    print "Reading file: {}".format(infile),
    sys.stdout.flush()
    with open(infile, 'rb') as f:
        data, timestamps = pickle.load(f)
    end_load = time()
    print "\t done in {} s".format(end_load - start_load)

    lightcurve = getLightCurve(data, timestamps, RA, DEC, winsize)

    #save intermediate data to disk
    fout = args.output if args.output.endswith('.lightcurve') else args.output + '.lightcurve'
    with open(fout, 'wb') as f:
        pickle.dump((lightcurve, timestamps), f)

    #plot data
    plt.figure()
    plt.plot(10*np.log10(lightcurve))
    plt.title(args.target)
    plt.grid()
    plt.savefig(fout + '.png', format='png')

    
    
