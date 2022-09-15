#!/usr/bin/env python3

import argparse

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

count = 0

def handle_pkt(pkt, tel_file, log_file):
    global count

    if Telemetry in pkt:
        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]
        log_file.write(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}\n")

        tel_file.write(f"{count}, {data_layers[0].hop_cnt}, {data_layers[0].telemetry_data_sz}\n")
        for sw in data_layers[1:]:
            utilization = 8.0*sw.amt_bytes/(sw.curr_time - sw.last_time)
            tel_file.write(f"{sw.sw_id}, {sw.amt_bytes}, {sw.last_time}, {sw.curr_time}\n")

            log_file.write(f"Switch {sw.sw_id}: {sw.amt_bytes}, {sw.last_time}, {sw.curr_time}")

        count+=1


def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")
    parser.add_argument("-o", "--tel_output_file", help="Telemetry output file", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)

  
    return vars(parser.parse_args())


def main(tel_output_file, timeout):
    iface = 'eth0'
    tel_file = open(tel_output_file, "w")

    log_file = open('log.txt', "w")
    try:
        log_file.write("Started receiving pkts, output file is:"+tel_output_file+"\n")
    except Exception as e:
        log_file.write(f"Error start: {e}\n")

    try:
        sniff(iface = iface,
              prn = lambda x: handle_pkt(x, tel_file, log_file), timeout = timeout)
    except Exception as e:
        log_file.write(f"Error in sniff: {e}\n")

    log_file.write("\nExiting")
    log_file.close()

    tel_file.close()

if __name__ == '__main__':

    args = parse_args()
    main(args['tel_output_file'], args['timeout'])
