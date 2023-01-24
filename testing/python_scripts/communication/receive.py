#!/usr/bin/env python3

import argparse
import csv
import os, sys

from datetime import datetime


from telemetry_headers import *



sys.path.append("../../constants")
import constants


class Flow:
  def __init__(self, flow_id, bandwidth, first_pdp_timestamp, lastest_pdp_timestamp, anomaly):
    self.flow_id = flow_id
    self.avg_bandwidth = bandwidth
    self.first_pdp_timestamp = first_pdp_timestamp
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    self.is_anomalous_now = False
    self.was_anomalous = False
    self.anomalous_identification_timestamp = []

    self.anomaly = anomaly


    self.check_anomalous()


  def __str__(self):
    return f"Flow {self.flow_id}, Avg. Bandwidth: {self.avg_bandwidth}, Time Active: {self.lastest_pdp_timestamp - self.first_pdp_timestamp}"+"\n"


  def update_same_flow(self, bandwidth, lastest_pdp_timestamp):
    self.avg_bandwidth = (self.avg_bandwidth + bandwidth)/2
    self.lastest_pdp_timestamp = lastest_pdp_timestamp

    self.check_anomalous()



  def same_id_but_different_flow(self, new_bandwidth, new_first_pdp_timestamp, new_lastest_pdp_timestamp):
    self.avg_bandwidth = new_bandwidth
    self.first_pdp_timestamp = new_first_pdp_timestamp
    self.lastest_pdp_timestamp = new_lastest_pdp_timestamp

    self.check_anomalous()



  def check_anomalous(self):

    bandwidth_threshold=0
    duration_threshold=0
    if(self.anomaly == "elephant"):
        bandwidth_threshold=constants.ELEPHANT_FLOW_BANDWIDTH_THRESHOLD
        duration_threshold=constants.ELEPHANT_FLOW_TIME_THRESHOLD
    else:
        bandwidth_threshold=constants.MICROBURST_FLOW_BANDWIDTH_THRESHOLD
        duration_threshold=constants.MICROBURST_FLOW_TIME_THRESHOLD


    if(self.is_anomalous_now is False and self.avg_bandwidth >= bandwidth_threshold and 
        self.lastest_pdp_timestamp - self.first_pdp_timestamp >= duration_threshold*constants.MICROSEG):
            self.is_anomalous_now = True
            self.was_anomalous = True
            self.anomalous_identification_timestamp.append((self.first_pdp_timestamp, self.lastest_pdp_timestamp))
    elif(self.is_anomalous_now is True and self.avg_bandwidth < bandwidth_threshold):
        self.is_anomalous_now = False
        self.anomalous_identification_timestamp[-1][1] = self.lastest_pdp_timestamp
        




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

def handle_pkt(pkt, tel_file, anomaly):
    global count
    if Telemetry in pkt:
        five_tuple = (pkt[IP].src, pkt[UDP].sport, pkt[IP].dst, pkt[UDP].dport, pkt[IP].proto)

        pkt.show2()

        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]
        flow_id = data_layers[0].flow_id

        tel_file.write(f"{count}, {flow_id}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")
        for sw in data_layers[1:]:
            tel_capture_period = (sw.curr_timestamp - sw.prev_timestamp)/constants.MICROSEG

            utilization = (8.0*sw.amt_bytes/(tel_capture_period)) # bits/seconds
            tel_file.write(f"{sw.sw_id},  {sw.amt_bytes}, {sw.prev_timestamp}, {sw.curr_timestamp}\n")


            if five_tuple in flows:
                if (tel_capture_period > constants.FLOW_TIMEOUT):
                    flows[five_tuple].same_id_but_different_flow(utilization, sw.prev_timestamp, sw.curr_timestamp) 
                else:
                    flows[five_tuple].update_same_flow(utilization, sw.curr_timestamp)
            else:
                flows[five_tuple] = Flow(flow_id, utilization, sw.prev_timestamp, sw.curr_timestamp, anomaly)
                
        count+=1





def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")
    parser.add_argument("-s", "--switch_type", help="Static, DINT, etc", required=True, type=str)
    parser.add_argument('-a', '--anomaly', type=str, help = "The type of anomaly (elephant or microburst)", required=True)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)



    return vars(parser.parse_args())


def main(args):
    print("Starting receiver")
    iface = 'h5-eth3'

    tel_output_file = constants.PKTS_DATA_FOLDER+args['switch_type']+"_telemetry_pkts.txt"
    tel_file = open(tel_output_file, 'w')

    try:
        sniff(iface = iface,
              prn = lambda x: handle_pkt(x, tel_file, args['anomaly']), timeout = args['timeout'])
    except Exception as e:
        print(f"Error in sniff: {e}\n")

    tel_file.close()

    anomalous_flows_output = constants.PKTS_DATA_FOLDER+args['switch_type']+"_"+args['anomaly']+"_flows.csv"

    with open(anomalous_flows_output, 'w') as csv_output_file:
        csv_writer=csv.writer(csv_output_file)
        csv_writer.writerow(['flow', 'bandwidth', 'anomalous_identification_timestamp'])
        saved_flows = set()
        for flow in list(flows.items()):
            if flow[1].was_anomalous is True and flow[0][1] not in saved_flows:
                saved_flows.add(flow[0][1])
                csv_writer.writerow([flow[0], flow[1].avg_bandwidth, str(flow[1].anomalous_identification_timestamp)])




if __name__ == '__main__':
    args = parse_args()
    main(args)
