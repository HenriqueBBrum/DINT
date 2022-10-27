import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import csv
import argparse
import numpy as np
from collections import OrderedDict
import glob


# To plot comparison rmse/telemetry graphs used reverse=True in line 208 and reverse=False for parameters eval


metric_unit = {'b': 1, 'k':1000, 'm':1000000, 'g':1000000000}

hatches = ['\\', '.', 'x', '-', 'x', 'o', 'O', '.', '*']

lint_comparison = True


# plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["lightblue", "cornflowerblue", "mediumblue"]) 
# legend = ["α=1.25s", "α=1.5s", "α=2.0s"]

# plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["paleturquoise", "mediumslateblue", "navy"]) 
# legend = ["$\\it{k}$=2", "$\\it{k}$=4", "$\\it{k}$=8"]

plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["tab:orange", "tab:green", "tab:red", "tab:blue"]) 
legend = ["static", "sINT", "LINT", "DINT"]

font = {'family' : 'normal',
        'size'   : 13}

plt.rc('font', **font)


# Arguments that need to be informed for this program
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--file_folder', type=str, help="Folder with input files", required=True)
    parser.add_argument('-g', '--graphs_output_folder', type=str, help="Folder for output files", required=True)
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (b, k, m, g)", required=False, default="b")


    return vars(parser.parse_args())


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


# pos = postion in data to be used, mult is the scale factor
def crete_bar_graph_rects(data, pos, mult):
    sw_type_count = {}
    rects = {}
    labels = []
    for k, v in data.items():
        sw_type, push_time = k.split('_')

        if sw_type not in sw_type_count:
            sw_type_count[sw_type] = 1

        labels.append(push_time)
        if sw_type not in rects:
            rects[sw_type] = ([(sum(v[pos])/len(v[pos]))*mult], [np.std(v[pos])*mult])
        else:
            rects[sw_type][0].append((sum(v[pos])/len(v[pos]))*mult)
            rects[sw_type][1].append(np.std(v[pos])*mult)

            sw_type_count[sw_type] = sw_type_count[sw_type]+1

    return labels, rects, sw_type_count





# Plots a bar graph provied the destination file, tile, ylabel legend, the bars to be drwan, 
def plot_bar_graph(filepath, title, ylabel, labels, rects, sw_type_count, label_decimal_house):
    fig, ax = plt.subplots(figsize=(8,5))
    labels = list(dict.fromkeys(labels))

    sw_type_count_x_map = {}
    for k, v in sw_type_count.items():
        sw_type_count_x_map[k] = np.arange(1 if v == 0 else v)


    width=0.20
    ct = 0


    for k, v in rects.items():
        ct = ct +1

        x = sw_type_count_x_map[k]
        r = ax.bar(x+width*ct, v[0], width, yerr=v[1], label=k.capitalize(), hatch=hatches[ct-1], align='center', capsize=3, 
            error_kw={'elinewidth':1, 'alpha':0.65})

   
    add_value_labels(ax, label_decimal_house, y_spacing=-2)
    #ax.set_title(title)
    ax.set_ylabel(ylabel)
    

    max_ = 0
    for rect in rects.values(): # Get biggest value of all and make ylim 50% bigger
        local_max = max(rect[0])
        if(local_max > max_): max_ = local_max
    
    ax.set_ylim([0, max_+0.25*max_])

    ax.set_xticks(np.arange(0.5, len(labels), 1), list(dict.fromkeys(labels)))
    ax.set_xlabel('Telemetry insertion time (s)')

    h1, l1 = ax.get_legend_handles_labels()
    l1 = [x.upper() for x in l1]
    ax.legend(h1, l1, ncol=len(legend))

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(filepath)

    

