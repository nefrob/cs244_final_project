
# Test Reproduction:

TODO: Pending updates ...


FIXME:
> apt-get install sysstat for sar #ref https://www.cyberciti.biz/tips/how-do-i-find-out-linux-cpu-utilization.html
> pip install plotly #ref https://plot.ly/python/getting-started/


1) To add a new congestion control algorithm on Linux do:<br />
`sudo -i`<br />
`modprobe tcp_alg` for example `tcp_cubic`<br /><br />
Verify it was added via:<br />
`cat /proc/sys/net/ipv4/tcp_available_congestion_control`<br /><br />
To set as default do:<br />
`echo alg > /proc/sys/net/ipv4/tcp_congestion_control`

2) To run the fidelity tests do (modify args as desired):<br />
`python3 ./scripts/run-fidelity-exp.py --outdir fidelity --duration 15 --alg reno --scenario fixed --ipcs netlink --kernel --iters 1`<br /><br />
Note: we have added our modified version to this repo that kills python aimd/reno/vegas algorithm processes.

3) To run our algorithms for fidelity you will need to replace `scripts/start_ccp.py` with our version in this repo. Furthermore you will need to copy our Vegas/Reno/etc. files into the home directory of the CCP-project repo and enable the algorithms via step (1) described in this document.
