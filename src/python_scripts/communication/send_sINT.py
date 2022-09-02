#!/usr/bin/env python3

# Send telemtry files according to a flow frequency file that is modified by a monitoring host running 'receive_sINT.py'


import time
import argparse
import os, sys
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *



# Checks if a file has been modified. If it has, update frequency dictionary
def check_for_file_change(frequency_file, last_modified, frequency_dict):
    modified = os.path.getmtime(frequency_file)
    if(modified != last_modified):
        try:
            with open(frequency_file,"r") as f_file:
                frequency_dict = json.load(f_file)
        except:
            print("Cant open file")

        last_modified = modified

    return frequency_dict

# Sends either a telemetry packet or a normal packet according to frequency
def send_telemtry_or_normal_pkt(socket, count, frequency, telemetry_pkt, normal_pkt):
    count+=1
    period = (1/frequency if frequency <= 1 and frequency>0 else 1)
    if(count>=period and frequency>0):
        socket.send(telemetry_pkt)
        count = 0
    else:
        socket.send(normal_pkt)

    return count


def main(args):
    count = 0
    string_val = "x" * int(args['packet_size'])

    telemetry_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                Telemetry(hop_cnt=0)/IP(dst=args['dst_ip'])/UDP(sport=args['dport'],dport=args['dport'])/Raw(load=string_val)

    normal_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth0')) / \
                IP(dst=args['dst_ip'])/UDP(sport=args['dport'],dport=args['dport'])/Raw(load=string_val)

    flow_id = "1"   # 5-tuple hash


    with open(args['frequency_file'],"r") as f_file:
        try:
            frequency_dict = json.load(f_file)
        except:
            frequency_dict = {}
        last_modified = os.path.getmtime(args['frequency_file'])

    s = conf.L2socket(iface='eth0')

    time.sleep(args['wait_time'])


    start = time.time()
    while time.time() - start < args['timeout']:
        try:
            frequency_dict = check_for_file_change(args['frequency_file'], last_modified, frequency_dict)
            if(flow_id in frequency_dict):
                count = send_telemtry_or_normal_pkt(s, count, frequency_dict.get(flow_id), telemetry_pkt, normal_pkt)
            else:
                s.send(telemetry_pkt)

            time.sleep(args['interval'])

        except KeyboardInterrupt:
            sys.exit()



def parse_args():
    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument("-f", "--frequency_file", help="Frequency input file", required=True, type=str)
    parser.add_argument("-a", "--dst_ip", help="Ip dest", required=True, type=str)
    parser.add_argument("-d", "--dport", help="Udp dest port", required=True, type=int) 
    parser.add_argument("-i", "--interval", help="Interval between packets", required=True, type=float)
    parser.add_argument("-s", "--packet_size", help="Packet size", required=True, type=float)
    parser.add_argument("-t", "--timeout", help="Packet dispatch period", required=True, type=float)
    parser.add_argument("-w", "--wait_time", help="Wait time before sending packets", required=False, default=0, type=float)

    return vars(parser.parse_args())

if __name__ == '__main__':
    log_file = open('log.txt', "a")
    log_file.flush()
    try:
        log_file.write("Started sending pkts")
    except Exception as e:
        log_file.write(f"Error start: {e}\n")

        
    args = parse_args()
    main(args)
