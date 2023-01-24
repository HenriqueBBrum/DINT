#!/usr/bin/env python3


# Generate link utilizaion step plots with matplotlib for each 'type' of switch.
# This script also calculates the rmse and telemetry overhead  of each 'type'

from math import sqrt, fabs, ceil
import csv
import argparse
import os, sys
import numpy as np
import pandas as pd
import glob


sys.path.append("../constants")
import constants



def find_real_anomalous_flows(bandwidth_threshold, duration_threshold):
    real_anomalous_flows_files = glob.glob(constants.PKTS_DATA_FOLDER+"*real_flows.csv")
    real_anomalous_flows = {}

    for f in real_anomalous_flows_files:
        switch_type = os.path.basename(f).split('_')[0]
        real_anomalous_flows[switch_type] = {}
        with open(f) as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                bandwidth = float(row['total_bytes'])/float(row['total_time'])
                five_tuple = (row['src_ip'], row['src_port'], row['dest_ip'], row['dest_port'], 17)
                print(bandwidth)
                if(bandwidth>bandwidth_threshold and flot(row['total_time'])>duration_threshold):
                    real_anomalous_flows[switch_type][five_tuple] = (bandwidth, flot(row['total_time']))

    return real_anomalous_flows


def main(args):

    pcapng_files = glob.glob(constants.PKTS_DATA_FOLDER+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]

        this_file_folder = os.path.abspath(os.path.dirname(__file__))
        switch_type = filename.split("_")[0]
        os.system("bash "+this_file_folder+"/save_tshark_conv.sh "+switch_type)

    bandwidth_threshold = 0
    duration_threshold = 0

    if(args['experiment'] == "elephant"):
        bandwidth_threshold=constants.ELEPHANT_FLOW_BANDWIDTH_THRESHOLD
        duration_threshold=constants.ELEPHANT_FLOW_TIME_THRESHOLD
    else:
        bandwidth_threshold=constants.MICROBURST_FLOW_BANDWIDTH_THRESHOLD
        duration_threshold=constants.MICROBURST_FLOW_TIME_THRESHOLD

    real_flows = find_real_anomalous_flows(bandwidth_threshold, duration_threshold)

    print(real_flows)

    #anomalous_montoitored_flows = glob.glob(args['input_file_folder']+"*telemtry*.txt")




    # calculate_avg_identifcation_delay(args['input_folder'], args['graphs_output_folder'])
    # identification_accuray()



def parse_args():
    parser = argparse.ArgumentParser(description=f"Save elephant flow or microburst related metrics")
    #parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    #parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    #parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-e', '--experiment', type=str, help = "The type of experiment (elephant or microburst)", required=True)

    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args)
