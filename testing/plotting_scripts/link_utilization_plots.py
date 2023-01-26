#!/usr/bin/env python3


# Generate link utilizaion step plots with matplotlib for each 'type' of switch.
# This script also calculates the nrmse and telemetry overhead  of each 'type'

import matplotlib.pyplot as plt
from math import sqrt, fabs, ceil
from operator import add
import csv
import argparse
import os, sys
import numpy as np
import pandas as pd
import glob


sys.path.append("../python_utils")
import constants



class FlowStats:
  def __init__(self, flow_id, experiment_start, first_flow_apperance):
    self.flow_id = flow_id
    self.timestamp_x = [experiment_start]
    self.throughput_y = [0]
    self.experiment_start = experiment_start
    self.current_tel_monitor_timestamp = first_flow_apperance


  def __str__(self):
    return f"FlowStats {self.flow_id}, timestamp_x: {self.timestamp_x}, throughput_y: {self.throughput_y}"+"\n"



# Arguments that need to be informed for this program
def parse_args():
    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-e', '--experiment_type', type=str, help = "The type of experiment (elephant_mice or microburst)", required=True)
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (k, m, g)", required=False, default="k")

    return vars(parser.parse_args())



def main(args):
    # Transforms all pcapng files (real traffic) to csv files with the folowing headers: frame.number, frame.time_epoch, frame.time_relative, frame.len
    pcapng_files = glob.glob(constants.TRAFFIC_DATA_FOLDER+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(paths[:-1])+"/"+filename+".csv"

        os.system("tshark -r "+f+" -T fields -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -e ip.src -e ip.dst -E header=y -E separator=, > "+filepath)


    telemetry_files = glob.glob(constants.TRAFFIC_DATA_FOLDER+"*_telemetry_pkts.txt")
    for telemetry_data_file in telemetry_files:
        switch_type = os.path.basename(telemetry_data_file).split("_")[0]

        real_traffic_file = constants.TRAFFIC_DATA_FOLDER+switch_type+"_real_output.csv"
        real_timestamp_x, real_throughput_y, total_real_traffic, experiment_start = real_traffic_data(args, real_traffic_file)

        tel_flows_stats, total_tel_count, total_tel_overhead, practical_tel_overhead = read_telemetry_file(args, telemetry_data_file, experiment_start)

        total_tel_throughput_y = [0]*len(real_timestamp_x)
        for flow_stat in tel_flows_stats.values():
            adjusted_flow_throughput_y = adjust_tel_throughput(real_timestamp_x, flow_stat.timestamp_x, flow_stat.throughput_y)
            total_tel_throughput_y = list(map(add, adjusted_flow_throughput_y, total_tel_throughput_y))


        plot_line_graph(args, switch_type, experiment_start, real_timestamp_x, real_throughput_y, total_tel_throughput_y)

       
        print(switch_type, args['min_telemetry_push_time'], total_tel_overhead, practical_tel_overhead , total_tel_overhead/total_real_traffic)

        nrmse = sqrt(np.square(np.subtract(real_throughput_y, total_tel_throughput_y)).mean())
        nrmse = nrmse/(max(real_throughput_y) - min(real_throughput_y))
        print("nrmse", nrmse)
        
        save_nrmse_and_telemetry_overhead(args, switch_type, nrmse, total_tel_count,  practical_tel_overhead, total_tel_overhead/total_real_traffic)
       


# Reads real data from csv file to find the amount of bytes transported each 'min_push_time' or if 'min_push_time' > 1s then each 1s
def real_traffic_data(args, real_data_file):
    min_push_time = 1 if args['min_telemetry_push_time'] >= 1 else args['min_telemetry_push_time'] 
    xy = dict.fromkeys(np.arange(0, args['experiment_duration']+min_push_time, min_push_time), 0)

    total_real_traffic = 0
    grouped_amt_bytes = 0
    current_time = 0
    experiment_start = 0

    with open(real_data_file) as csvfile:
        data = list(csv.DictReader(csvfile, delimiter=','))
        experiment_start = float(data[0]['frame.time_epoch'])
        for row in data:
            if(float(row['frame.time_relative']) >= args['experiment_duration']):
                break

            total_real_traffic+=int(row['frame.len'])

            # Keeps adding each pkt size until a second has elapsed. After summing up all bytes in that second, write to list
            if(float(row['frame.time_relative']) - current_time <= min_push_time):
                grouped_amt_bytes+=int(row['frame.len'])
            else:
                xy[current_time+min_push_time] = grouped_amt_bytes/(constants.METRIC_UNIT[args['unit']]*min_push_time)
              
                current_time = current_time + min_push_time
                grouped_amt_bytes=int(row['frame.len'])

        xy[current_time+min_push_time] = grouped_amt_bytes/(constants.METRIC_UNIT[args['unit']]*min_push_time)

    real_timestamp_x, real_throughput_y = [], []
    for key, value in xy.items():
        real_timestamp_x.append(experiment_start+key)
        real_throughput_y.append(value)

    return real_timestamp_x, real_throughput_y, total_real_traffic, experiment_start




# Reads telemetry data from a custom txt file
# Txt file Format:
# telemetry_count, flow_id, hop_cnt, telemetry_metadata_sz, time_arrived_in_monitor
# hop_id, byte_cnt, previous_time, current_time
# hop_id, byte_cnt, previous_time, current_time
def read_telemetry_file(args, telemetry_data_file, experiment_start):
    flows_stat = {}
    hop_cnt, total_tel_count = 0, 0
    total_tel_overhead, practical_tel_overhead  = 0, 0

    with open(telemetry_data_file, 'r') as txt_file:
        flow_id = 0
        for line in txt_file:
            cols = line.split(",")
            if (hop_cnt == 0):
                hop_cnt = int(cols[2],10) 

                total_tel_count+=1
                total_tel_overhead=total_tel_overhead+(constants.TELEMETRY_HEADER_SZ+constants.TELEMETRY_METADATA_SZ*hop_cnt)
                if(hop_cnt > 0):    
                    practical_tel_overhead=practical_tel_overhead+(constants.TELEMETRY_HEADER_SZ+constants.TELEMETRY_METADATA_SZ*hop_cnt)

                flow_id = cols[1]
                if (flow_id not in flows_stat):
                    flows_stat[flow_id] = FlowStats(flow_id, experiment_start, float(cols[4]))

                flows_stat[flow_id].current_tel_monitor_timestamp=float(cols[4])
            else:
                if (cols[0]==args['switch_id']):
                    time_window_s = (int(cols[-1],10)-int(cols[-2],10))/(constants.MICROSEG)
                    time_window_s = 1 if time_window_s == 0 else time_window_s


                    relative_timestamp = flows_stat[flow_id].current_tel_monitor_timestamp-experiment_start
                    if (relative_timestamp>args['experiment_duration']):
                        hop_cnt-=1
                        continue

                    flows_stat[flow_id].timestamp_x.append(float("{:.6f}".format(flows_stat[flow_id].current_tel_monitor_timestamp)))
                    flows_stat[flow_id].throughput_y.append((float(cols[1])/time_window_s)/constants.METRIC_UNIT[args['unit']])

                hop_cnt-=1

    return flows_stat, total_tel_count, total_tel_overhead, practical_tel_overhead


# Returns the flow telemetry reported throughput according to the real timestamp 
def adjust_tel_throughput(real_timestamp_x, tel_timestamp_x, tel_throughput_y):
    i, j = 0, 0
    adjusted_tel_throughput_y = []
    while i <len(real_timestamp_x) and j<len(tel_timestamp_x)-1:
        if (real_timestamp_x[i] < tel_timestamp_x[j+1]):
            adjusted_tel_throughput_y.append(tel_throughput_y[j])
            i+=1
        else:
            j+=1

    adjusted_tel_throughput_y.append(tel_throughput_y[j])
    adjusted_tel_throughput_y.extend([0]*(len(real_timestamp_x) - len(adjusted_tel_throughput_y)))

    return adjusted_tel_throughput_y


# Plots link utilization graph in 'Scale'Bits pre second
def plot_line_graph(args, switch_type, experiment_start, real_timestamp_x, real_throughput_y, tel_throughput_y):
    real_timestamp_x = [x - experiment_start for x in real_timestamp_x] # Ajdust time
    real_throughput_y = [y * 8 for y in real_throughput_y]
    tel_throughput_y = [y * 8 for y in tel_throughput_y]

    plot1 = plt.figure(1)

    plt.step(real_timestamp_x, real_throughput_y, color="b", label='Real')
    plt.plot([real_timestamp_x[0], real_timestamp_x[-1]] , [real_throughput_y[0], real_throughput_y[-1]], '*', color='b');

    plt.step(real_timestamp_x, tel_throughput_y, color='r', label="Telemetry")
    plt.plot([real_timestamp_x[0], real_timestamp_x[-1]] , [tel_throughput_y[0], tel_throughput_y[-1]], '*', color='r');

    plt.fill_between(real_timestamp_x, real_throughput_y, tel_throughput_y, step='pre',  interpolate=True, facecolor='black', alpha=0.2, hatch="X")


    plt.xlabel("Time (s)")
    plt.ylabel("Traffic throughput ("+args['unit'].upper()+"bps)");
    #plt.title('Real link X Telemetry link')
    #plt.yticks(np.arange(0,4.5,0.5))

    plt.gca().legend()
    plot1.savefig(constants.GRAPHS_FOLDER+args['experiment_type']+'_Real_X_Telemetry_'+switch_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 


# Saves to a specific file nrmse(%) and byte count(Bytes) information
def save_nrmse_and_telemetry_overhead(args, switch_type, nrmse, total_tel_count, practical_tel_overhead, telemetry_percentage):
    filepath = constants.NRMSE_OVERHEAD_DATA_FOLDER+args['experiment_type']+".csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a") as csvfile:
        headers = ['switch_type', 'switch_id', 'min_telemetry_push_time', 'experiment_time', 'nrmse', 'tel_packet_count', 'practical_tel_overhead', 'telemetry_percentage']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if (not file_exists):
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'switch_type': switch_type, 'switch_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                    'experiment_time': args['experiment_duration'], 'nrmse': nrmse,  'tel_packet_count': total_tel_count, 
                        'practical_tel_overhead': practical_tel_overhead, 'telemetry_percentage': telemetry_percentage})




if __name__ == '__main__':
    args = parse_args()
    main(args)
