#!/usr/bin/python3

import os
import plotly
import plotly.graph_objs as go
import plotly.tools as tls
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Plot CPU utilization')
parser.add_argument('--indir', dest='indir', type=str, default='.', help='Directory to read data files from')
parser.add_argument('--outdir', dest='outdir', type=str, default='.', help='Directory in which to save plot')


# TODO
def parse_file(fname):
    data = []
    avg = []

    with open(fname) as f:
        for line in f:
            if line.find('all') < 0:
                continue

            usage = map(float, line.split('all')[1].split())
            
            # [user, system, all - idle]
            vals = np.array([usage[0], usage[2], sum(usage) - usage[-1]])

            if line.find('Average') >= 0:
                avg = vals
            else:
                data.append(vals)

    return data, avg


# 
def get_data(indir):
    all_data = []
    all_avg = []

    for fname in os.listdir(indir):
        if fname.endswith('.cpu_data'):
            data, avg = parse_file(fname)
            
            all_data.append(data)
            all_avg.append(avg)

    return np.array(all_data), np.array(all_avg)


#
def plot_avg(user_data, kernel_data, outdir='.'):
    N = len(user_data)
    flow_labels = ['Count=' + str(1 << i) for i in range(N)]

    kernel1 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 0],
        xaxis = 'x2',
        name = 'user',
        marker = dict(color = '#0033cc')
    )
    kernel2 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 1],
        xaxis = 'x2',
        name = 'system',
        marker = dict(color = '#3366ff')
    )
    kernel3 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 2] - kernel_data[:, 0] - kernel_data[:, 1],
        xaxis = 'x2',
        name = 'other',
        marker = dict(color = '#99b3ff')
    )

    user1 = go.Bar(
        x = flow_labels,
        y = user_data[:, 0],
        xaxis = 'x1',
        name = 'user',
        marker = dict(color = '#cc0000')
    )
    user2 = go.Bar(
        x = flow_labels,
        y = user_data[:, 1],
        xaxis = 'x1',
        name = 'system',
        marker = dict(color = '#ff3333')
    )
    user3 = go.Bar(
        x = flow_labels,
        y = user_data[:, 2] - user_data[:, 0] - user_data[:, 1],
        xaxis = 'x1',
        name = 'other',
        marker = dict(color = '#ff9999')
    )

    layout = dict(title = 'Average CPU Utilization Breakdown',
        xaxis = dict(title = 'CCP Flows', domain = [0, 0.5], anchor = 'x1'),
        xaxis2 = dict(title = 'Kernel Flows', domain = [0.5, 1], anchor = 'x2'),
        yaxis = dict(title = 'Utilization (%)'),
        barmode = 'stack'
    )

    data = [kernel1, kernel2, kernel3, user1, user2, user3]
    fig = dict(data=data, layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/avg_cpu_util.html')


#
def plot_usage(user_data, kernel_data, outdir):
    N = len(user_data)
    time = np.arange(len(user_data[0]))

    flow_labels = [str(1 << i) + ' flow(s)' for i in range(N)]

    plot_data = []
    for i in range(N):
        kernel = go.Scatter(
            x = time,
            y = kernel_data[i],
            mode = 'lines+markers',
            name = 'Kernel, ' + flow_labels[i]
        )
        
        plot_data.append(kernel)

        user = go.Scatter(
            x = time,
            y = user_data[i],
            mode = 'lines+markers',
            name = 'CCP, ' + flow_labels[i]
        )

        plot_data.append(user)

    layout = dict(title = 'Total CPU Utilization',
        xaxis = dict(title = 'Time (s)'),
        yaxis = dict(title = 'Utilization (%)'),
    )

    fig = dict(data=plot_data, layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/total_cpu_util.html')

if __name__ == '__main__':
    args = parser.parse_args()
    data, avg = get_data(args.indir)
    
    n = len(avg) / 2 # number of files for each ccp/kernel modes
    plot_avg(avg[:n], avg[n:], args.outdir)
    plot_usage(data[:n, :, 2], data[n:, :, 2], args.outdir)








