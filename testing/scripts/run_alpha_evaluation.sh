#!/bin/bash

# Run the evaluation of the alpha parameter for the values 1.25, 1.50 and 2.0
# This file does not modify the minimum telemetry values in the P4 source files so you need to change them manually in each run


echo "Running alpha evaluation"
echo "Min push time: $1"

config_files_folder=~/Documents/DINT/testing/config_files
scripts_input_dir=$2



cd ../src

for i in 125 150 200; do

	make clean
	p4_src="main_DINT-""$i"".p4"
	make P4_SRC=$p4_src TEST_JSON=$config_files_folder/DINT_tcpreplay.json

	# Rename the pcap and telemetry files since they all have the same name
	new_name="DINT-""$i""_"
	for file in $scripts_input_dir/pkts_output/DINT_*; do
		echo $file
		mv $file ${file//DINT_/$new_name} 
	done

done


cd ../testing/plotting_scripts


# Plot line graphs indicating the real link utilization and the one reported by the monitoring algorithm

python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m "$1" -s 2 -u "m" -t "Payless"
