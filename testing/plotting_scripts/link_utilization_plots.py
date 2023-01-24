#!/usr/bin/env python3


# Generate link utilizaion step plots with matplotlib for each 'type' of switch.
# This script also calculates the rmse and telemetry overhead  of each 'type'

import matplotlib.pyplot as plt
from math import sqrt, fabs, ceil
import csv
import argparse
import os, sys
import numpy as np
import pandas as pd
import glob


sys.path.append("../constants")
print(sys.path)

import constants


ms = 1000
telemetry_data_sz = 21
telelemetry_header_sz = 4


# Arguments that need to be informed for this program
def parse_args():

    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-e', '--experiment', type=str, help = "The type of experiment (elephant or microburst)", required=True)
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (k, m, g)", required=False, default="k")

    return vars(parser.parse_args())


# Reads real data from csv file to find the amount of bytes transported each 'min_push_time' or if 'min_push_time' > 1s then each 1s
def real_traffic_data(filepath, min_push_time,  unit, experiment_duration):
    min_push_time = 1 if min_push_time >= 1 else min_push_time 
    xy = dict.fromkeys(np.arange(0, experiment_duration+min_push_time, min_push_time), 0)

    total_traffic = 0
    grouped_amt_bytes = 0
    current_time = 0

    with open(filepath) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            if(float(row['frame.time_relative']) >= experiment_duration):
                break

            total_traffic+=int(row['frame.len'])

            # Keeps adding each pkt size until a second has elapsed. After summing up all bytes in that second, write to list
            if(float(row['frame.time_relative']) - current_time <= min_push_time):
                grouped_amt_bytes+=int(row['frame.len'])
            else:
                xy[current_time+min_push_time] = grouped_amt_bytes/(constants.METRIC_UNIT[unit]*min_push_time)
              
                current_time = current_time + min_push_time
                grouped_amt_bytes=int(row['frame.len'])

        xy[current_time+min_push_time] = grouped_amt_bytes/(constants.METRIC_UNIT[unit]*min_push_time)
    
    return list(xy.keys()), list(xy.values()), total_traffic


# Reads telemetry data from a custom txt file
# Txt file Format:
# id, hop_cnt, telemetry_data_sz
# hop_id, flow_id, byte_cnt, previous_time, current_time
# hop_id, flow_id, byte_cnt, previous_time, current_time
def read_telemetry_file(telemetry_file, switch_id, unit, experiment_duration):
    x, y = [0], [0]
    hop_cnt = 0
    prev_time = 0
    telemetry_byte_count = 0
    total_telemetry = 0

    with open(telemetry_file, 'r') as txt_file:
        for line in txt_file:
            cols = line.split(",")
            if hop_cnt == 0:
                hop_cnt = int(cols[1],10) 
                total_telemetry=total_telemetry+(telelemetry_header_sz+telemetry_data_sz*hop_cnt)
                if(hop_cnt > 0):    
                    telemetry_byte_count=telemetry_byte_count+(telelemetry_header_sz+telemetry_data_sz*hop_cnt)
            else:
                if(cols[0]==switch_id):
                    time_window_s = (int(cols[-1],10)-int(cols[-2],10))/(constants.MICROSEG)
                    time_window_s = 1 if time_window_s == 0 else time_window_s

                    if(prev_time+time_window_s) > experiment_duration:
                        return x, y, total_telemetry, telemetry_byte_count

                    x.append(float("{:.6f}".format(prev_time+time_window_s)))
                    y.append((float(cols[1])/time_window_s)/constants.METRIC_UNIT[unit])
                    

                    prev_time+=time_window_s

                hop_cnt-=1

    return x, y, total_telemetry, telemetry_byte_count


# Returns the telemetry reported link utilization 
def find_telemetry_traffic(real_x, telemetry_x, telemetry_y):
    i, j = 0, 0
    expanded_y = []
    while i <len(real_x) and j<len(telemetry_x)-1:
        if(real_x[i] < telemetry_x[j+1]):
            expanded_y.append(telemetry_y[j])
            i+=1
        else:
            j+=1

    expanded_y.append(telemetry_y[j])

    return expanded_y