# Plot all bar graphs (RMSE and telemetry overhead)
def plot_graphs(args, traffic_type, sw_id, total_time, data, unit):
    output_folder = args['graphs_output_folder']

    if len(data) <= 0:
        return

    rmse_exp_title = 'Measurement Error - '+'(SW'+sw_id+', '+total_time+'s)'
    rmse_exp_fp = output_folder+traffic_type+'_RMSE_'+sw_id+'_'+total_time.split('.')[0]+'s.png'
    plot_bar_graph(rmse_exp_fp, rmse_exp_title, 'NRMSE  (%)', *crete_bar_graph_rects(data, 1, 100), "1")


    byte_cnt_title = 'Telemetry Overhead S - '+'(SW'+sw_id+', '+total_time+'s)'
    byte_cnt_fp = output_folder+traffic_type+'_Tel_Overhead_'+sw_id+'_'+total_time.split('.')[0]+'s.png'
    plot_bar_graph(byte_cnt_fp, byte_cnt_title, 'Total Overhead (KBytes)', *crete_bar_graph_rects(data, 2, 1/metric_unit[args['unit']]), "1")


    # byte_cnt_title = 'Telemetry Overhead - '+'(SW'+sw_id+', '+total_time+'s)'
    # byte_cnt_fp = output_folder+traffic_type+'_Tel_Overhead_'+sw_id+'_'+total_time.split('.')[0]+'s.png'
    # plot_bar_graph(byte_cnt_fp, byte_cnt_title, 'Overhead compared to Total traffic (%)', *crete_bar_graph_rects(data, 3, 100), "3")


def main():
    args = parse_args()
    rmse_and_byte_cnt_files = glob.glob(args['file_folder']+"*.csv")

    for f in rmse_and_byte_cnt_files:
        traffic_type = (f.split("/")[-1].split(".")[0]).split("_")[0]

        my_dict = OrderedDict()
        graph_dict = OrderedDict()

        min_times = {}

        with open(f) as csvfile:
            data = csv.DictReader(csvfile, delimiter=',')
            for row in data:
                f_key = row['sw_id']+"_"+row['experiment_time']
                s_key = row['sw_type']+"_"+row['min_telemetry_push_time']

                min_times[row['min_telemetry_push_time']] = 1

                if (f_key+s_key) in my_dict:
                    count, rmse_list, byte_cnt_lst, percentage_byte_lst, h1_jitter_lst, h3_jitter_lst, h4_jitter_lst, previous_experiment_time = my_dict[(f_key+s_key)]

                    rmse_list.append(float(row['rmse']))
                    byte_cnt_lst.append(float(row['telemetry_byte_count']))
                    percentage_byte_lst.append(float(row['telemetry_percentage']))

                    updated_value = (float(count+1),rmse_list, byte_cnt_lst, percentage_byte_lst, h1_jitter_lst, h3_jitter_lst, h4_jitter_lst, previous_experiment_time+float(row['experiment_time']))

                    my_dict[(f_key+s_key)] = updated_value
                    graph_dict[f_key][s_key] = updated_value
                else:
                    value = (1, [float(row['rmse'])], [float(row['telemetry_byte_count'])], [float(row['telemetry_percentage'])], float(row['experiment_time']))
                    
                    my_dict[(f_key+s_key)] = value
                    if f_key not in graph_dict:
                        graph_dict[f_key] = {}
                        graph_dict[f_key][s_key] = value
                    else:
                        graph_dict[f_key][s_key] = value


        final_dict = OrderedDict()
        for f_k in graph_dict.keys():
            order = sorted(graph_dict[f_k].keys(), reverse=lint_comparison) # False for parameters
            ordered_keys = order

            sub = []
            for i in range(0, len(ordered_keys), len(min_times)):
                sub.extend(sorted(ordered_keys[i:i+len(min_times)], reverse=False))

            tmp_dict = {}
            for s_k in sub:
                tmp_dict[s_k] = graph_dict[f_key][s_k]


            final_dict[f_k] = tmp_dict

        for k, v in final_dict.items():
            sw_id, total_time = k.split('_')
            plot_graphs(args , traffic_type, sw_id, total_time, v, args['unit'])
           


if __name__ == '__main__':
    main()
