#!/usr/bin/env python3

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
tel_data_sz = 17
telelemetry_header_sz = 4

# Reads real data from csv file to find amount of bytes transported each second
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

# def read_data_from_telemtry_reported_traffic(telemetry_pkts_csv, args):
#     x_telemetry, y_telemetry = [0], [0]

    # with open(telemetry_pkts_csv) as csvfile:
    #     prev_time = 0
    #     data = csv.DictReader(csvfile, delimiter=',')
    #     for row in data:
    #         time_frame = row["hbb.time_frame"]
    #         amt_bytes = row["hbb.amt_bytes"]

    #         x_telemetry.append(prev_time+(int(time_frame,10)/microseg))
    #         y_telemetry.append((int(amt_bytes,10)/int(time_frame,10)*(microseg))/1000)


    #         prev_time += (int(time_frame, 10)/microseg)

    # return x_telemetry, y_telemetry

def telemetry_reported_traffic_data(telemetry_file, switch_id, unit):
    x, y = [0], [0]
    hop_cnt = 0
    prev_time = 0

    with open(telemetry_file, 'r') as txt_file:
        for line in txt_file:
            cols = line.split(",")
            if hop_cnt == 0:
                hop_cnt = int(cols[1],10)
            else:
                if(cols[0]==switch_id):
                    time_window_s = (int(cols[-1],10)-int(cols[-2],10))/(microseg)
                    x.append(prev_time+time_window_s)
                    y.append((float(cols[2])/time_window_s)/metric_unit[unit])

                    prev_time+=time_window_s

                hop_cnt-=1

    return x, y


def save_rmse_and_byte_count_data(args, y_fill, y_tel_fill, amt_tel_packets, experiment_time):
    rmse = math.sqrt(np.square(np.subtract(y_fill, y_tel_fill)).mean())
    max_ = max(sorted(set(y_fill))[-1], sorted(set(y_tel_fill))[-1])

    filepath = "input_files/rmse_bytes_"+args.traffic_shape+".csv"
    file_exists = os.path.isfile(filepath)
    y_set = sorted(set(y_fill))
    with open(filepath, "a") as csvfile:
        headers = ['rmse', 'byte_count', 'packet_count', 'min_telemetry_push_time', 'experiment_time']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'rmse': rmse/(max_-sorted(set(y_fill))[0]), 'byte_count': telemetry_size*amt_tel_packets, 'packet_count': amt_tel_packets,
                        'min_telemetry_push_time': args.min_telemetry_push_time_time, 'experiment_time': experiment_time})


def plot_rmse():
    return None


def plot_line_graph():
    return None



def parse_args():

    parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
    parser.add_argument('-f', '--file_folder', type=str, help="Folder with input files")
    parser.add_argument('-m', '--min_telemetry_push_time', type=float, help="Minimum polling time in seconds used in 'main_dynamic.p4'")
    parser.add_argument('-s', '--switch_id', type=str, help="Switch id to be compared")
    parser.add_argument('-t', '--traffic_shape', type=str, help = "RMSE traffic shape name", required=False)
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (k, m, g)", required=False, default="k")


    return vars(parser.parse_args())


def main():
    args = parse_args()
    pcapng_files = glob.glob(args['file_folder']+"*.pcapng")
    for f in pcapng_files:
        paths = f.split("/")
        filename = paths[-1].split(".")[0]
        filepath = "/".join(f.split("/")[0:-1])+"/"+filename+".csv"
       
        os.system("tshark -r "+f+" -T fields -e frame.number -e frame.time_epoch -e frame.time_relative -e frame.len -E header=y -E separator=, > "+filepath)


    real_traffic_file = glob.glob(args['file_folder']+"*real*.csv")[0]
    print(real_traffic_file)

    x_real, y_real = real_traffic_data(real_traffic_file, args['unit'])
    telemetry_files = glob.glob(args['file_folder']+"*.txt")
    telemetry_data = {}
    
    for f in telemetry_files:
        x_tel, y_tel = telemetry_reported_traffic_data(f, args['switch_id'], args['unit'])
        filename = f.split("/")[-1].split(".")[0].split("_")[0]
        telemetry_data[filename] = (x_tel, y_tel)

        if x_tel[-1] < x_real[-1]:
            x_tel.append(x_real[-1])
            y_tel.append(y_tel[-1])

    #     print(filename)
    #     print(x_tel)
    #     print(y_tel)
    #     print(filename)


    print(x_real)
    print(y_real)

    filename = 'static'
    x_tel, y_tel = telemetry_data.get(filename)
    print(x_tel)
    x_combined = np.sort(np.concatenate([x_real, x_tel]))
    print(x_combined)

    i, j = 0, 0
    y_tel_fill = []
    while j<len(x_tel) and i<len(x_combined):
        if x_combined[i] > x_tel[j]:
            j+=1
        else:
            y_tel_fill.append(y_tel[j])
            i+=1

    # print(y_tel_fill)

    i, j = 0, 0
    y_fill = []
    while j<len(x_real) and i<len(x_combined):
        if x_combined[i] <= x_real[j]:
            y_fill.append(y_real[j])
            i+=1
        else:
            if j == len(x_real)-1:
                y_fill.append(y_real[j])
                i+=1
            j+=1
    # print(y_fill)
    print(len(y_fill), len(y_tel_fill), len(x_combined))
    plot1 = plt.figure(1)
    plt.plot(x_combined, y_fill, color="b", label='Real')
    plt.plot(x_combined, y_tel_fill, color="r", label='Telemetry')
    plt.plot(x_tel, y_tel, 'o', color='black');
    plt.fill_between(x_combined, y_fill, y_tel_fill, facecolor='black', alpha=0.2, hatch="X")

    # plt.fill_between(x_combined, y_fill, y_tel_fill, where=(y_tel_fill > y_fill), interpolate=True, facecolor='red', alpha=0.2)
    # plt.fill_between(x_combined, y_fill, y_tel_fill, where=(y_tel_fill <= y_fill), interpolate=True, facecolor='blue', alpha=0.2)

    plt.xlabel("time(sec)")
    plt.ylabel("link utilization("+args['unit'].upper()+"B/secs)");
    plt.title('Real link X Telemetry link (min_telemetry_push_time = '+str(args['min_telemetry_push_time'])+' sec)')
    plt.gca().legend()
    # save_rmse_and_byte_count_data(args, y_fill[2:], y_tel_fill[2:], len(y_tel), x_real[-1])
    plot1.savefig(args['traffic_shape']+'_Real_X_Telemetry_'+filename+'_sw'+args['switch_id']+'.png')
    plt.show()



if __name__ == '__main__':
    main()
