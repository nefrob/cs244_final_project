'''
TCP Reno implementation

In progress ...
'''

import sys
import time
import portus
from argparse import ArgumentParser

parser = ArgumentParser(description='TCP Reno')
parser.add_argument('--ipc', type=str, help='IPC communication type', default='netlink')
parser.add_argument('--debug', type=bool, help='Portus debugging', default=True)
args = parser.parse_args()


# Signals class
class CongSignals():
    def __init__(self):
        self.acked = 0
        self.pkts_acked = 0
        self.sacked = 0
        self.loss = 0
        self.timeout = False
        self.rtt = 0
        self.inflight = 0
        self.now = 0


#
class RenoFlow():
    # Constants
    INIT_CWND = 10
    INIT_SSTHRESH = 500
    CWND_MAX = 65535


    #
    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info

        self.init_cwnd = float(self.datapath_info.mss * VegasFlow.INIT_CWND)
        self.cwnd = self.init_cwnd

        self.ssthresh = float(self.datapath_info.mss * VegasFlow.INIT_SSTHRESH)
        self.slow_start = True

        self.last_report = 0
        self.outstanding = 0

        self.datapath.set_program("slow_start", [("Cwnd", self.cwnd)])


    #
    def get_fields(self, r):
        fields = CongSignals()
        fields.acked = r.acked
        fields.pkts_acked = r.pkts_acked
        fields.sacked = r.sacked
        fields.loss = r.loss
        fields.timeout = r.timeout
        fields.rtt = r.rtt
        fields.inflight = r.inflight
        fields.now = r.now

        return fields


    def on_report(self, r):
        fields = self.get_fields(r)

        # Exit slow start
        if self.slow_start:
            print("Exit slow start")
            self.slow_start = False
            self.cwnd = fields.inflight * self.datapath_info.mss
            self.datapath.set_program("default", [("Cwnd", self.cwnd)])

        # Restart with thresholded slow start
        if fields.timeout:
            print("Timeout")
            self.ssthresh = max(self.ssthresh / 2, self.init_cwnd)
            self.reset()
            return


        #if time.time() - self.last_report > fields.rtt / 1000000.0:
        #if fields.now - self.last_report > 3 * fields.rtt and fields.loss > 0:
        #    self.outstanding = 0

        # FIXME:
        if fields.acked > 0:
            self.outstanding = max(0, self.outstanding - fields.pkts_acked)

        self.reno_cong_avoid(fields)

    # Perform congestion avoidance window updates
    def reno_cong_avoid(self, r):
        #print("loss=", r.loss, "timeout=", r.timeout, "acked=", r.acked, "ssthresh=", self.ssthresh, "cwnd=", self.cwnd, "out=", self.outstanding)

        # Multiplicative decrease
        if r.loss > 0 and self.outstanding == 0:
            self.cwnd = max(self.cwnd / 2, self.init_cwnd)
            self.ssthresh = self.cwnd

            self.last_report = r.now
            self.outstanding += r.loss #+ r.sacked
            self.datapath.update_field("Cwnd", int(self.cwnd))
            return

        # Additive increase
        self.outstanding = max(0, self.outstanding - r.pkts_acked)
        self.cwnd += (self.datapath_info.mss * (r.acked / float(self.cwnd)))

        self.datapath.update_field("Cwnd", int(self.cwnd))


    def ss_begin(self):
        self.slow_start = True
        self.datapath.set_program("slow_start_thresh", [("Cwnd", self.cwnd)])
        self.datapath.update_field("ssthresh", int(self.ssthresh))


    def reset(self):
        self.outstanding = 0
        self.cwnd = self.init_cwnd
        self.ss_begin()


class Reno(portus.AlgBase):
    def datapath_programs(self):
        return {
                "default" : """\
                (def (Report
                    (volatile acked 0)
                    (volatile pkts_acked 0)
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                    (volatile now 0)
                ))
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.pkts_acked (+ Report.pkts_acked Ack.packets_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.now Ack.now)
                    (fallthrough)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (report)
                    (:= Micros 0)
                )
                (when (> Micros Flow.rtt_sample_us)
                    (report)
                    (:= Micros 0)
                )
            """, "slow_start" : """\
                (def (Report
                    (volatile acked 0)
                    (volatile pkts_acked 0)
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                    (volatile now 0)
                ))
                (when true
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.pkts_acked (+ Report.pkts_acked Ack.packets_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.now Ack.now)
                    (:= Cwnd (+ Cwnd Ack.bytes_acked))
                    (fallthrough)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (report)
                )
            """, "slow_start_thresh" : """\
                (def (Report
                        (volatile acked 0)
                        (volatile pkts_acked 0)
                        (volatile sacked 0)
                        (volatile loss 0)
                        (volatile timeout false)
                        (volatile rtt 0)
                        (volatile inflight 0)
                        (volatile now 0)
                    )
                    (ssthresh 0)
                )
                (when true
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.pkts_acked (+ Report.pkts_acked Ack.packets_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.now Ack.now)
                    (:= Cwnd (+ Cwnd Ack.bytes_acked))
                    (fallthrough)
                )
                (when (> Cwnd ssthresh)
                    (report)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (report)
                )
            """
        }


    def new_flow(self, datapath, datapath_info):
        return RenoFlow(datapath, datapath_info)


if __name__ == '__main__':
    portus.start(args.ipc, Reno(), args.debug)

