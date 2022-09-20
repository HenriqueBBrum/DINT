#!/usr/bin/env python3

import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from math import sqrt, fabs, ceil
import csv
import argparse
import json
import os
import numpy as np
import pandas as pd
import glob

metric_unit = {'k':1000, 'm':1000000, 'g':1000000000}

ms = 1000
microseg = 1000000
telemetry_data_sz = 21
telelemetry_header_sz = 4


# Arguments for this program
def parse_args():

    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-i', '--input_file_folder', type=str, help="Folder with input files")
    parser.add_argument('-j', '--jitter_input_folder', type=str, help = "Jitter calculation input files", required=False)
    parser.add_argument('-g', '--graphs_output_folder', type=str, help="Folder for output graph files")
    parser.add_argument('-r', '--rmse_output_folder', type=str, help="Folder for output rmse and byte overhead files")
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-t', '--traffic_shape', type=str, help = "RMSE traffic shape name", required=False, default="no_type")
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (k, m, g)", required=False, default="k")


    return vars(parser.parse_args())


# Reads real data from csv file to find the amount of bytes transported each min_push_time
def real_traffic_data(filepath, min_push_time,  unit, experiment_duration):
    min_push_time = 1 if min_push_time >= 1 else min_push_time
    xy = dict.fromkeys(np.arange(0, experiment_duration+min_push_time, min_push_time), 0)
    grouped_amt_bytes = 0
    current_time = 0
    previous_time = 0

    with open(filepath) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            if(float(row['frame.time_relative']) >= experiment_duration):
                break

            # Keeps adding each pkt size until a second has elapsed. After summing up all bytes in that second, write to list
            if(float(row['frame.time_relative']) - current_time <= min_push_time):
                grouped_amt_bytes+=int(row['frame.len'])
            else:
                xy[current_time+min_push_time] = grouped_amt_bytes/(metric_unit[unit]*min_push_time)
              
                previous_time = current_time
                current_time = current_time + min_push_time

                grouped_amt_bytes=int(row['frame.len'])

        xy[current_time+min_push_time] = grouped_amt_bytes/(metric_unit[unit]*min_push_time)
    
    return list(xy.keys()), list(xy.values())


# Reads telemetry data from custom txt file to find the amount of bytes transported each second
# Format:
# id, hop_cnt, telemetry_data_sz
# hop_id, flow_id, byte_cnt, previous_time, current_time
# hop_id, flow_id, byte_cnt, previous_time, current_time

def telemetry_traffic_data(telemetry_file, switch_id, unit, experiment_duration):
    x, y = [0], [0]
    hop_cnt = 0
    prev_time = 0
    telemetry_byte_count = 0

    with open(telemetry_file, 'r') as txt_file:
        for line in txt_file:
            cols = line.split(",")
            if hop_cnt == 0:
                hop_cnt = int(cols[1],10) 
                telemetry_byte_count=telemetry_byte_count+(telelemetry_header_sz+telemetry_data_sz*hop_cnt)
            else:
                if(cols[0]==switch_id):
                    time_window_s = (int(cols[-1],10)-int(cols[-2],10))/(microseg)
                    time_window_s = 1 if time_window_s == 0 else time_window_s

                    if(prev_time+time_window_s) > experiment_duration:
                        return x, y, telemetry_byte_count

                    x.append(float("{:.6f}".format(prev_time+time_window_s)))
                    y.append((float(cols[1])/time_window_s)/metric_unit[unit])
                    

                    prev_time+=time_window_s

                hop_cnt-=1

    return x, y, telemetry_byte_count



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


