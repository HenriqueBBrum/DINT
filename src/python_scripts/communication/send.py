#!/usr/bin/env python3

# Send telemtry files according to a flow frequency file that is modified by a monitoring host running 'receive_sINT.py'


import time
import argparse
import os, sys
import json
import threading

PKT_SIZE_WITH_HEADER = 1400 #Bytes
HEADER_SIZE = 28



sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *


magnitude = {'B':1, 'K':1000, 'M':1000000, 'G': 1000000000}
items_name = ['dst_ip', 'bandwidth', 'execution_time', 'wait_time']


# ip_addr, bandwidth (Xb/s), execution time (s), wait time (s)
def read_input_file(filename):
    configuration = []
    with open(filename, 'r') as file:
        for line in file.readlines():
            items = line.split(' ')
            if(len(items) != len(items_name)):
                break

            # Finds the first occurence of a alphabetic char and returns the substring from that pos to the end of the string
            first_alpha = items[1].find(next((filter(str.isalpha, items[1])), str(None)))
            if first_alpha is -1:
                mag = 1
                first_alpha = len(items[1])
            else:
                mag = items[1][first_alpha:] 


            final_band = float(items[1][:first_alpha])*magnitude.get(mag, 1)
            items[1] = final_band

            configuration.append(dict(zip(items_name, items)))

    return configuration


def send_packets(pkt, pps, amt_packets, wait_time):
    print(f"Running thread with config: (pps={pps}), (amt_packets={amt_packets})")
    pkt.show2()
    time.sleep(wait_time)

    sendpfast(pkt, pps=pps, loop=amt_packets)



def main(args):
    configuration = read_input_file(args['input_file']) 


    ordered_configuration = sorted(configuration,  key=lambda x: x['wait_time'], reverse=True)

    print(ordered_configuration)

    udp_port = 50000
    for config in configuration:

        print(*config.items())
        pps = config['bandwidth']/(8*PKT_SIZE_WITH_HEADER)
        amt_packets = pps*float(config['execution_time'])

        print(pps)
        print(amt_packets)

        pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                IP(dst=config['dst_ip'])/UDP(sport=udp_port,dport=udp_port)/Raw(RandString(size=(PKT_SIZE_WITH_HEADER-HEADER_SIZE)))


        t = Thread(target=send_packets, args=(pkt, pps, amt_packets, int(config['wait_time'])))
        t.start()

        udp_port=udp_port + 1




def parse_args():
    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument("-i", "--input_file", help="Input file containing information about each flow", required=True, type=str)
  

    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args)
