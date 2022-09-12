#!/usr/bin/env python3

import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import math
import csv
import argparse
import json
import os
import numpy as np
import pandas as pd
import glob

metric_unit = {'k':1000, 'm':1000000, 'g':1000000000}

microseg = 1000000
telemetry_data_sz = 21
telelemetry_header_sz = 4

# Reads real data from csv file to find the amount of bytes transported each second
def real_traffic_data(filepath, unit, experiment_duration):
    xy = {0.0: 0.0}
    grouped_amt_bytes = 0
    current_time = 0
    previous_time = 0

    with open(filepath) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            if(float(row['frame.time_relative']) >= experiment_duration):
                break

            # Keeps adding each pkt size until a second has elapsed. After summing up all bytes in that second, write to list
            if(float(row['frame.time_relative']) - current_time <= 1):
                grouped_amt_bytes+=int(row['frame.len'])
            else:
                xy[current_time+1] = grouped_amt_bytes/metric_unit[unit]
              
                # If the next timestamp is not 1 second later, add zero bytes for each second until the next not empty second
                previous_time = current_time
                current_time = int(float(row['frame.time_relative']))
                diff = abs(current_time - previous_time)

                if(diff > 1):
                    for i in range(previous_time+2, previous_time+diff+1):
                        xy[i] = 0
                   

                grouped_amt_bytes=int(row['frame.len'])

        xy[current_time+1] = grouped_amt_bytes/metric_unit[unit]
       
    return xy


# Reads real data from csv file to find the amount of bytes transported each second
def real_traffic_data_(filepath, telemetry_x, unit, experiment_duration):
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

            #print(i, i - telemetry_x[idx-1], ct, ct*1442, ct*1442/(i - telemetry_x[idx-1]))

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

def save_rmse_and_telemetry_byte_count(args, sw_type, rmse_expanded, rmse_simple, telemetry_byte_count, telemetry_pkts_count):
    filepath = args['rmse_output_folder']+args['traffic_shape']+".csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a") as csvfile:
        headers = ['sw_type', 'sw_id', 'min_telemetry_push_time', 'experiment_time', 'packet_count', 'rmse_expanded', 'rmse_simple', 'telemetry_byte_count']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'sw_type': sw_type, 'sw_id':args['switch_id'], 'min_telemetry_push_time': args['min_telemetry_push_time'], 
                    'experiment_time': args['experiment_duration'], 'packet_count': telemetry_pkts_count, 
                        'rmse_expanded': rmse_expanded, 'rmse_simple': rmse_simple, 'telemetry_byte_count': telemetry_byte_count})


