#!/usr/bin/python3

import os
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser(description='Write CPU utilization')
parser.add_argument('--outfile', dest='outfile', type=str, default='.', help='Output file name')
parser.add_argument('--freq', dest='freq', type=float, default=100, help='Update frequency in ms')
parser.add_argument('--dur', dest='dur', type=int, default=10, help='Duration to perform task in sec')

# Constants
CPU_COUNT = 4.0


#
def get_base_stats():
    with open('/proc/stat') as f:
        line = f.readline()
        return np.array(map(float, line.split()[1:]))


#
def write_new_stats(outfile, prev, freq):
    with open('/proc/stat') as f:
        line = f.readline()

        data = np.array(map(float, line.split()[1:]))
  
        # Convert to percent (also convert freq to jiffies)
        norm_data = (data - prev) / sum(data - prev) * 100.0

        str_data = ''
        for i in range(len(norm_data)):
            str_data += str(norm_data[i]) + ' '

        outfile.write(str_data + '\n')
        return data

# 
def record_stats(args):
    outfile = open(args.outfile, 'a+')

    prev = get_base_stats() # baseline
    time.sleep(0.01) # so that stats will change

    iters = 0
    data = []
    start = time.time()
    while time.time() < start + args.dur:
        prev = write_new_stats(outfile, prev, args.freq)
        time.sleep(1 * args.freq / 1000.0)

    outfile.close()


if __name__ == '__main__':
    args = parser.parse_args()
    record_stats(args)    

