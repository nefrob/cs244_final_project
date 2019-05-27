'''
TCP Vegas implementation

Ref: https://github.com/spotify/linux/blob/6eb782fc88d11b9f40f3d1d714531f22c57b39f9/net/ipv4/tcp_vegas.c
'''

import sys
import time
import portus
from argparse import ArgumentParser

parser = ArgumentParser(description='TCP Vegas')
parser.add_argument('--ipc', type=str, help='IPC communication type', default='netlink')
parser.add_argument('--debug', type=bool, help='Portus debugging', default=True)
args = parser.parse_args()


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


class VegasFlow():
    # Constants
    INIT_CWND = 10
    INIT_SSTHRESH = 300
    ALPHA = 2
    BETA = 4
    GAMMA = 4 # FIXME: tweak this value
    CWND_MAX = 65535
    INIT_RTT = 0x7fffffff


    def __init__(self, datapath, datapath_info):
        self.datapath = datapath
        self.datapath_info = datapath_info

        self.init_cwnd = float(self.datapath_info.mss * VegasFlow.INIT_CWND)
        self.cwnd = self.init_cwnd

        self.ssthresh = float(self.datapath_info.mss * VegasFlow.INIT_SSTHRESH)
        self.slow_start = False # FIXME: not in use currently

        self.cwnd_reduction = 0

        self.base_rtt = VegasFlow.INIT_RTT
        self.min_rtt = VegasFlow.INIT_RTT
        self.rtt_count = 0

        self.last_report = 0

        self.outstanding = self.cwnd
        self.loss = 0

        self.datapath.set_program("default", [("Cwnd", self.cwnd)])


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

        print("loss=", r.loss, "timeout=", r.timeout, "acked=", r.acked, "ssthresh=", self.ssthresh, "cwnd=", self.cwnd)

        # Exit slow start
        if self.slow_start:
            print("Exit slow start")
            self.slow_start = False
            self.cwnd = fields.inflight * self.datapath_info.mss
            self.datapath.set_program("default", [("Cwnd", self.cwnd)])


        if fields.timeout:
            print("Timeout")
            self.ssthresh = max(self.ssthresh / 2, self.init_cwnd)
            #self.reset()
            return

        if fields.rtt < 0:
            print("Invalid RTT")
            return

        vrtt = fields.rtt + 1
        self.base_rtt = min(r.base, vrtt)
        self.min_rtt = min(r.minrtt, vrtt)

        self.loss += fields.loss

        self.rtt_count += fields.pkts_acked
        print("rtt_count=", self.rtt_count)

        self.outstanding -= r.acked

        if self.outstanding <= 0:
        #if time.time() - self.last_report > fields.rtt / 1000000.0:
        #if (fields.now - self.last_report) > fields.rtt / 100000.0: # convert RTT us to jiffies

            self.outstanding = self.cwnd

            #self.last_report = fields.now

            if self.rtt_count <= 2:
                print("Reno")
                self.reno_cong_avoid(fields)

                self.rtt_count = 0
                self.min_rtt = VegasFlow.INIT_RTT
                self.loss = 0
                return

            cwnd = float(self.cwnd) / self.datapath_info.mss

            target_cwnd = cwnd * self.base_rtt / self.min_rtt
            diff = cwnd * (self.min_rtt - self.base_rtt) / self.base_rtt

            if diff > VegasFlow.GAMMA and self.cwnd <= self.ssthresh:
                print("Gamma", diff)

                self.cwnd = min(self.cwnd, target_cwnd * self.datapath_info.mss + self.datapath_info.mss)
                self.ssthresh = min(self.ssthresh, self.cwnd - self.datapath_info.mss)
            elif self.cwnd <= self.ssthresh:
                print("Slow start")
                #self.ss_begin() # try with return slow start fold function after RTT

                # FIXME: this is horrible
                pkts = fields.pkts_acked
                while self.cwnd <= self.ssthresh and pkts > 0:
                    self.cwnd += self.datapath_info.mss
                    pkts -= 1
            else:
                if diff > VegasFlow.BETA:
                    print("Beta")
                    self.cwnd -= self.datapath_info.mss
                    self.ssthresh = min(self.ssthresh, self.cwnd - self.datapath_info.mss)
                elif diff < VegasFlow.ALPHA:
                    print("Alpha")
                    self.cwnd += self.datapath_info.mss

            self.cwnd = max(self.cwnd, 2 * self.datapath_info.mss)
            self.cwnd = min(self.cwnd, VegasFlow.CWND_MAX * self.datapath_info.mss)
           
            self.ssthresh = max(self.ssthresh, self.cwnd / 2)
            self.rtt_count = 0
            self.loss = 0
            #self.min_rtt = VegasFlow.INIT_RTT

        elif self.cwnd <= self.ssthresh:
            print("Slow start")
            #self.ss_begin() # try with return slow start fold function after RTT
            
            # FIXME: this is horrible
            pkts = fields.pkts_acked
            while self.cwnd <= self.ssthresh and pkts > 0:
                self.cwnd += self.datapath_info.mss
                pkts -= 1

        print("cwnd=", self.cwnd)

        self.datapath.update_field("Cwnd", int(self.cwnd))


    def reno_cong_avoid(self, r):
        if r.loss > 0:
            print("Multiplicative decrease")
            self.cwnd = max(self.cwnd / 2, self.init_cwnd)
            self.ssthresh = self.cwnd
        elif self.cwnd <= self.ssthresh:
            # FIXME: this is horrible
            pkts = fields.pkts_acked
            while self.cwnd <= self.ssthresh and pkts > 0:
                self.cwnd += self.datapath_info.mss
                pkts -= 1
            
        else:
            print("Additive increase")
            self.cwnd += (self.datapath_info.mss * (r.acked / float(self.cwnd)))

        print("cwnd=", self.cwnd)

        self.datapath.update_field("Cwnd", int(self.cwnd))


    def ss_begin(self):
        self.slow_start = True
        self.datapath.set_program("slow_start", [("Cwnd", self.cwnd)])


    def reset(self):
        self.cwnd = self.init_cwnd
        self.ss_begin()


