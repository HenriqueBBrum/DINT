#!/bin/bash

echo "Running comparison evaluation"
echo "Min push time: $1"


config_files_folder=~/Documents/Masters/testing/config_files/comparison_evaluation
scripts_input_dir=$2

cd ../src 


for i in static DINT sINT LINT; do

	make clean
	p4_src="main_""$i"".p4"
	config_file="$i""_tcpreplay.json"
	make P4_SRC=$p4_src TEST_JSON=$config_files_folder/$config_file

done


cd ../testing/plotting_scripts



python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m "$1" -s 2 -u "m" -t "Payless" --plot_jitter