# Plot link utilization graph in 'Scale'Bits pre second
def plot_line_graph(args, sw_type, real_x, real_y, telemetry_y):
    real_y = [x * 8 for x in real_y]
    telemetry_y = [x * 8 for x in telemetry_y]

    plot1 = plt.figure(1)

    plt.step(real_x, real_y, color="b", label='Real')
    plt.step(real_x, telemetry_y, color='r', label="Telemetry")

    plt.plot([real_x[0], real_x[-1]] , [telemetry_y[0], telemetry_y[-1]], '*', color='red');
    plt.plot([real_x[0], real_x[-1]] , [real_y[0], real_y[-1]], '*', color='blue');

    plt.fill_between(real_x, real_y, telemetry_y, step='pre',  interpolate=True, facecolor='black', alpha=0.2, hatch="X")


    plt.xlabel("Time (s)")
    plt.ylabel("Traffic throughput ("+args['unit'].upper()+"bps)");
    #plt.title('Real link X Telemetry link')
    #plt.yticks(np.arange(0,4.5,0.5))

    plt.gca().legend()
    plot1.savefig(constants.GRAPHS_OUTPUT_FOLDER+args['experiment']+'_Real_X_Telemetry_'+sw_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 


# Saves to a specific file rmse(%) and byte count(Bytes) information
def save_rmse_and_telemetry_byte_count(args, sw_type, telemetry_pkts_count, rmse, telemetry_byte_count, telemetry_percentage):
    filepath = constants.RMSE_OVERHEAD_FOLDER+args['experiment']+".csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a") as csvfile:
        headers = ['sw_type', 'sw_id', 'min_telemetry_push_time', 'experiment_time', 'packet_count', 'rmse', 'telemetry_byte_count', 'telemetry_percentage']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'sw_type': sw_type, 'sw_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                    'experiment_time': args['experiment_duration'], 'packet_count': telemetry_pkts_count, 
                        'rmse': rmse, 'telemetry_byte_count': telemetry_byte_count, 'telemetry_percentage': telemetry_percentage})




def main(args):

    # Transforms all pcapng files (real traffic) to csv files with the folowing headers: frame.number, frame.time_epoch, frame.time_relative, frame.len
    pcapng_files = glob.glob(constants.PKTS_DATA_FOLDER+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(paths[:-1])+"/"+filename+".csv"

        os.system("tshark -r "+f+" -T fields -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -e ip.src -e ip.dst -E header=y -E separator=, > "+filepath)


    telemetry_files = glob.glob(constants.PKTS_DATA_FOLDER+"*_telemetry_pkts.txt")
    for f in telemetry_files:
        sw_type = f.split("/")[-1].split(".")[0].split("_")[0]

        telemetry_x, telemetry_y, total_telemetry, telemetry_byte_count = read_telemetry_file(f, args['switch_id'], args['unit'], args['experiment_duration'])

        real_traffic_file = glob.glob(constants.PKTS_DATA_FOLDER+sw_type+"_real_output.csv")[0]
        real_x, real_y, total_traffic = real_traffic_data(real_traffic_file, args['min_telemetry_push_time'], args['unit'], args['experiment_duration'])
        

        if telemetry_x[-1] < real_x[-1]:
            telemetry_x.append(real_x[-1])
            telemetry_y.append(telemetry_y[-1])

        tel_y = find_telemetry_traffic(real_x, telemetry_x, telemetry_y)

        plot_line_graph(args, sw_type, real_x, real_y, tel_y)

       
        print(sw_type, args['min_telemetry_push_time'], total_telemetry, telemetry_byte_count , total_telemetry/total_traffic)

        rmse = sqrt(np.square(np.subtract(real_y, tel_y)).mean())
        rmse = rmse/(max(real_y) - min(real_y))
        print("rmse", rmse)
        
        save_rmse_and_telemetry_byte_count(args, sw_type, len(telemetry_x), rmse, telemetry_byte_count, total_telemetry/total_traffic)
       

  
if __name__ == '__main__':
    args = parse_args()
    main(args)