# Plot link utilization graph
def plot_line_graph(args, sw_type, real_x, real_y, telemetry_y):
    real_y = [x * 8 for x in real_y]
    telemetry_y = [x * 8 for x in telemetry_y]

    plot1 = plt.figure(1)

    plt.step(real_x, real_y, color="b", label='Real')
    plt.step(real_x, telemetry_y, color='r', label="Telemetry")

    plt.plot([real_x[0], real_x[-1]] , [telemetry_y[0], telemetry_y[-1]], '*', color='red');
    plt.plot([real_x[0], real_x[-1]] , [real_y[0], real_y[-1]], '*', color='blue');

    plt.fill_between(real_x, real_y, telemetry_y, step='pre',  interpolate=True, facecolor='black', alpha=0.2, hatch="X")


    plt.xlabel("Time(sec)")
    plt.ylabel("Link utilization ("+args['unit'].upper()+"bits/secs)");
    plt.title('Real link X Telemetry link')
    plt.yticks(np.arange(0,5,0.5))

    plt.gca().legend()
    plot1.savefig(args['graphs_output_folder']+args['traffic_shape']+'_Real_X_Telemetry_'+sw_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 


# Calculate jitter of each host of the experiment
def find_jitter(args, sw_type):
    src_pcapng_files = glob.glob(args['jitter_input_folder']+sw_type+"*.pcapng")
    dest_csv = glob.glob(args['input_file_folder']+sw_type+"_real*.csv")[0]

    dest_traffic = pd.read_csv(dest_csv)
   
    src_data = {}
    jitter_dict = {}

    for src_file in src_pcapng_files:
        filename = src_file.split("/")[-1]
        host = filename[filename.find('h'):filename.find('h')+2]
        
        paths = src_file.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(src_file.split("/")[0:-1])+"/"+filename+".csv"
       
        os.system("tshark -r "+src_file+" -T fields -e frame.number -e frame.time_epoch -e frame.len -e ip.src -e ip.dst -E header=y -E separator=, > "+filepath)
        src_data[host] = pd.read_csv(filepath)

    for k, src_traffic in src_data.items():
        ip_src = src_traffic.iloc[0]['ip.src']
        sub_dest_traffic = dest_traffic[dest_traffic['ip.src'] == ip_src]

        if(len(sub_dest_traffic['frame.time_epoch'].to_numpy()) != len(src_traffic['frame.time_epoch'].to_numpy())):
            continue

        time_delay = np.subtract(sub_dest_traffic['frame.time_epoch'].to_numpy(), src_traffic['frame.time_epoch'].to_numpy())
        avg_latency = sum(time_delay)/len(time_delay)

        jitter = 0.0
        iterations = len(time_delay)-1
        for idx in range(0, iterations):
            diff = fabs(time_delay[idx] - time_delay[idx+1])
            jitter+=diff

        jitter_dict[k] =  (jitter/iterations)*ms

    return jitter_dict



# Saves to a specific file rmse(%), byte count(Bytes) and jitter(ms) information
def save_rmse_and_telemetry_byte_count(args, sw_type, telemetry_pkts_count, rmse, telemetry_byte_count, jitter):
    filepath = args['rmse_output_folder']+args['traffic_shape']+".csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a") as csvfile:
        headers = ['sw_type', 'sw_id', 'min_telemetry_push_time', 'experiment_time', 'packet_count', 'rmse', 'telemetry_byte_count', 'jitter']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'sw_type': sw_type, 'sw_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                    'experiment_time': args['experiment_duration'], 'packet_count': telemetry_pkts_count, 
                        'rmse': rmse, 'telemetry_byte_count': telemetry_byte_count, 'jitter': jitter})




def main():
    args = parse_args()

    # Transforms all pcapng files (real traffic) to csv files with the folowing headers: frame.number, frame.time_epoch, frame.time_relative, frame.len
    pcapng_files = glob.glob(args['input_file_folder']+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(f.split("/")[0:-1])+"/"+filename+".csv"
       
        os.system("tshark -r "+f+" -T fields -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -e ip.src -e ip.dst -E header=y -E separator=, > "+filepath)

   
    telemetry_files = glob.glob(args['input_file_folder']+"*.txt")
    rmse_dict = {}

    for f in telemetry_files:
        sw_type = f.split("/")[-1].split(".")[0].split("_")[0]

        telemetry_x, telemetry_y, telemetry_byte_count = telemetry_traffic_data(f, args['switch_id'], args['unit'], args['experiment_duration'])

        real_traffic_file = glob.glob(args['input_file_folder']+sw_type+"_real*.csv")[0]
        real_x, real_y = real_traffic_data(real_traffic_file, args['min_telemetry_push_time'], args['unit'], args['experiment_duration'])
        

        if telemetry_x[-1] < real_x[-1]:
            telemetry_x.append(real_x[-1])
            telemetry_y.append(telemetry_y[-1])

        tel_y = find_telemetry_traffic(real_x, telemetry_x, telemetry_y)

        plot_line_graph(args, sw_type, real_x, real_y, tel_y)

       
        print(sw_type, len(real_y), args['min_telemetry_push_time'], len(tel_y))

        rmse = sqrt(np.square(np.subtract(real_y, tel_y)).mean())
        rmse = rmse/(max(real_y) - min(real_y))
        print("rmse", rmse)

        
        save_rmse_and_telemetry_byte_count(args, sw_type, len(telemetry_x), rmse, telemetry_byte_count, find_jitter(args, sw_type))
       



  
if __name__ == '__main__':
    main()
