#!/usr/bin/env python3


# Generates the NMRSE and Telemetry overhead bar plots with matplotlib.
# This script also calculates the average classification performance and detection delay of the elephant flow or micorbursts
# detection app. for each switch 'type' and saves to a CSV file 

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import csv
import argparse
import numpy as np
from collections import OrderedDict
import glob
import sys, os
import pandas as pd


sys.path.append("python_utils")
import constants


hatches = ['\\', '.', 'x', '-', 'x', 'o', 'O', '.', '*']

font = {'size'   : 13}

plt.rc('font', **font)
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["tab:orange", "tab:green", "tab:red", "tab:blue"]) 

# Arguments needed for this program
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--experiment_type', type=str, help = "The type of experiment (elephant_mice or microburst)", required=True)
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (b, k, m, g)", required=False, default="b")

    return vars(parser.parse_args())


def main(args):
    args = parse_args()

    nrmse_and_overhead_file = constants.NRMSE_OVERHEAD_DATA_FOLDER+args['experiment_type']+".csv"

    grouped_nrmse_and_overhead_data = group_nrmse_and_overhead_data(nrmse_and_overhead_file)
    avg_nrmse_and_overhead_data = avg_nmrse_and_overhead_results(grouped_nrmse_and_overhead_data)

    for first_key, graph_bars_data in avg_nrmse_and_overhead_data.items():
        switch_id, total_time = first_key.split('_')
        plot_nmrse_and_overhead_graphs(graph_bars_data , args['experiment_type'], switch_id, total_time, args['unit'])


    anomalous_flows_stats_file = constants.ANOMALOUS_FLOWS_DATA_FOLDER+args['experiment_type']+".csv"
    performance = anomalous_flows_stats(anomalous_flows_stats_file)

    performance_csv_path =  constants.ANOMALOUS_FLOWS_DATA_FOLDER+args['experiment_type']+"_performance_results.csv"
    performance.round(5).to_csv(performance_csv_path, mode='w',index=False)


# The nrmse_and_overhead_file file contains results from multiple types of experiments, switches, INT algorithms, and minimum telemetry push times.
# This function groups the information of each unique experiment
def group_nrmse_and_overhead_data(nrmse_and_overhead_file):
    grouped_data = {}

    df = pd.read_csv(nrmse_and_overhead_file, delimiter=',')
    for index, row in df.iterrows():
        f_key = str(row['switch_id'])+"_"+str(row['experiment_time'])+"-"
        s_key = row['switch_type']+"_"+str(row['min_telemetry_push_time'])
        composed_key = f_key+s_key

        if (composed_key in grouped_data):
            grouped_data[composed_key]['count'] = grouped_data[composed_key]['count'] + 1
            grouped_data[composed_key]['nrmse'].append(float(row['nrmse']))
            grouped_data[composed_key]['tel_overhead'].append(float(row['practical_tel_overhead']))
            grouped_data[composed_key]['tel_overhead_percent'].append(float(row['telemetry_percentage']))
        else:                
            grouped_data[composed_key] = {'count': 1, 'nrmse': [float(row['nrmse'])], 'tel_overhead': [float(row['practical_tel_overhead'])],
                                                                            'tel_overhead_percent': [float(row['telemetry_percentage'])]}

    return grouped_data

# For each unique experiment's data, calculates the average and standard deviation of the NMRSE and the telemetry overhead.
#
# Saves the average data from all types of switches and min telemetry times from the same experiment type and measured on the same switch 
# within the same dictionary
def avg_nmrse_and_overhead_results(grouped_nrmse_and_overhead_data):
    avg_nrmse_and_overhead_data = {}
    final_data = {}
    for composed_key, grouped_data in grouped_nrmse_and_overhead_data.items():
        first_key = composed_key.split("-")[0]
        second_key = composed_key.split("-")[1]

        avg_nrmse_and_overhead_data[composed_key] = {}
        if (first_key not in final_data):
            final_data[first_key] = {}

        for data_name, value in grouped_data.items():
            if(data_name == 'count'):
                continue

            data_array = grouped_data[data_name]
            unit = 1
            if(data_name == 'tel_overhead'):
                unit = constants.METRIC_UNIT[args['unit']]
                
            avg_nrmse_and_overhead_data[composed_key][data_name] =  ((sum(data_array)/grouped_data['count'])/unit, np.std(data_array)/unit)
        final_data[first_key][second_key] = avg_nrmse_and_overhead_data[composed_key]

    return final_data
 
# Plot all bar graphs (NRMSE and telemetry overhead)
def plot_nmrse_and_overhead_graphs(graph_bars_data, experiment_type, switch_id, total_time, unit):
    output_folder = constants.GRAPHS_FOLDER

    if len(graph_bars_data) <= 0:
        return

    y_tick_labels, switch_type_set = set(), set()
    nmrse_data, tel_overhead_data = {}, {}
    for second_key, graph_bar_data in graph_bars_data.items():
        switch_type, push_time = second_key.split('_')

        if(switch_type not in switch_type_set):
            nmrse_data[switch_type] = []
            tel_overhead_data[switch_type] = []

        y_tick_labels.add(float(push_time))
        switch_type_set.add(switch_type)

        nmrse_data[switch_type].append(graph_bar_data['nrmse']+ (float(push_time), ))
        tel_overhead_data[switch_type].append(graph_bar_data['tel_overhead'] + (float(push_time), ))

    ordered_y_tick_labels = sorted(y_tick_labels)
    nrmse_graph_title = 'Measurement Error - '+'(SW'+switch_id+', '+total_time+'s)'
    nrmse_graph_filepath = output_folder+experiment_type+'_NRMSE_'+switch_id+'_'+total_time.split('.')[0]+'s.png'
    plot_bar_graph(nrmse_graph_filepath, nrmse_graph_title, 'NRMSE  (%)', ordered_y_tick_labels, nmrse_data, len(switch_type_set), '3')


    overhead_graph_title = 'Telemetry Overhead S - '+'(SW'+switch_id+', '+total_time+'s)'
    overhead_graph_filepath = output_folder+experiment_type+'_Tel_Overhead_'+switch_id+'_'+total_time.split('.')[0]+'s.png'
    overhead_graph_ylabel = 'Total Overhead ('+unit.upper()+'Bytes)'
    plot_bar_graph(overhead_graph_filepath, overhead_graph_title, overhead_graph_ylabel, ordered_y_tick_labels, tel_overhead_data, len(switch_type_set), '1')


