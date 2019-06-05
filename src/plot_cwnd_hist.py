#!/usr/bin/python3

import os
import plotly
import plotly.graph_objs as go
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Plot Cwnd Average')
parser.add_argument('--indir', dest='indir', type=str, default='.', help='Directory to read data files from')
parser.add_argument('--subsample', dest='subsample', type=bool, default=True, help='Use cwnd subsample file')
parser.add_argument('--outdir', dest='outdir', type=str, default='.', help='Directory in which to save plot')
parser.add_argument('--dt', dest='dt', type=float, default=0.1, help='Cwnd time sampling bucket size')


#
def parse_file(fname, dt):
    avg_cwnds_data = {'ccp': {}, 'kernel': {}}
    all_cwnds = {'ccp': [], 'kernel': []}

    with open(fname) as f:  
        for line in f:
            if line.find('Algorithm') >= 0:
                continue

            key = 'ccp' if line.find('kernel') < 0 else 'kernel'
      
            tokens = line.split()
            time = float(tokens[-2])
            cwnd_sample = float(tokens[-1])

            all_cwnds[key].append(cwnd_sample)
            
            # Precision should match dt sig figs
            interval = round(round(time / dt) * dt, 2)

            if interval in avg_cwnds_data[key]:
                avg_cwnds_data[key][interval][0] += cwnd_sample
                avg_cwnds_data[key][interval][1] += 1
            else:
                avg_cwnds_data[key][interval] = [cwnd_sample, 1]

    # Average results
    avg_cwnds = {'ccp': [], 'kernel': []}
    for key in sorted(avg_cwnds_data['ccp']):
        v = avg_cwnds_data['ccp'][key]
        avg_cwnds['ccp'].append(v[0] / v[1])

    for key in sorted(avg_cwnds_data['kernel']):
        v = avg_cwnds_data['kernel'][key]
        avg_cwnds['kernel'].append(v[0] / v[1])
    
    # Truncate if one longer than other
    N = min(len(avg_cwnds['ccp']), len(avg_cwnds['kernel']))

    avg_cwnds['ccp'] = avg_cwnds['ccp'][:N]
    avg_cwnds['kernel'] = avg_cwnds['kernel'][:N]
    
    return avg_cwnds, all_cwnds


# 
def get_data(indir, dt, subsample):
    if subsample:
        return parse_file(indir + '/cwndevo-subsampled.log', dt)
    else:
        return parse_file(indir + '/cwndevo.log', dt)


#
def plot(avg_cwnds, all_cwnds, dt, outdir):
    N = len(avg_cwnds['ccp'])
    time = np.linspace(0, N * dt, N)

    avg_user = go.Scatter(
        x = time,
        y = avg_cwnds['ccp'],
        mode = 'lines',
        name = 'CCP'
    )

    avg_kernel = go.Scatter(
        x = time,
        y = avg_cwnds['kernel'],
        mode = 'lines',
        name = 'Kernel'
    )

    avg_diff = go.Scatter(
        x = time,
        y = np.abs(np.array(avg_cwnds['kernel']) - np.array(avg_cwnds['ccp'])),
        mode = 'lines',
        name = 'Difference'
    )

    layout = dict(title = 'Average cwnd per ' + str(dt) + 's bucket',
        xaxis = dict(title = 'Time (s)'),
        yaxis = dict(title = 'Cwnd size'),
    )

    fig = dict(data=[avg_user, avg_kernel, avg_diff], layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/avg_cwnd_plot.html')

    total_user = go.Histogram(
        x = all_cwnds['ccp'],
        histnorm = 'percent',
        opacity = 0.75,
        name = 'CCP'
    )

    total_kernel = go.Histogram(
        x = all_cwnds['kernel'],
        histnorm = 'percent',
        opacity = 0.75,
        name = 'Kernel'
    )

    layout = dict(title = 'Cwnd histogram',
        xaxis = dict(title = 'Cwnd size (in MSS)'),
        yaxis = dict(title = 'Count (%)'),
        barmode = 'overlay'
    )

    fig = dict(data=[total_user, total_kernel], layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/hist_cwnd_plot.html')

if __name__ == '__main__':
    args = parser.parse_args()
    avg_cwnds, all_cwnds = get_data(args.indir, args.dt, args.subsample)
    
    plot(avg_cwnds, all_cwnds, args.dt, args.outdir)









