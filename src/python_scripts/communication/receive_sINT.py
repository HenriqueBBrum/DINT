#!/usr/bin/env python3

import time
import os, sys
import json
import argparse

from math import fabs

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *


count = 0
frequency_dict = {}
previous_tel_data = []
timer = 0

timeout = 5
min_frequency = 0.1
link_util_threshold = 100

type = 'link'


def signifcant_change(tel_data):
    if(len(tel_data)!=len(previous_tel_data)):
        return True

    print("diff not in len")
    for i in range(0, len(tel_data)):
        if(type == 'swid'):
            if (tel_data[i].sw_id != previous_tel_data[i].sw_id):
                return True
        elif(type == 'link'):
            curr_utilization = tel_data[i].amt_bytes/(tel_data[i].time)
            prev_utilization = previous_tel_data[i].amt_bytes/(previous_tel_data[i].time)
            print(curr_utilization, prev_utilization)
            if (fabs(curr_utilization - prev_utilization) > link_util_threshold):
                return True

    return False

def insertion_ratio_algorithm(flow_id, tel_data, frequency_file):
    global count
    global frequency_dict
    global previous_tel_data
    global timer

    count+=1

    if flow_id not in frequency_dict:
        frequency_dict = {flow_id: 0}

    print(frequency_dict, timer, count)
    if(count == 1):
        timer = time.time()
        rf = 1
    elif(signifcant_change(tel_data)):
        timer = time.time()
        rf = frequency_dict.get(flow_id)
        if(2*rf<=1):
            rf = 2*rf
        else:
            rf = 1
    elif(timer >= timeout):
        rf = min_frequency

    previous_tel_data = tel_data

    print("New frequency", rf)
    frequency_dict[flow_id] = rf

    with open(frequency_file, 'w') as f_file:
        f_file.write(json.dumps(frequency_dict))
        f_file.flush()


def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x

def handle_pkt(pkt, frequency_file, tel_file):
    if Telemetry in pkt:
        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]

        print(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}")
        tel_file.write(f"{count}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")

        for sw in data_layers[1:]:
            #utilization = 8.0*sw.amt_bytes/(sw.curr_time - sw.last_time)
            tel_file.write(f"{sw.sw_id}, {sw.flow_id}, {sw.amt_bytes}, {sw.last_time}, {sw.curr_time}\n")
            print(f"Switch {sw.sw_id} - Flow {sw.flow_id}: {sw.amt_bytes}, {sw.last_time}, {sw.curr_time}")

        # flow_id =
        insertion_ratio_algorithm("1", data_layers[1:], frequency_file)



def main(frequency_file, tel_output_file, timeout):
    global frequency_dict

    # frequency_file = 'input_files/frequency_table.json'

    # with open(output_file, 'r') as f_file:
    #     frequency_dict = json.load(f_file)

    tel_file = open(tel_output_file, "w")

    iface = 'eth0'
    print("sniffing on {}".format(iface))
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x, frequency_file, tel_file), timeout = timeout)

    tel_file.close()



def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")

    parser.add_argument("-f", "--frequency_file", help="Output file", required=True, type=str)
    parser.add_argument("-o", "--tel_output_file", help="Output file", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)

  
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args['frequency_file'], args['tel_output_file'], args['timeout'])
