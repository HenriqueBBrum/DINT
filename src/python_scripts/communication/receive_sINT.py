#!/usr/bin/env python3

import time
import os, sys
import json
import argparse

from math import fabs

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_headers import *

microseg = 1000000

count = 0
frequency_dict = {}
previous_tel_data = []
timer = 0

timeout = 0.01
min_frequency = 0.01

type = 'link'


log_file = open('log.txt', "a")



def signifcant_change(tel_data, link_threshold):
    if(len(tel_data)!=len(previous_tel_data)):
        return True

    for i in range(0, len(tel_data)):
        if(type == 'swid'):
            if (tel_data[i].sw_id != previous_tel_data[i].sw_id):
                return True
        elif(type == 'link'):
            curr_utilization = microseg*tel_data[i].amt_bytes/(tel_data[i].curr_time - tel_data[i].last_time)
            prev_utilization = microseg*previous_tel_data[i].amt_bytes/(previous_tel_data[i].curr_time - previous_tel_data[i].last_time)
            log_file.write(str(fabs(curr_utilization - prev_utilization))+"\n")
            if (fabs(curr_utilization - prev_utilization) > link_threshold):
                return True

    return False

def insertion_ratio_algorithm(flow_id, tel_data, frequency_file, link_threshold):
    global count
    global frequency_dict
    global previous_tel_data
    global timer

    count+=1

    #print(frequency_dict, timer, count, frequency_dict)
    if(count == 1):
        timer = time.time()
        rf = min_frequency
    elif(signifcant_change(tel_data, link_threshold)):
        timer = time.time()
        rf = frequency_dict.get(flow_id)
        if(2*rf<=1):
            rf = 2*rf
        else:
            rf = 1
    elif((time.time() - timer)>= timeout):
        rf = min_frequency
    else:
        previous_tel_data = tel_data
        return

    previous_tel_data = tel_data
    log_file.write("New frequency: "+str(rf)+"\n")

    if(flow_id in frequency_dict):
        old_rf = frequency_dict[flow_id]
    else:
        old_rf = 0

    frequency_dict[flow_id] = rf

    if(rf != old_rf):
        with open(frequency_file, 'w') as f_file:
            f_file.write(json.dumps(frequency_dict))
            f_file.flush()


def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x

def handle_pkt(pkt, frequency_file, tel_file, link_threshold):
    flow_id = "1"

    if Telemetry in pkt:

        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]

        #print(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}")
        tel_file.write(f"{count}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")

        for sw in data_layers[1:]:
            tel_file.write(f"{sw.sw_id},{sw.amt_bytes}, {sw.last_time}, {sw.curr_time}\n")

        insertion_ratio_algorithm(flow_id, data_layers[1:], frequency_file, link_threshold)



def main(args):
    iface = 'eth0'
    tel_file = open(args['tel_output_file'], "w")

    log_file.flush()
    try:
        log_file.write("Started receiving pkts, output file is:"+ args['tel_output_file']+"\n")
    except Exception as e:
        log_file.write(f"Error start Receive: {e}\n")

    try:
        sniff(iface = iface,
              prn = lambda x: handle_pkt(x, args['frequency_file'], tel_file, args['link_threshold']), timeout = args['timeout'])
    except Exception as e:
        log_file.write(f"Error in sniff sINT: {e}\n")

    log_file.write("Exiting")
    log_file.close()
    
    tel_file.close()



def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")

    parser.add_argument("-f", "--frequency_file", help="Frequency output file", required=True, type=str)
    parser.add_argument("-o", "--tel_output_file", help="Telemetry output file", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)
    parser.add_argument("-l", "--link_threshold", help="Link treshhold in B/s", required=True, type=int)

  
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args)