def plot_line_graph(args, sw_type, real_data, telemetry_data):
    real_x, real_y = real_data
    telemetry_x, telemetry_y = telemetry_data

    i, j = 0, 0
    telemetry_y_expanded = []
    while j<len(telemetry_x) and i<len(real_x):
        if real_x[i] > telemetry_x[j]:
            j+=1
        else:
            telemetry_y_expanded.append(telemetry_y[j])
            i+=1

    plot1 = plt.figure(1)

    temp_real_y_expanded = [x * 8 for x in real_y]
    temp_telemetry_y_expanded = [x * 8 for x in telemetry_y_expanded]
    temp_telemetry_y = [x * 8 for x in telemetry_y]

    plt.plot(real_x, temp_real_y_expanded, color="b", label='Real')
    plt.plot(real_x, temp_telemetry_y_expanded, color="r", label='Telemetry')

    plt.plot(telemetry_x[1:-1], temp_telemetry_y[1:-1], 'o', color='black')
    plt.plot([telemetry_x[0], telemetry_x[-1]] , [temp_telemetry_y[0], temp_telemetry_y[-1]], '*', color='red');
    plt.plot([real_x[0], real_x[-1]] , [temp_real_y_expanded[0], temp_real_y_expanded[-1]], '*', color='blue');

   
    plt.fill_between(real_x, temp_real_y_expanded, temp_telemetry_y_expanded, interpolate=True, facecolor='black', alpha=0.2, hatch="X")


    plt.xlabel("Time(sec)")
    plt.ylabel("Link utilization ("+args['unit'].upper()+"bits/secs)");
    plt.title('Real link X Telemetry link')
    plt.yticks(np.arange(0,5,0.5))

    plt.gca().legend()

    # plt.show()

    plot1.savefig(args['graphs_output_folder']+args['traffic_shape']+'_Real_X_Telemetry_'+sw_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 

    return real_y, telemetry_y_expanded


def parse_args():

    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-i', '--file_folder', type=str, help="Folder with input files")
    parser.add_argument('-g', '--graphs_output_folder', type=str, help="Folder for output files")
    parser.add_argument('-r', '--rmse_output_folder', type=str, help="Folder for output files")
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
    parser.add_argument('--min_sINT_frequency', type=float, help="Minimum telemetry insertion frequency in a packet", required=False)
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-t', '--traffic_shape', type=str, help = "RMSE traffic shape name", required=False, default="no_type")
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (k, m, g)", required=False, default="k")


    return vars(parser.parse_args())


def main():
    args = parse_args()

    # Transforms all pcapng files (real traffic) to csv files with the folowing headers: frame.number, frame.time_epoch, frame.time_relative, frame.len
    pcapng_files = glob.glob(args['file_folder']+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(f.split("/")[0:-1])+"/"+filename+".csv"
       
        os.system("tshark -r "+f+" -T fields -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -E header=y -E separator=, > "+filepath)

   
    telemetry_files = glob.glob(args['file_folder']+"*.txt")
    telemetry_data = {}
    rmse_dict = {}

    for f in telemetry_files:
        sw_type = f.split("/")[-1].split(".")[0].split("_")[0]

        telemetry_x, telemetry_y, telemetry_byte_count = telemetry_traffic_data(f, args['switch_id'], args['unit'], args['experiment_duration'])
        real_traffic_file = glob.glob(args['file_folder']+sw_type+"_real*.csv")[0]
        real_xy = real_traffic_data(real_traffic_file, args['unit'], args['experiment_duration'])
        real_xy_ = real_traffic_data_(real_traffic_file, telemetry_x, args['unit'], args['experiment_duration'])
       
        merge = {**real_xy_, **real_xy}

        sorted_merge = dict(sorted(merge.items()))


        if telemetry_x[-1] < list(real_xy.keys())[-1]:
            telemetry_x.append(list(real_xy.keys())[-1])
            telemetry_y.append(telemetry_y[-1])
            real_xy_[list(real_xy.keys())[-1]] = telemetry_y[-1]


        telemetry_data[sw_type] = (telemetry_x, telemetry_y)


        real_y_expanded, telemetry_y_expanded= plot_line_graph(args, sw_type, (list(sorted_merge.keys()), list(sorted_merge.values())), telemetry_data.get(sw_type))

        print(sw_type, len(real_y_expanded), args['min_telemetry_push_time'], len(telemetry_y))

        rmse_expanded = math.sqrt(np.square(np.subtract(real_y_expanded, telemetry_y_expanded)).mean())
        print(rmse_expanded,rmse_expanded/(max(real_y_expanded) - min(real_y_expanded)))
        rmse_expanded = rmse_expanded/(max(real_y_expanded) - min(real_y_expanded))

        real_y = list(real_xy_.values())



        rmse_simple = math.sqrt(np.square(np.subtract(real_y, telemetry_y)).mean())
        print(rmse_simple, rmse_simple/(max(real_y) - min(real_y)))
        rmse_simple = rmse_simple/(max(real_y) - min(real_y))


        save_rmse_and_telemetry_byte_count(args, sw_type, rmse_expanded, rmse_simple, telemetry_byte_count, len(telemetry_x))

  
if __name__ == '__main__':
    main()
