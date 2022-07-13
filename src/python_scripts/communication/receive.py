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

def handle_pkt(pkt, file):
    global count
    # pkt.show()
    if Telemetry in pkt:

        data_layers = [l for l in expand(pkt) if(l.name=='Telemetry_Data' or l.name=='Telemetry')]
        # print(f"Telemetry header. hop_count:{data_layers[0].hop_cnt}")

        file.write(f"{count}, {data_layers[0].hop_cnt}\n")
        for sw in data_layers[1:]:
            utilization = 8.0*sw.amt_bytes/(sw.time)
            file.write(f"{sw.sw_id}, {sw.flow_id}, {sw.amt_bytes}, {sw.time}\n")

            print(f"Switch {sw.sw_id} - Flow {sw.flow_id}: {utilization} Mbps")

        count+=1


def parse_args():
    parser = argparse.ArgumentParser(description=f"Receive packets and save them to a file")
    parser.add_argument("-f", "--output_file", help="Output file", required=True, type=str)
    parser.add_argument("-t", "--timeout", help="Sniff capture time", required=True, type=float)

  
    return vars(parser.parse_args())


def main(file_path, time):
    iface = 'eth0'
    file = open(file_path, "w")

    sniff(iface = iface,
          prn = lambda x: handle_pkt(x, file), timeout = time)

    file.close()

if __name__ == '__main__':

    args = parse_args()
    main(args['output_file'], args['timeout'])
