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


#
def parse_file(fname):
    data = []
    with open(fname) as f:
        f.readline() # skip first
        for line in f:
            usage = map(float, line.split())
            
            # [user, system, all - idle]
            vals = np.array([usage[0], usage[2], sum(usage) - usage[3]])         
            data.append(vals)

    return data, sum(data) / float(len(data))


# 
def get_data(indir):
    all_data = []
    all_avg = []

    for fname in os.listdir(indir):
        if fname.endswith('.cpu_data'):
            data, avg = parse_file(indir + '/' + fname)
            
            all_data.append(data)
            all_avg.append(avg)

    return np.array(all_data), np.array(all_avg)


#
def plot_avg(user_data1, user_data2, kernel_data, outdir='.'):
    N = len(user_data1)
    flow_labels = ['Count=' + str(1 << i) for i in range(N)]

    kernel1 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 0],
        xaxis = 'x3',
        name = 'user',
        marker = dict(color = '#0033cc')
    )
    kernel2 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 1],
        xaxis = 'x3',
        name = 'system',
        marker = dict(color = '#3366ff')
    )
    kernel3 = go.Bar(
        x = flow_labels,
        y = kernel_data[:, 2] - kernel_data[:, 0] - kernel_data[:, 1],
        xaxis = 'x3',
        name = 'other',
        marker = dict(color = '#99b3ff')
    )

    user1 = go.Bar(
        x = flow_labels,
        y = user_data1[:, 0],
        xaxis = 'x1',
        name = 'user',
        marker = dict(color = '#cc0000')
    )
    user2 = go.Bar(
        x = flow_labels,
        y = user_data1[:, 1],
        xaxis = 'x1',
        name = 'system',
        marker = dict(color = '#ff3333')
    )
    user3 = go.Bar(
        x = flow_labels,
        y = user_data1[:, 2] - user_data1[:, 0] - user_data1[:, 1],
        xaxis = 'x1',
        name = 'other',
        marker = dict(color = '#ff9999')
    )

    user4 = go.Bar(
        x = flow_labels,
        y = user_data2[:, 0],
        xaxis = 'x2',
        name = 'user',
        marker = dict(color = '#339933')
    )
    user5 = go.Bar(
        x = flow_labels,
        y = user_data2[:, 1],
        xaxis = 'x2',
        name = 'system',
        marker = dict(color = '#66cc66')
    )
    user6 = go.Bar(
        x = flow_labels,
        y = user_data2[:, 2] - user_data2[:, 0] - user_data2[:, 1],
        xaxis = 'x2',
        name = 'other',
        marker = dict(color = '#b3e6b3')
    )

    layout = dict(title = 'Average CPU Utilization Breakdown',
        xaxis = dict(title = 'CCP Per-10ms Flows', domain = [0, 0.33], anchor = 'x1'),
        xaxis2 = dict(title = 'CCP Per-Ack Flows', domain = [0.33, 0.66], anchor = 'x2'),
        xaxis3 = dict(title = 'Kernel Flows', domain = [0.66, 1], anchor = 'x3'),
        yaxis = dict(title = 'Utilization (%)'),
        barmode = 'stack'
    )

    data = [kernel1, kernel2, kernel3, user1, user2, user3, user4, user5, user6]
    fig = dict(data=data, layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/avg_plot.html')


#
def plot_usage(user_data1, user_data2, kernel_data, outdir):
    N = len(user_data1)
    time = np.arange(len(user_data1[0]))

    flow_labels = [str(1 << i) + ' flow(s)' for i in range(N)]

    plot_data = []
    for i in range(N):
        kernel = go.Scatter(
            x = time,
            y = kernel_data[i],
            mode = 'lines+markers',
            name = 'Kernel, ' + flow_labels[i]
        )

        user1 = go.Scatter(
            x = time,
            y = user_data1[i],
            mode = 'lines+markers',
            name = 'User (per-10ms), ' + flow_labels[i]
        )

        user2 = go.Scatter(
            x = time,
            y = user_data2[i],
            mode = 'lines+markers',
            name = 'User (per-ack), ' + flow_labels[i]
        )

        plot_data.append(kernel)
        plot_data.append(user1)
        plot_data.append(user2)

    layout = dict(title = 'Total CPU Utilization',
        xaxis = dict(title = 'Time (s)'),
        yaxis = dict(title = 'Utilization (%)'),
    )

    fig = dict(data=plot_data, layout=layout)
    plotly.offline.plot(fig, filename=outdir + '/util_plot.html')

if __name__ == '__main__':
    args = parser.parse_args()
    data, avg = get_data(args.indir)
    
    n = len(avg) / 3 # number of files for each ccp/kernel modes
    plot_avg(avg[:n], avg[n:2*n], avg[2*n:], args.outdir)
    plot_usage(data[:n, :, 2], data[n:2*n, :, 2], data[2*n:, :, 2], args.outdir)


