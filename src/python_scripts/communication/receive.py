#!/usr/bin/env python3

import argparse
from datetime import datetime

from telemetry_headers import *


FLOW_TIMEOUT = 10 # In seconds
ELEPHANT_FLOW_BANDWIDTH_THRESHOLD = 10 # In bits/second
ELPHANT_FLOW_TIME_THRESHOLD = 5 #In seconds

MICROSEG = 1000000


class Flow:
  def __init__(self, flow_id, bandwidth, first_pdp_timestamp, lastest_pdp_timestamp):
    self.flow_id = flow_id
    self.avg_bandwidth = bandwidth
    self.first_pdp_timestamp = first_pdp_timestamp
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    self.elephant = False
    self.elephant_classification_timestamp = 0

    self.check_elephant()



  def __str__(self):
    return f"Flow {self.flow_id}, Avg. Bandwidth: {self.avg_bandwidth}, Time Active: {self.lastest_pdp_timestamp - self.first_pdp_timestamp}"+"\n"


  def update_same_flow(self, bandwidth, lastest_pdp_timestamp):
    self.avg_bandwidth = (self.avg_bandwidth + bandwidth)/2
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    print(self)

    self.check_elephant()



  def same_id_but_different_flow(self, new_bandwidth, new_first_pdp_timestamp, new_lastest_pdp_timestamp):
    self.avg_bandwidth = new_bandwidth
    self.first_pdp_timestamp = new_first_pdp_timestamp
    self.lastest_pdp_timestamp = new_lastest_pdp_timestamp

    self.check_elephant()



  def check_elephant(self):
    if(self.elephant is not True and self.avg_bandwidth > ELEPHANT_FLOW_BANDWIDTH_THRESHOLD and 
        self.lastest_pdp_timestamp - self.first_pdp_timestamp > ELPHANT_FLOW_TIME_THRESHOLD*MICROSEG):
            self.elephant = True
            self.elephant_classification_timestamp = self.lastest_pdp_timestamp
            print("New elephant flow identified: ")
            print(self)
        




def get_packet_layers(packet):
    counter = 0
    while True:
        layer = packet.getlayer(counter)
        if layer is None:
            break

        yield layer
        counter += 1

def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x

count = 0


flows ={}

def handle_pkt(pkt, tel_file):
    global count
    if Telemetry in pkt:
        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]

        print(f"{count}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")
        tel_file.write(f"{count}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")
        for sw in data_layers[1:]:
            tel_capture_period = (sw.curr_timestamp - sw.prev_timestamp)/MICROSEG

            utilization = (8.0*sw.amt_bytes/(tel_capture_period)) # bits/seconds
            tel_file.write(f"{sw.sw_id}, {sw.amt_bytes}, {sw.prev_timestamp}, {sw.curr_timestamp}\n")


            if (sw.sw_id, sw.flow_id) in flows:
                if (tel_capture_period > FLOW_TIMEOUT):
                    print("hey")
                    flows[(sw.sw_id, sw.flow_id)].same_id_but_different_flow(utilization, sw.prev_timestamp, sw.curr_timestamp) 
                else:
                    print("opaaaaaaaaaaaa")
                    flows[(sw.sw_id, sw.flow_id)].update_same_flow(utilization, sw.curr_timestamp)
            else:
                print("init")
                flows[(sw.sw_id, sw.flow_id)] = Flow(sw.flow_id, utilization, sw.prev_timestamp, sw.curr_timestamp)
                
        count+=1






def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")
    parser.add_argument("-o", "--tel_output_file", help="Telemetry output file", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)

  
    return vars(parser.parse_args())


def main(tel_output_file, timeout):
    print("Starting receiver")
    iface = 'eth0'

    tel_file = open(tel_output_file, "w")

    try:
        sniff(iface = iface,
              prn = lambda x: handle_pkt(x, tel_file), timeout = timeout)
    except Exception as e:
        print(f"Error in sniff: {e}\n")


    for flow in list(flows.items()):
        if flow[1].elephant is True:
            print(e.flow_id)

    tel_file.close()

if __name__ == '__main__':
    args = parse_args()
    main(args['tel_output_file'],  args['timeout'])
