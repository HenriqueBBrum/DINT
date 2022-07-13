#!/usr/bin/env python3

import zlib
import time
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *


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

count = 1
frequency_dict = {}
previous_tel_data = []
type = 'link'


def signifcant_change(tel_data):
    if(len(tel_data)!=len(previous_tel_data)):
        return True

    for i in range(0, len(tel_data)):
        if(type == 'swid'):
            if (tel_data[i].sw_id != previous_tel_data[i].sw_id):
                return True
        elif(type == 'link'):
            curr_utilization = tel_data[i].amt_bytes/(tel_data[i].time)
            prev_utilization = previous_tel_data[i].amt_bytes/(previous_tel_data[i].time)
            if (fabs(curr_utilization - prev_utilization) > link_util_threshold):
                return True

    return False

def insertion_ratio_algorithm(tel_data, output_file):
    count+=1
    flow_id = 1     # get flow_id from telemetry header

    if flow_id not in frequency_dict:
        frequency_dict = {{flow_id, 0}}

    if(count == 1):
        timer = time.time()
        previous_data = tel_data
        rf = 1
    elif(signifcant_change(tel_data)):
        timer = time.time()
        rf = frequency_dict[flow_id]
        if(2*rf<=1):
            rf = 2*rf
        else:
            rf = 1
    elif(timer >= T):
        rf = min_frequency

    frequency_dict[flow_id] = rf

    with open(output_file, 'w') as frequency_file:
        frequency_file.write(json.dumps(frequency_dict))
        f.flush()



def handle_pkt(pkt, output_file):
    # pkt.show()
    if Telemetry in pkt:
        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]
        print(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}")

        insertion_ratio_algorithm(data_layers[1:], output_file)

        for sw in data_layers[1:]:
            utilization = 8.0*sw.amt_bytes/(sw.time)
            print(f"Switch {sw.sw_id} - Flow {sw.flow_id}: {utilization} Mbps")

def main():
    output_file = 'frequency_table.json'
    iface = 'eth0'
    print("sniffing on {}".format(iface))
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x, output_file))

if __name__ == '__main__':
    main()
