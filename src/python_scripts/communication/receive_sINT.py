#!/usr/bin/env python3

import time
import os, sys
import json
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

def insertion_ratio_algorithm(flow_id, tel_data, output_file):
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

    with open(output_file, 'w') as f_file:
        f_file.write(json.dumps(frequency_dict))
        f_file.flush()


def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x

def handle_pkt(pkt, output_file):
    if Telemetry in pkt:
        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]

        print(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}")
        for sw in data_layers[1:]:
            utilization = sw.amt_bytes/(sw.time)
            print(f"Switch {sw.sw_id} - Flow {sw.flow_id}: {utilization} MBps")

        # flow_id =
        insertion_ratio_algorithm("1", data_layers[1:], output_file)


def main():
    global frequency_dict

    output_file = 'input_files/frequency_table.json'

    # with open(output_file, 'r') as f_file:
    #     frequency_dict = json.load(f_file)

    iface = 'eth0'
    print("sniffing on {}".format(iface))
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x, output_file))

if __name__ == '__main__':
    main()
