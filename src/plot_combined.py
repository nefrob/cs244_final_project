
import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Plot Cwnd Average')
parser.add_argument('--indir', dest='indir', type=str, default='.', help='Directory to read sample files from')
parser.add_argument('--outdir', dest='outdir', type=str, default='.', help='Directory in which to save combined samples')

def append_file(fname, tput_delay_f):
    with open(fname) as f:
        next(f)
        for line in f:
            tput_delay_f.write(line)


def combine_files(indir, outdir):
    tput_delay_f = open(outdir + '/tput-delay-combined.log', 'a+')
    tput_delay_f.write('Algorithm Impl Scenario Iteration TimeBin Throughput Delay\n')
    
    subdirs = [x[0] for x in os.walk(indir)]
    for subdir in subdirs:
        for fname in os.listdir(indir + '/' + subdir):
            if fname == 'tput-delay-cdf.log':
                append_file(indir + '/' + subdir + '/' + fname, tput_delay_f)      
     
    tput_delay_f.close()


def plot(outdir):
    subprocess.Popen('./plot/tput-delay-cdf.r {0}/tput-delay-combined.log {0}/tput-cdf.pdf {0}/delay-cdf.pdf'.format(outdir), shell=True)

if __name__ == '__main__':
    args = parser.parse_args()
    combine_files(args.indir, args.outdir)
    plot(args.outdir)

    

        
