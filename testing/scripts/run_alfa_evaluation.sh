#!/bin/bash

echo "Running alfa evaluation"
echo "Min push time: $1"

config_files_folder=~/Documents/Masters/testing/config_files/parameter_evaluation
scripts_input_dir=$2



cd ../src 

for i in 125 150 200 250; do

	make clean
	p4_src="main_DINT-""$i"".p4"
	echo $p4_src
	make P4_SRC=$p4_src TEST_JSON=$config_files_folder/DINT_no_jitter_tcpreplay.json

	new_name="DINT-""$i"
	echo $new_name
	for file in $scripts_input_dir/pkts_output/DINT_*; do 
		echo $file
		mv $file ${file//DINT/$new_name} 
	done

done


cd ../testing/plotting_scripts

python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m "$1" -s 2 -u "m" -t "Payless"


