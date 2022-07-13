#!/usr/bin/env python3
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

def main(frequency_file, dst_ip, dport):

    count = 0
    string_val = "x" * 1
    telemetry_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                Telemetry(hop_cnt=0)/IP(dst=dst_ip)/UDP(sport=dport,dport=dport)/Raw(load=string_val)

    normal_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                IP(dst=dst_ip)/UDP(sport=dport,dport=dport)/Raw(load=string_val)

    flow_id = 1
    with open(frequency_file,"r") as f_file:
        data = json.load(f_file)
        modifiedOn = os.path.getmtime(frequency_file)

    while True:
        try:
            modified = os.path.getmtime(frequency_file)
            if modified != modifiedOn:
                with open(frequency_file,"r") as f_file:
                    data = json.load(f_file)
                modifiedOn = modified
            if(flow_id == data['flow_id']):
                count+=1
                frequency = (1/data['frequency'] if data['frequency'] <= 1 and data['frequency']>=0 else 1)
                if(count>=frequency):
                    print("Sent telemetry")
                    sendp(telemetry_pkt, iface='eth0', verbose=0)
                    count = 0
                else:
                    print("Sent normal packet")
                    sendp(normal_pkt, iface='eth0', verbose=0)

            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    args = parse_args()

    main(args['frequency_file'], args['dst_ip'], args['dport'])
