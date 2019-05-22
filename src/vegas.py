'''
TCP Vegas implementation

Ref: https://github.com/spotify/linux/blob/6eb782fc88d11b9f40f3d1d714531f22c57b39f9/net/ipv4/tcp_vegas.c

This version is depracated
'''

import sys
import time
import portus
from argparse import ArgumentParser

parser = ArgumentParser(description='TCP Vegas')
parser.add_argument('--ipc', type=str, help='IPC communication type', default='netlink')
parser.add_argument('--debug', type=bool, help='Portus debugging', default=True)
args = parser.parse_args()

class VegasFlow():
    # Constants
    INIT_CWND = 10
    INIT_SSTHRESH = 32
    ALPHA = 2
    BETA = 4
    GAMMA = 1
    CWND_MAX = 0xffffffff / 128
    INIT_RTT = 0x7fffffff
    TIMEOUT_MULT = 0


    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info

        self.init_cwnd = float(self.datapath_info.mss * VegasFlow.INIT_CWND)
        self.cwnd = self.init_cwnd

        self.ssthresh = float(self.datapath_info.mss * VegasFlow.INIT_SSTHRESH)
        self.slow_start = True

        self.cwnd_reduction = 0

        self.base_rtt = VegasFlow.INIT_RTT
        self.min_rtt = VegasFlow.INIT_RTT
        self.next_seq = 0
        self.last_reduce = 0
        self.rtt_count = 0

        self.datapath.set_program("slow_start", [("Cwnd", self.cwnd)])


    def on_report(self, r):
        # Exit slow start
        if self.slow_start:
        print("Exit slow start")
            self.slow_start = False
            self.cwnd = r.inflight * self.datapath_info.mss
            self.datapath.set_program("default", [("Cwnd", self.cwnd)])

        if r.timeout:
        print("Timeout")
            self.ssthresh = max(self.ssthresh / 2, self.init_cwnd)
            self.reset()
            return

        if r.rtt < 0:
            print("Invalid RTT")
            return

        self.last_rtt = r.rtt

        vrtt = r.rtt + 1
        self.base_rtt = min(self.base_rtt, vrtt)
        self.min_rtt = min(self.min_rtt, vrtt)
        self.rtt_count += 1

        acked = self.ss_increase(r.acked)

        print("expected=", self.next_seq, ", acked=", acked, ", r.acked=", r.acked)

        if acked >= self.next_seq:
            print("Vegas phase")

            self.next_seq = acked
           
            if self.rtt_count <= 2:
                print("Insufficient RTT measurements, reno cong")

                self.reno_cong_avoid(r, acked)
                return

            target_cwnd = self.cwnd * self.base_rtt / self.min_rtt
            diff = self.cwnd * (self.min_rtt - self.base_rtt) / self.base_rtt

            if diff > VegasFlow.GAMMA and self.cwnd <= self.ssthresh:
                print("Gamma cond")

                self.cwnd = min(self.cwnd, target_cwnd + self.datapath_info.mss)
                self.ssthresh = min(self.ssthresh, self.cwnd - self.datapath_info.mss)
            elif self.cwnd <= self.ssthresh:
                print("Switch to slow start")
                self.ss_begin()
            else:
                if diff > VegasFlow.BETA:
                    print("Beta cond")
                    self.cwnd -= self.datapath_info.mss
                    self.ssthresh = min(self.ssthresh, self.cwnd - self.datapath_info.mss)
                elif diff < VegasFlow.ALPHA:
                    print("Alpha cond")
                    self.cwnd += self.datapath_info.mss

            self.cwnd = max(self.cwnd, 2 * self.datapath_info.mss)
            self.cwnd = min(self.cwnd, VegasFlow.CWND_MAX * self.datapath_info.mss)
           
            #self.ssthresh = ?
            self.rtt_count = 0
            self.min_rtt = VegasFlow.INIT_RTT

        elif self.cwnd <= self.ssthresh:
            print("Switch to slow start")
            self.ss_begin()

        self.datapath.update_field("Cwnd", int(self.cwnd))


    def reno_cong_avoid(self, r, acked):
        # AI
        self.cwnd += (self.datapath_info.mss) * float(acked / self.cwnd)
        self.maybe_reduce(r, acked)
        self.datapath.update_field("Cwnd", int(self.cwnd))


    def maybe_reduce(self, r, acked):
        # check if loss happened in last rtt

        if r.loss > 0 or r.sacked > 0:
            if VegasFlow.TIMEOUT_MULT > 0 and \
                time.time() - self.last_reduce > self.last_rtt * VegasFlow.TIMEOUT_MULT:

                self.cwnd_reduction = 0

            if r.loss and self.cwnd_reduction == 0 \
                or (r.acked > 0 and self.cwnd == self.ssthresh):

                # MD
                self.cwnd = min(self.cwnd / 2, self.init_cwnd)
               
                self.last_reduce = time.time()

                self.ssthresh = self.cwnd
                self.datapath.update_field("Cwnd", int(self.cwnd))

            self.cwnd_reduction += r.loss + r.sacked

        elif acked < self.cwnd_reduction:
            self.cwnd_reduction -= int(acked / self.datapath_info.mss)
        else:
            self.cwnd_reduction = 0


    def ss_begin(self):
        self.slow_start = True
        self.datapath.set_program("slow_start", [("Cwnd", self.cwnd)])


    def ss_increase(self, acked):
        if self.cwnd < self.ssthresh:
            if self.cwnd + acked > self.ssthresh:
                self.cwnd = self.ssthresh
                return acked - (self.ssthresh - self.cwnd)

            # Note: no infrequent update correction
            self.cwnd += acked

        return acked


    def reset(self):
        self.cwnd = self.init_cwnd
        self.ss_begin()
        self.curr_cwnd_reduction = 0


class Vegas(portus.AlgBase):
    def datapath_programs(self):
        return {
                "default" : """\
                (def (Report
                    (volatile acked 0)
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                ))
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
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
                    (volatile sacked 0)
                    (volatile loss 0)
                    (volatile timeout false)
                    (volatile rtt 0)
                    (volatile inflight 0)
                ))
                (when true
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Cwnd (+ Cwnd Ack.bytes_acked))
                    (fallthrough)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (report)
                )
            """
        }


    def new_flow(self, datapath, datapath_info):
        return VegasFlow(datapath, datapath_info)


if __name__ == '__main__':
    portus.start(args.ipc, Vegas(), args.debug)