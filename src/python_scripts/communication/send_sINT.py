#!/usr/bin/env python3

# Send telemtry files according to a flow frequency file that is modified by a monitoring host running 'receive_sINT.py'


import time
import argparse
import os, sys
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *

def parse_args():
    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument("-f", "--frequency_file", help="Frequency file", required=True, type=str)
    parser.add_argument("-a", "--dst_ip", help="Ip dest", required=True, type=str)
    parser.add_argument("-d", "--dport", help="Udp dest port", required=True, type=int) # cpu, io

    return vars(parser.parse_args())


# Checks if a file has been modified. If it has, update frequency dictionary
def check_for_file_change(frequency_file, last_modified, frequency_dict):
    modified = os.path.getmtime(frequency_file)
    if(modified != last_modified):
        with open(frequency_file,"r") as f_file:
            frequency_dict = json.load(f_file)
        last_modified = modified

    return frequency_dict

# Sends either a telemetry packet or a normal packet according to frequency
def send_telemtry_or_normal_pkt(count, frequency, telemetry_pkt, normal_pkt):
    count+=1
    period = (1/frequency if frequency <= 1 and frequency>0 else 1)
    if(count>=period and frequency>0):
        print("Sent telemetry flow exists")
        sendp(telemetry_pkt, iface='eth0', verbose=0)
        count = 0
    else:
        print("Sent normal packet flow exists")
        sendp(normal_pkt, iface='eth0', verbose=0)

    return count


def main(frequency_file, dst_ip, dport):
    count = 0
    string_val = "x" * 300

    telemetry_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                Telemetry(hop_cnt=0)/IP(dst=dst_ip)/UDP(sport=dport,dport=dport)/Raw(load=string_val)

    normal_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                IP(dst=dst_ip)/UDP(sport=dport,dport=dport)/Raw(load=string_val)

    flow_id = "1"   # 5-tuple hash

    with open(frequency_file,"r") as f_file:
        frequency_dict = json.load(f_file)
        last_modified = os.path.getmtime(frequency_file)

    while True:
        try:
            frequency_dict = check_for_file_change(frequency_file, last_modified, frequency_dict)

            if(flow_id in frequency_dict):
                count = send_telemtry_or_normal_pkt(count, frequency_dict.get(flow_id), telemetry_pkt, normal_pkt)
            else:
                print("Sent telemetry packet")
                sendp(telemetry_pkt, iface='eth0', verbose=0)

            time.sleep(1)

        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    args = parse_args()
    main(args['frequency_file'], args['dst_ip'], args['dport'])
