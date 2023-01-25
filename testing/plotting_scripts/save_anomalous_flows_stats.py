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


sys.path.append("../python_utils")
import constants



def parse_args():
    parser = argparse.ArgumentParser(description=f"Save elephant flow or microburst related metrics")
    parser.add_argument('-e', '--experiment_type', type=str, help = "The type of experiment (elephant or microburst)", required=True)
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment", required=True)
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files", required=True)
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared", required=True)

    return vars(parser.parse_args())



def main(args):
    pcapng_files = glob.glob(constants.TRAFFIC_DATA_FOLDER+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]

        this_file_folder = os.path.abspath(os.path.dirname(__file__))
        switch_type = filename.split("_")[0]
        os.system("bash "+this_file_folder+"/save_tshark_conv.sh "+ constants.TRAFFIC_DATA_FOLDER +" "+switch_type)

    throughput_threshold = 0
    duration_threshold = 0

    if(args['experiment_type'] == "elephant_mice"):
        throughput_threshold=constants.ELEPHANT_FLOW_THROUGHPUT_THRESHOLD
        duration_threshold=constants.ELEPHANT_FLOW_TIME_THRESHOLD
    else:
        throughput_threshold=constants.MICROBURST_FLOW_THROUGHPUT_THRESHOLD
        duration_threshold=constants.MICROBURST_FLOW_TIME_THRESHOLD

    real_anomalous_flows, amt_real_flows = find_real_anomalous_flows(throughput_threshold,duration_threshold)
    tel_anomalous_flows = get_telemetry_anomalous_flows(args['experiment_type'])

    classification_accuracy, throughput_nrmse, avg_delay = anomalous_flows_stats(real_anomalous_flows, tel_anomalous_flows, amt_real_flows, duration_threshold)

    if classification_accuracy:
        save_anomalous_flows_stats(args, classification_accuracy, throughput_nrmse, avg_delay)



def find_real_anomalous_flows(throughput_threshold, duration_threshold):
    real_anomalous_flows_files = glob.glob(constants.TRAFFIC_DATA_FOLDER+"*real_flows.csv")
    real_anomalous_flows = {}
    amt_flows = {}

    for f in real_anomalous_flows_files:
        amt_flows_count = 0
        switch_type = os.path.basename(f).split('_')[0]
        real_anomalous_flows[switch_type] = {}
        with open(f) as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                amt_flows_count+=1
                throughput = (float(row['total_bytes'])*8)/float(row['total_time']) # bits/s
                five_tuple = (row['src_ip'], row['src_port'], row['dest_ip'], row['dest_port'], str(17))
                if(throughput>throughput_threshold and float(row['total_time'])>duration_threshold):
                    real_anomalous_flows[switch_type][five_tuple] = (throughput, float(row['total_time']))

        amt_flows[switch_type] = amt_flows_count

    return real_anomalous_flows, amt_flows


def get_telemetry_anomalous_flows(experiment_type):
    tel_anomalous_flows_files = glob.glob(constants.TRAFFIC_DATA_FOLDER+"*"+experiment_type+"_flows.csv")
    tel_anomalous_flows = {}

    for f in tel_anomalous_flows_files:
        switch_type = os.path.basename(f).split('_')[0]
        tel_anomalous_flows[switch_type] = {}
        with open(f) as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                timestamp = ast.literal_eval(row['anomalous_identification_timestamp'])[0]
               
                time_to_detect = (float(timestamp[1]) - float(timestamp[0]))/constants.MICROSEG
                flow_id = tuple(str(i) for i in ast.literal_eval(row['flow'])) 
                tel_anomalous_flows[switch_type][flow_id] = (float(row['throughput']), time_to_detect)
              

    return tel_anomalous_flows


def anomalous_flows_stats(real_anomalous_flows, tel_anomalous_flows, amt_real_flows, duration_threshold):
    if(set(real_anomalous_flows.keys()) != set(tel_anomalous_flows.keys())):
        return {}, {}, {}

    classification_accuracy = {}
    throughput_nrmse = {}
    avg_delay = {}
   
    for switch_type in real_anomalous_flows:
        real_anom_five_tuples = real_anomalous_flows[switch_type].keys()
        tel_anom_five_tuples = tel_anomalous_flows[switch_type].keys()

        print(list(tel_anom_five_tuples - real_anom_five_tuples))

        true_positives = len(list(real_anom_five_tuples & tel_anom_five_tuples))
        false_positives = len(list(tel_anom_five_tuples - real_anom_five_tuples))
        false_negatives = len(list(real_anom_five_tuples - tel_anom_five_tuples))
        true_negatives =  amt_real_flows[switch_type] - true_positives - false_positives - false_negatives

        classification_accuracy[switch_type] = {"TPR": true_positives/(true_positives+false_negatives),
                                                  "FPR": false_positives/(false_positives+true_negatives), 
                                                      "FNR":  false_negatives/(false_negatives+true_positives)} # TPR, FNR


        real_anom_flows_throughput = []
        tel_anom_flows_throughput = []
        tel_anom_flows_delay = []
        for five_tuple in real_anomalous_flows[switch_type]:
            real_anom_flows_throughput.append(real_anomalous_flows[switch_type][five_tuple][0])
            tel_anom_flows_throughput.append(tel_anomalous_flows[switch_type][five_tuple][0])

            tel_anom_flows_delay.append(tel_anomalous_flows[switch_type][five_tuple][1] - duration_threshold)

    
        rmse = sqrt(np.square(np.subtract(real_anom_flows_throughput, tel_anom_flows_throughput)).mean())
        throughput_nrmse[switch_type] = rmse/(max(real_anom_flows_throughput) - min(real_anom_flows_throughput))

        avg_delay[switch_type] = sum(tel_anom_flows_delay)/len(tel_anom_flows_delay)

    return classification_accuracy, throughput_nrmse, avg_delay



def save_anomalous_flows_stats(args, classification_accuracy, throughput_nrmse, avg_delay):
    filepath = constants.ANOMALOUS_FLOWS_DATA_FOLDER+args['experiment_type']+".csv"
    file_exists = os.path.isfile(filepath)

    print(classification_accuracy)

    with open(filepath, "a") as csvfile:
        headers = ['switch_type', 'switch_id', 'min_telemetry_push_time', 'experiment_time', 'TPR', 'FPR', 'FNR', 'throughput_nrmse', 'avg_delay']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if (not file_exists):
            writer.writeheader()  # file doesn't exist yet, write a header


        for switch_type, cl_accuracy in classification_accuracy.items():
            writer.writerow({'switch_type': switch_type, 'switch_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                                 'experiment_time': args['experiment_duration'], 'TPR': cl_accuracy['TPR'], 'FPR': cl_accuracy['FPR'], 
                                 'FNR': cl_accuracy['FNR'],  'throughput_nrmse': throughput_nrmse[switch_type], 'avg_delay':avg_delay[switch_type]})




if __name__ == '__main__':
    args = parse_args()
    main(args)