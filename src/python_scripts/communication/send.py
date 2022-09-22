#!/usr/bin/env python3

# Send telemtry files according to a flow frequency file that is modified by a monitoring host running 'receive_sINT.py'


import time
import argparse
import os, sys
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *


def main(args):
    count = 0
    string_val = "x" * int(args['packet_size'])

    pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                IP(dst=args['dst_ip'])/UDP(sport=args['dport'],dport=args['dport'])/Raw(load=string_val)
   
    s = conf.L2socket()
    time.sleep(args['wait_time'])

    start = time.time()
    while time.time() - start < args['timeout']:
        try:
            s.send(pkt)
            time.sleep(args['interval'])

        except KeyboardInterrupt:
            sys.exit()



def parse_args():
    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument("-a", "--dst_ip", help="Ip dest", required=True, type=str)
    parser.add_argument("-d", "--dport", help="Udp dest port", required=True, type=int) 
    parser.add_argument("-i", "--interval", help="Interval between packets", required=True, type=float)
    parser.add_argument("-s", "--packet_size", help="Packet size", required=True, type=int)
    parser.add_argument("-t", "--timeout", help="Packet dispatch period", required=True, type=float)
    parser.add_argument("-w", "--wait_time", help="Wait time before sending packets", required=False, default=0, type=float)




    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args)
