#!/usr/bin/env python3

import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from math import sqrt, fabs
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
       
    return xy


# Reads real data from csv file to find the amount of bytes transported at the same timestamp that was telemetry reported
def real_traffic_data_tel(filepath, telemetry_x, unit, experiment_duration):
    xy = {0: 0}
    count = 1

    with open(filepath) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for idx, i in enumerate(telemetry_x):
            if idx == 0:
                continue
           
            grouped_amt_bytes = 0
            ct = 0
        
            for row in data:
                time = float(row['frame.time_relative'])

                if time > i:
                    break
                if time <= i:
                    grouped_amt_bytes+=int(row['frame.len'])
                    ct+=1

            xy[float("{:.6f}".format(i))] = float("{:.6f}".format((grouped_amt_bytes/(i - telemetry_x[idx-1]))/metric_unit[unit]))
        
    return xy


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

# Fill 'y' array with values in 'expanded_x' but not in 'x' (original array)
def my_interpolation(expanded_x, x, y):
    i, j = 0, 0
    expanded_y = []
    while j<len(x) and i<len(expanded_x):
        if expanded_x[i] > x[j]:
            j+=1
        else:
            expanded_y.append(y[j])
            i+=1

    return expanded_y


# Find common values between telemetry and real data and plot link utilization graph
def plot_line_graph(args, sw_type, real_data, telemetry_data):
    real_x, real_y = real_data
    telemetry_x, telemetry_y = telemetry_data

    combined_x = np.sort(np.concatenate([real_x, telemetry_x]))

    tel_expanded_y = my_interpolation(combined_x, telemetry_x, telemetry_y)
    real_expanded_y = my_interpolation(combined_x, real_x, real_y)
   
    real_expanded_y = [x * 8 for x in real_expanded_y]
    tel_expanded_y = [x * 8 for x in tel_expanded_y]
    telemetry_y = [x * 8 for x in telemetry_y]

    plot1 = plt.figure(1)

    plt.step(combined_x, real_expanded_y, color="b", label='Real')
    plt.step(combined_x, tel_expanded_y, color="r", label='Telemetry')

    plt.plot(telemetry_x[1:-1], telemetry_y[1:-1], 'o', color='black')
    plt.plot([telemetry_x[0], telemetry_x[-1]] , [telemetry_y[0], telemetry_y[-1]], '*', color='red');
    plt.plot([real_x[0], real_x[-1]] , [real_expanded_y[0], real_expanded_y[-1]], '*', color='blue');

    plt.fill_between(combined_x, real_expanded_y, tel_expanded_y, step='pre',  interpolate=True, facecolor='black', alpha=0.2, hatch="X")


    plt.xlabel("Time(sec)")
    plt.ylabel("Link utilization ("+args['unit'].upper()+"bits/secs)");
    plt.title('Real link X Telemetry link')
    plt.yticks(np.arange(0,5,0.5))

    plt.gca().legend()
    plot1.savefig(args['graphs_output_folder']+args['traffic_shape']+'_Real_X_Telemetry_'+sw_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 

    return real_expanded_y, tel_expanded_y


# Calculate jitter of each experiment
def find_jitter(args, sw_type):
    src_pcapng_files = glob.glob(args['jitter_input_folder']+sw_type+"*.pcapng")
    dest_csv = glob.glob(args['input_file_folder']+sw_type+"_real*.csv")[0]

    dest_traffic = pd.read_csv(dest_csv)
   
    src_data = {}
    jitter = 0.0

    for src_file in src_pcapng_files:
        host = src_file[src_file.find('h'):src_file.find('h')+2]
        
        paths = src_file.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(src_file.split("/")[0:-1])+"/"+filename+".csv"
       
        os.system("tshark -r "+src_file+" -T fields -e frame.number -e frame.time_epoch -e frame.len -e ip.src -e ip.dst -E header=y -E separator=, > "+filepath)
        src_data[host] = pd.read_csv(filepath)

    for k, src_traffic in src_data.items():
        ip_src = src_traffic.iloc[0]['ip.src']
        sub_dest_traffic = dest_traffic[dest_traffic['ip.src'] == ip_src]

        time_delay = np.subtract(sub_dest_traffic['frame.time_epoch'].to_numpy(), src_traffic['frame.time_epoch'].to_numpy())
        avg_latency = sum(time_delay)/len(time_delay)

        jit = 0.0
        iterations = len(time_delay)-1
        for idx in range(0, iterations):
            diff = fabs(time_delay[idx] - time_delay[idx+1])
            jit+=diff

        jitter = jitter + (jit/iterations)*ms

    return jitter/len(src_pcapng_files)



# Saves to a specific file rmse(%), byte count(Bytes) and jitter(ms) information
def save_rmse_and_telemetry_byte_count(args, sw_type, telemetry_pkts_count, rmse_expanded, rmse_simple, telemetry_byte_count, jitter):
    filepath = args['rmse_output_folder']+args['traffic_shape']+".csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a") as csvfile:
        headers = ['sw_type', 'sw_id', 'min_telemetry_push_time', 'experiment_time', 'packet_count', 'rmse_expanded', 'rmse_simple', 'telemetry_byte_count', 'jitter']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'sw_type': sw_type, 'sw_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                    'experiment_time': args['experiment_duration'], 'packet_count': telemetry_pkts_count, 
                        'rmse_expanded': rmse_expanded, 'rmse_simple': rmse_simple, 'telemetry_byte_count': telemetry_byte_count,
                        'jitter': jitter})



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
    telemetry_data = {}
    rmse_dict = {}

    for f in telemetry_files:
        sw_type = f.split("/")[-1].split(".")[0].split("_")[0]

        telemetry_x, telemetry_y, telemetry_byte_count = telemetry_traffic_data(f, args['switch_id'], args['unit'], args['experiment_duration'])
        
        real_traffic_file = glob.glob(args['input_file_folder']+sw_type+"_real*.csv")[0]
        real_xy = real_traffic_data(real_traffic_file, args['min_telemetry_push_time'], args['unit'], args['experiment_duration'])
        

        if telemetry_x[-1] < list(real_xy.keys())[-1]:
            telemetry_x.append(list(real_xy.keys())[-1])
            telemetry_y.append(telemetry_y[-1])


        telemetry_data[sw_type] = (telemetry_x, telemetry_y)
        real_expanded_y, tel_expanded_y= plot_line_graph(args, sw_type, (list(real_xy.keys()), list(real_xy.values())), telemetry_data.get(sw_type))

       
        print(sw_type, len(real_expanded_y), args['min_telemetry_push_time'], len(telemetry_y))

        rmse_expanded = sqrt(np.square(np.subtract(real_expanded_y, tel_expanded_y)).mean())
        rmse_expanded = rmse_expanded/(max(real_expanded_y) - min(real_expanded_y))
        print("rmse", rmse_expanded)


        ## Second way of finding values. Calculate real traffic in all points

        real_xy_ = real_traffic_data_tel(real_traffic_file, telemetry_x, args['unit'], args['experiment_duration'])
      
        merge = {**real_xy_, **real_xy}
        sorted_merge = dict(sorted(merge.items()))
        real_x = list(sorted_merge.keys())
        real_y = list(sorted_merge.values())

        tel_expanded_y = my_interpolation(real_x, telemetry_x, telemetry_y)

        rmse_simple = sqrt(np.square(np.subtract(real_y, tel_expanded_y)).mean())
        rmse_simple = rmse_simple/(max(real_y) - min(real_y))

        jitter = find_jitter(args, sw_type)

        save_rmse_and_telemetry_byte_count(args, sw_type, len(telemetry_x), rmse_expanded, rmse_simple, telemetry_byte_count, jitter)

  
if __name__ == '__main__':
    main()
