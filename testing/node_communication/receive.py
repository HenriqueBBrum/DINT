#!/usr/bin/env python3

# Receives all incoming packets to a host. If a packet has telemetry headers, the information about the collected metrics is saved
# This script also saves flow information that is used to detect elephant flows or microbursts in the plotting_scripts/save_anomalous_flows_stats.py script

import argparse
import csv
import os, sys
import time
import traceback

sys.path.append("../python_utils")
import constants


from telemetry_headers import *
from flow import *


def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")
    parser.add_argument('-e', '--experiment_type', type=str, help = "The type of experiment (elephant_mice or microburst)", required=True)
    parser.add_argument("-s", "--switch_type", help="Static, DINT, etc", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)

    return vars(parser.parse_args())


flows ={}

# Saves all telemetry reported information and the information about the detected elephant flows or microbursts. 
# To understand how the elephant flows, or microbursts are detected check the python_utils/flow.py script
def main(args):
    print("Starting receiver")
    iface = 'h5-eth3'

    tel_output_file = constants.TRAFFIC_DATA_FOLDER+args['switch_type']+"_telemetry_pkts.txt"
    tel_file = open(tel_output_file, 'w')

    try:
        sniff(iface = iface,
              prn = lambda x: handle_pkt(x, tel_file, args['experiment_type']), timeout = args['timeout'])
    except Exception as e:
        print(f"Error in sniff: {e}\n")
        print(traceback.format_exc())
    
    tel_file.close()

    # Saves information about the detected elephant flows or micrbursts
    anomalous_flows_output = constants.TRAFFIC_DATA_FOLDER+args['switch_type']+"_"+args['experiment_type']+"_flows.csv"
    with open(anomalous_flows_output, 'w') as csv_output_file:
        csv_writer=csv.writer(csv_output_file)
        csv_writer.writerow(['flow', 'throughput', 'anomalous_identification_timestamp'])
        saved_flows = set()
        for flow_id, flow_stats in list(flows.items()):
            if flow_stats.was_anomalous is True and flow_id not in saved_flows:
                saved_flows.add(flow_id)
                csv_writer.writerow([flow_id, flow_stats.avg_throughput, str(flow_stats.anomalous_identification_timestamp)])


count = 0
MONITORED_SWITCH = 4

# Handles each packet and saves the telemetry reported information. If the information is from the monitored switch, save the flow aggregated information
def handle_pkt(pkt, tel_file, experiment_type):
    global count
    if Telemetry in pkt:
        five_tuple = (pkt[IP].src, pkt[UDP].sport, pkt[IP].dst, pkt[UDP].dport, pkt[IP].proto)

        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]
        flow_id = data_layers[0].flow_id

        tel_file.write(f"{count}, {flow_id}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}, {time.time()}\n")
        for sw in data_layers[1:]:
            tel_capture_period = (sw.curr_timestamp - sw.prev_timestamp)/constants.MICROSEG

            throughput = (8.0*sw.amt_bytes/(tel_capture_period)) # bits/seconds
            tel_file.write(f"{sw.switch_id},  {sw.amt_bytes}, {sw.prev_timestamp}, {sw.curr_timestamp}\n")

            ## Save flow information if the metrics come from the monitored siwtchh, in this case it's switch 4
            if(int(sw.switch_id) == MONITORED_SWITCH):
                if five_tuple in flows:
                    # If a flow stops sending information after a ceratin period and a new packet arrives with the same five_tuple, 
                    # this new packet is considered a new flow
                    if (tel_capture_period > constants.FLOW_TIMEOUT):
                        flows[five_tuple].same_id_but_different_flow(throughput, sw.prev_timestamp, sw.curr_timestamp) 
                    else:
                        flows[five_tuple].update_same_flow(throughput, sw.curr_timestamp)
                else:
                    flows[five_tuple] = Flow(flow_id, throughput, sw.prev_timestamp, sw.curr_timestamp, experiment_type)
                
        count+=1


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


if __name__ == '__main__':
    args = parse_args()
    main(args)


