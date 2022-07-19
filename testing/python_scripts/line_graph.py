#!/usr/bin/env python3



# Usage: python3 line_graph.py -f ../input_files/ -m 1 -s 1 

import matplotlib.pyplot as plt
import math
import csv
import argparse
import json
import os
import numpy as np
import glob


metric_unit = {'k':1000, 'm':1000000, 'g':1000000000}

microseg = 1000000
telemetry_data_sz = 17
telelemetry_header_sz = 4

# Reads real data from csv file to find the amount of bytes transported each second
def real_traffic_data(filepath, unit):
    x, y = [0], [0]
    grouped_amt_bytes = 0
    current_time = 0
    previous_time = 0

    with open(filepath) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            # Keeps adding each pkt size until a second has elapsed. After summing up all bytes in that second, write to list
            if float(row['frame.time_relative']) - current_time <= 1:
                grouped_amt_bytes+=int(row['frame.len'])
            else:
                y.append(grouped_amt_bytes/metric_unit[unit])
                x.append(current_time+1)

                # If the next timestamp is not 1 second later, add zero bytes for each second until the next not empty second
                previous_time = current_time
                current_time = int(float(row['frame.time_relative']))
                diff = abs(current_time - previous_time)

                if(diff > 1):
                    y.extend([0]*(diff-1))
                    x.extend(list(range(previous_time+1, previous_time+diff)))

                grouped_amt_bytes=int(row['frame.len'])

        y.append(grouped_amt_bytes/metric_unit[unit])
        x.append(current_time+1)



    return x, y


# Reads telemetry data from custom txt file to find the amount of bytes transported each second
def telemetry_traffic_data(telemetry_file, switch_id, unit):
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
                    x.append(prev_time+time_window_s)
                    y.append((float(cols[2])/time_window_s)/metric_unit[unit])

                    prev_time+=time_window_s

                hop_cnt-=1

    return x, y, telemetry_byte_count


# Saves information about 
def save_rmse_and_telemetry_byte_count(args, sw_type, real_y_expanded, telemetry_y_expanded, telemetry_byte_count, telemetry_pkts_count):
    rmse = math.sqrt(np.square(np.subtract(real_y_expanded, telemetry_y_expanded)).mean())
    max_ = max(sorted(set(real_y_expanded))[-1], sorted(set(telemetry_y_expanded))[-1])

    filepath = args['output_folder']+args['traffic_shape']+".csv"
    file_exists = os.path.isfile(filepath)
    y_set = sorted(set(real_y_expanded))
    with open(filepath, "a") as csvfile:
        headers = ['traffic_shape', 'sw_type', 'rmse', 'telemetry_byte_count', 'packet_count', 'min_telemetry_push_time', 'experiment_time']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'traffic_shape': args['traffic_shape'], 'sw_type': sw_type, 'rmse': rmse/(max_-sorted(set(real_y_expanded))[0]), 
                        'telemetry_byte_count': telemetry_byte_count, 'packet_count': telemetry_pkts_count,
                        'min_telemetry_push_time': args['min_telemetry_push_time'], 'experiment_time': args['experiment_duration']})


def plot_line_graph(args, sw_type, real_data, telemetry_data):
    real_x, real_y = real_data
    telemetry_x, telemetry_y = telemetry_data
    x_combined = np.sort(np.concatenate([real_x, telemetry_x]))

    i, j = 0, 0
    telemetry_y_expanded = []
    while j<len(telemetry_x) and i<len(x_combined):
        if x_combined[i] > telemetry_x[j]:
            j+=1
        else:
            telemetry_y_expanded.append(telemetry_y[j])
            i+=1

    i, j = 0, 0
    real_y_expanded = []
    while j<len(real_x) and i<len(x_combined):
        if int(x_combined[i]) == real_x[j]:
            real_y_expanded.append(real_y[j])
            i+=1
        else:
            j+=1

    plot1 = plt.figure(1)
    plt.plot(x_combined, real_y_expanded, color="b", label='Real')
    plt.plot(x_combined, telemetry_y_expanded, color="r", label='Telemetry')
    plt.plot(telemetry_x, telemetry_y, 'o', color='black');
    plt.fill_between(x_combined, real_y_expanded, telemetry_y_expanded, facecolor='black', alpha=0.2, hatch="X")

    # plt.fill_between(x_combined, real_y_expanded, telemetry_y_expanded, where=(telemetry_y_expanded > real_y_expanded), interpolate=True, facecolor='red', alpha=0.2)
    # plt.fill_between(x_combined, real_y_expanded, telemetry_y_expanded, where=(telemetry_y_expanded <= real_y_expanded), interpolate=True, facecolor='blue', alpha=0.2)

    plt.xlabel("time(sec)")
    plt.ylabel("link utilization("+args['unit'].upper()+"B/secs)");
    plt.title('Real link X Telemetry link (min_telemetry_push_time = '+str(args['min_telemetry_push_time'])+' sec)')
    plt.gca().legend()
    plot1.savefig(args['output_folder']+args['traffic_shape']+'_Real_X_Telemetry_'+sw_type+'_sw'+args['switch_id']+'.png')
    plot1.clf() 
    # plt.show()

    return real_y_expanded, telemetry_y_expanded


def parse_args():

    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-i', '--file_folder', type=str, help="Folder with input files")
    parser.add_argument('-o', '--output_folder', type=str, help="Folder for output files")
    parser.add_argument('-d', '--experiment_duration', type=float, help="Duration of the experiment'")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in the 'p4' files")
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
        telemetry_x, telemetry_y, telemetry_byte_count = telemetry_traffic_data(f, args['switch_id'], args['unit'])
        sw_type = f.split("/")[-1].split(".")[0].split("_")[0]

        real_traffic_file = glob.glob(args['file_folder']+sw_type+"_real*.csv")[0]
        real_x, real_y = real_traffic_data(real_traffic_file, args['unit'])

        telemetry_data[sw_type] = (telemetry_x, telemetry_y)

        if telemetry_x[-1] < real_x[-1]:
            telemetry_x.append(real_x[-1])
            telemetry_y.append(telemetry_y[-1])


        real_y_expanded, telemetry_y_expanded = plot_line_graph(args, sw_type, (real_x, real_y), telemetry_data.get(sw_type))

        save_rmse_and_telemetry_byte_count(args, sw_type, real_y_expanded, telemetry_y_expanded, telemetry_byte_count, len(telemetry_x))

    #plot_rmse_graph(args, rmse_dict)

  
if __name__ == '__main__':
    main()
