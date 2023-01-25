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
import ast


sys.path.append("../python_constants")
import constants




def parse_args():
    parser = argparse.ArgumentParser(description=f"Save elephant flow or microburst related metrics")
    #parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    #parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    #parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-e', '--experiment', type=str, help = "The type of experiment (elephant or microburst)", required=True)

    return vars(parser.parse_args())

def find_real_anomalous_flows(bandwidth_threshold, duration_threshold):
    real_anomalous_flows_files = glob.glob(constants.PKTS_DATA_FOLDER+"*real_flows.csv")
    real_anomalous_flows = {}

    for f in real_anomalous_flows_files:
        switch_type = os.path.basename(f).split('_')[0]
        real_anomalous_flows[switch_type] = {}
        with open(f) as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                bandwidth = (float(row['total_bytes'])*8)/float(row['total_time']) # bits/s
                five_tuple = (row['src_ip'], row['src_port'], row['dest_ip'], row['dest_port'], 17)
                print(bandwidth)
                if(bandwidth>bandwidth_threshold and float(row['total_time'])>duration_threshold):
                    real_anomalous_flows[switch_type][five_tuple] = (bandwidth, float(row['total_time']))

    return real_anomalous_flows



def get_telemetry_anomalous_flows(experiment):
    tel_anomalous_flows_files = glob.glob(constants.PKTS_DATA_FOLDER+"*"+experiment+"_flows.csv")
    tel_anomalous_flows = {}

    for f in tel_anomalous_flows_files:
        switch_type = os.path.basename(f).split('_')[0]
        tel_anomalous_flows[switch_type] = {}
        with open(f) as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                timestamp = ast.literal_eval(row['anomalous_identification_timestamp'])[0]
               
                time_to_detect = (float(timestamp[1]) - float(timestamp[0]))/constants.MICROSEG
                tel_anomalous_flows[switch_type][ast.literal_eval(row['flow'])] = (row['bandwidth'], time_to_detect)
              

    return tel_anomalous_flows



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

    real_anomalous_flows = find_real_anomalous_flows(bandwidth_threshold, duration_threshold)
    tel_anomalous_flows = get_telemetry_anomalous_flows(args['experiment'])


    print(real_anomalous_flows)
    print(tel_anomalous_flows)

    # calculate_avg_identifcation_delay(args['input_folder'], args['graphs_output_folder'])
    # identification_accuray()



if __name__ == '__main__':
    args = parse_args()
    main(args)
