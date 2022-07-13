import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import math
import csv
import argparse
import os
import numpy as np
from collections import OrderedDict

def add_value_labels(ax, spacing=4, y_spacing=0, color='gray'):
    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        # Number of points between bar and label. Change to your liking.
        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        label = "{:.1f}".format(y_value)

        # Create annotation
        ax.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(y_spacing, space),          # Vertically shift label by `space`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va=va,
            color=color)                      # Vertically align label differently for
                                        # positive and negative values.


def plot_rmse_graph(args, data_dict):
    if len(data_dict) <= 0:
        return

    x = np.arange(len(data_dict))
    width=0.15

    fig, ax1 = plt.subplots()

    color = 'tab:orange'
    ax1.set_ylabel('RMSE (%)')
    ax1.tick_params(axis='y', labelcolor=color)
    rects1 = ax1.bar(x-width, [(value[1]/value[0])*100 for value in data_dict.values()], width*2, label='Measurement Error', color=color, hatch='\\')
    add_value_labels(ax1, y_spacing=-2, color='orange')

    ax2 = ax1.twinx()
    color = 'tab:green'
    ax2.set_ylabel('Byte overhead ('+args.traffic_shape.split("_")[-1]+' secs)')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim([0, 3200])
    rects2 = ax2.bar(x + width, [value[2]/value[0] for value in data_dict.values()], width*2, label='Telemetry Overhead', color=color, hatch="/")
    add_value_labels(ax2, y_spacing=6, color='green')

    ax1.set_title('Telemetry overhead and measurement error')
    ax1.set_xticks(x)
    ax1.set_ylim([0, 26])
    start, end = ax1.get_ylim()
    ax1.yaxis.set_ticks(np.arange(start, end,5))

    ax1.set_xticklabels(data_dict.keys())
    ax1.set_xlabel('Telemetry push time (s)')

    #print(labels)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax2.legend(h1+h2, l1+l2, loc='upper center')

    #fig.tight_layout()  # otherwise the right y-label is slightly clipped



    fig.savefig('graphs/'+args.traffic_shape+'_RMSE_X_Byte.png', dpi=270)
    plt.show()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', type=str, help = "Csv file with data")
    parser.add_argument('traffic_shape', type=str, help = "Traffic type")


    args = parser.parse_args()

    my_dict = OrderedDict()

    with open(args.file_name) as csvfile:
        data = csv.DictReader(csvfile, delimiter=',')
        for row in data:
            if row['min_telemetry_push_time'] in my_dict:
                count, previous_rmse, previous_byte_count, previous_experiment_time = my_dict[row['min_telemetry_push_time']]
                my_dict[row['min_telemetry_push_time']] = (float(count+1), previous_rmse+float(row['rmse']), previous_byte_count+float(row['byte_count']),
                            previous_experiment_time+float(row['experiment_time']))
            else:
                my_dict[row['min_telemetry_push_time']] = (1, float(row['rmse']), float(row['byte_count']), float(row['experiment_time']))
    final_dict = OrderedDict()
    for i in sorted (my_dict):
        final_dict[i] = my_dict[i]

    plot_rmse_graph(args, final_dict)




if __name__ == '__main__':
    main()