class Vegas(portus.AlgBase):
    def datapath_programs(self):
        return {
                "default" : """\
                (def
                    (Report
                        (volatile acked 0)
                        (volatile pkts_acked 0)
                        (volatile sacked 0)
                        (volatile loss 0)
                        (volatile timeout false)
                        (volatile rtt 0)
                        (volatile inflight 0)
                        (volatile now 0)
                        (volatile minrtt +infinity)
                        (volatile base 0)
                    )
                    (basertt +infinity)
                )
                (when true
                    (:= Report.inflight Flow.packets_in_flight)
                    (:= Report.rtt Flow.rtt_sample_us)
                    (:= Report.minrtt (min Report.minrtt Flow.rtt_sample_us))
                    (:= basertt (min basertt Flow.rtt_sample_us))
                    (:= Report.acked (+ Report.acked Ack.bytes_acked))
                    (:= Report.pkts_acked (+ Report.pkts_acked Ack.packets_acked))
                    (:= Report.sacked (+ Report.sacked Ack.packets_misordered))
                    (:= Report.loss Ack.lost_pkts_sample)
                    (:= Report.timeout Flow.was_timeout)
                    (:= Report.now Ack.now)
                    (:= Report.base basertt)
                    (fallthrough)
                )
                (when (|| Report.timeout (> Report.loss 0))
                    (:= Micros 0)
                    (report)
                )
                (when (> Micros Flow.rtt_sample_us)
                    (:= Micros 0)
                    (report)
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
            """
        }


    def new_flow(self, datapath, datapath_info):
        return VegasFlow(datapath, datapath_info)


if __name__ == '__main__':
    portus.start(args.ipc, Vegas(), args.debug)
