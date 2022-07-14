#!/usr/bin/env python3

import matplotlib.pyplot as plt
import math
import csv
import argparse
import json
import os
import numpy as np

microseg = 1000000
telemetry_size = 15




def read_data_from_real_traffic_csv(args):
    x_real, y_real = [0], [0]
    grouped_amt_bytes = 0
    aux_time = 0
    aux = 0

    with open(args.real_traffic_file) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            if float(row['Time']) - aux_time <= 1:
                grouped_amt_bytes+=int(row['Length'])
                aux = 1
            else:
                if float(row['Time']) - aux_time > 1 and aux == 0:
                    y_real.append(0)
                    aux = 0
                else:
                    y_real.append(grouped_amt_bytes/1000)
                    grouped_amt_bytes=int(row['Length'])
                    aux = 0

                aux_time+=1
                x_real.append(aux_time)



    return x_real, y_real

def read_data_from_telemtry_reported_traffic(telemetry_pkts_csv, args):
    x_telemetry, y_telemetry = [0], [0]

    with open(telemetry_pkts_csv) as csvfile:
        prev_time = 0
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            time_frame = row["hbb.time_frame"]
            amt_bytes = row["hbb.amt_bytes"]

            x_telemetry.append(prev_time+(int(time_frame,10)/microseg))
            y_telemetry.append((int(amt_bytes,10)/int(time_frame,10)*(microseg))/1000)


            prev_time += (int(time_frame, 10)/microseg)

    return x_telemetry, y_telemetry



def save_rmse_and_byte_count_data(args, y_fill, y_tel_fill, amt_tel_packets, experiment_time):
    rmse = math.sqrt(np.square(np.subtract(y_fill, y_tel_fill)).mean())
    max_ = max(sorted(set(y_fill))[-1], sorted(set(y_tel_fill))[-1])

    file_path = "input_files/rmse_bytes_"+args.traffic_shape+".csv"
    file_exists = os.path.isfile(file_path)
    y_set = sorted(set(y_fill))
    with open(file_path, "a") as csvfile:
        headers = ['rmse', 'byte_count', 'packet_count', 'min_telemetry_push_time', 'experiment_time']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow({'rmse': rmse/(max_-sorted(set(y_fill))[0]), 'byte_count': telemetry_size*amt_tel_packets, 'packet_count': amt_tel_packets,
                        'min_telemetry_push_time': args.min_telemetry_push_time_time, 'experiment_time': experiment_time})



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('telemery_pcapng_file', type=str, help = "Pcapng file with info about packets with my custom protocol (hbb)")
    parser.add_argument('real_traffic_file', type=str, help = "CSV file containing all packets sent")
    parser.add_argument('traffic_shape', type=str, help = "RMSE traffic shape name")
    parser.add_argument('min_telemetry_push_time_time', type=float, help = "Minimum polling time in seconds used in 'main.p4'")

    args = parser.parse_args()
    aux_1 = args.telemery_pcapng_file.split("/")

    aux_1.pop()
    telemetry_pkts_csv = ("/".join(aux_1))+"/cloned_pkts_with_tel.csv"

    os.system("tshark -r "+args.telemery_pcapng_file+" -T fields -e frame.number -e hbb.amt_bytes -e hbb.time_frame -E header=y -E separator=, > "+telemetry_pkts_csv)


    x_real, y_real = read_data_from_real_traffic_csv(args)
    x_telemetry, y_telemetry = read_data_from_telemtry_reported_traffic(telemetry_pkts_csv, args)
    if x_telemetry[-1] < x_real[-1]:
        x_telemetry.append(x_real[-1])
        y_telemetry.append(y_telemetry[-1])

    x_combined = np.sort(np.concatenate([x_real, x_telemetry]))

    i, j = 0, 0
    y_tel_fill = []
    while j<len(x_telemetry) and i<len(x_combined):
        if x_combined[i] > x_telemetry[j]:
            j+=1
        else:
            y_tel_fill.append(y_telemetry[j])
            i+=1

    i, j = 0, 0
    y_fill = []
    while j<len(x_real) and i<len(x_combined):
        if x_combined[i] <= x_real[j]:
            y_fill.append(y_real[j])
            i+=1
        else:
            j+=1

    plot1 = plt.figure(1)
    plt.plot(x_combined, y_fill, color="b", label='Real')
    plt.plot(x_combined, y_tel_fill, color="r", label='Telemetry')
    plt.plot(x_telemetry, y_telemetry, 'o', color='black');
    plt.fill_between(x_combined, y_fill, y_tel_fill, facecolor='black', alpha=0.2, hatch="X")

    # plt.fill_between(x_combined, y_fill, y_tel_fill, where=(y_tel_fill > y_fill), interpolate=True, facecolor='red', alpha=0.2)
    # plt.fill_between(x_combined, y_fill, y_tel_fill, where=(y_tel_fill <= y_fill), interpolate=True, facecolor='blue', alpha=0.2)

    plt.xlabel("time(sec)")
    plt.ylabel("link utilization(KB/secs)");
    plt.title('Real link X Telemetry link (min_telemetry_push_time = '+str(args.min_telemetry_push_time_time)+' sec)')
    plt.gca().legend()

    save_rmse_and_byte_count_data(args, y_fill[2:], y_tel_fill[2:], len(y_telemetry), x_real[-1])
    plot1.savefig('graphs/'+args.traffic_shape+'_Real_X_Telemetry.png', dpi=270)
    plt.show()



if __name__ == '__main__':
    main()