# Plots a bar graph
def plot_bar_graph(filepath, title, ylabel, y_tick_labels, bar_data, switch_type_count, label_decimal_house):
    fig, ax = plt.subplots(figsize=(8,5))

    n = int(switch_type_count/2)
    if(switch_type_count%2!=0): 
        pos = list(np.arange(-1*n, 0, 1))+[0]+list(np.arange(1, n+1, 1))
    else:
        pos = list(np.arange(-1*n, 0, 1))+list(np.arange(1, n+1, 1))

    width = 0.2
    pos = [p*width for p in pos] 
    max_, count = 0, 0
    x = np.arange(len(y_tick_labels))

    for switch_type, switch_type_data in bar_data.items():
        sorted_avg_list = sorted(switch_type_data, key=lambda tuple_: tuple_[2]) # Sort by min_push_time
        sorted_avg_list = [avg[0] for avg in sorted_avg_list] # List of all averages ordered by min_push_time

        sorted_sd_list = sorted(switch_type_data, key=lambda tuple_: tuple_[2]) # Sort by min_push_time
        sorted_sd_list = [sd[1] for sd in sorted_sd_list] # List of all sd ordered by min_push_time

        local_max = max(sorted_avg_list)
        if(local_max > max_): max_ = local_max


        r = ax.bar(x + pos[count], sorted_avg_list, width, yerr=sorted_sd_list, label=switch_type.capitalize(), hatch=hatches[count], capsize=3, 
            error_kw={'elinewidth':1, 'alpha':0.65})

        count+=1

    #ax.set_yscale('log')
    #plt.ticklabel_format(axis='both', style='sci', scilimits=(0,0))
    add_value_labels(ax, label_decimal_house, y_spacing=-2)
    ax.set_ylabel(ylabel)
    ax.set_ylim([0, max_+0.25*max_])

    ax.set_xticks(np.arange(0, len(y_tick_labels), 1), y_tick_labels)
    ax.set_xlabel('Telemetry insertion time (s)')

    h1, l1 = ax.get_legend_handles_labels()
    l1 = [x.upper() for x in l1]
    ax.legend(h1, l1, ncol=len(l1))

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(filepath)         

    
# Add a label on top of each bar plot
def add_value_labels(ax, decimal_format=2, spacing=8, y_spacing=0, color='black'):
    for rect in ax.patches:
        #print(rect)
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
     
        # Use Y value as label and format number with one decimal place
        str_ = "{:."+decimal_format+"f}"
        label = str_.format(y_value)
        # Create annotation
        ax.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(y_spacing, spacing),          # Vertically shift label by `spacing`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va='bottom',                      # Vertically align label for positive values ('bottom' for positive, 'top' for negatives).
            color=color
            )       


# Using the confusion matrix saved by each experiment calculates the accuracy, precision, recall, and F1-Score. 
# Also calculates the average and the standard deviation for the detection delay
def anomalous_flows_stats(anomalous_flows_stats_file):
    df = pd.read_csv(anomalous_flows_stats_file, delimiter=',')
    df['first_key'] = df['switch_id'].astype(str) + '_' + df['experiment_time'].astype(str)
    df['second_key'] = df['switch_type'] + '_' + df['min_telemetry_push_time'].astype(str)
    df['min_telemetry_push_time'].astype(str)

    common_colums = ['first_key', 'second_key', 'switch_type', 'min_telemetry_push_time']
    metrics = df.groupby(common_colums, as_index=False)[['throughput_nrmse', 'avg_delay']].agg([np.mean, np.std])
    perf_df =  df.groupby(common_colums, as_index=False)[['TP', 'FP', 'FN', 'TN']].mean()

    final_perf_df = perf_df[common_colums].copy()
    final_perf_df['accuracy'] = (perf_df['TP'] + perf_df['TN'])/(perf_df['TP'] + perf_df['TN'] + perf_df['FP'] + perf_df['FN'])
    final_perf_df['precision'] = perf_df['TP']/(perf_df['TP'] + perf_df['FP'])
    final_perf_df['recall'] = perf_df['TP']/(perf_df['TP'] + perf_df['FN'])
    final_perf_df['f1score'] = 2*((final_perf_df['precision']*final_perf_df['recall'])/(final_perf_df['precision']+final_perf_df['recall']))
    final_perf_df['delay_mean'] =  metrics['avg_delay'].reset_index()['mean']
    final_perf_df['delay_std'] =  metrics['avg_delay'].reset_index()['std']
    
    final_perf_df = final_perf_df.drop(['switch_type', 'min_telemetry_push_time'], axis=1)

    return final_perf_df


if __name__ == '__main__':
    args = parse_args()
    main(args)
