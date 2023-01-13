#!/bin/bash

# Run the evaluation that compares DINT with sINT, LINT and a static method
# This file does not modify the minimum telemetry values in the P4 source files so you need to change them manually in each run


echo "Running comparison evaluation"
echo "Min push time: $1"


config_files_folder=~/Documents/DINT/testing/config_files
scripts_input_dir=$2

cd ../src


#for i in static DINT sINT LINT; do

for i in static; do

	make clean
	p4_src="main_""$i"".p4"
	config_file="$i""_tcpreplay.json"
	make P4_SRC=$p4_src TEST_JSON=$config_files_folder/$config_file

done


cd ../testing/plotting_scripts


# Plot line graphs indicating the real link utilization and the one reported by the monitoring algorithm

python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m "$1" -s 2 -u "m" -t "Payless"
