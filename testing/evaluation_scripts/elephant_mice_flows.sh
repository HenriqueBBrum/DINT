#!/bin/bash

# Run the evaluation that compares DINT with sINT, LINT and a static method
# This file does not modify the minimum telemetry values in the P4 source files so you need to change them manually in each run


main_script_path=$1

echo "Running elephant mice evaluation"
echo "Min push time is: $3"


plotting_scripts_folder=$2
evaluation_config_folder="$main_script_path""/evaluation_config/elephant_mice"

cd ../src


#for i in static DINT sINT LINT; do

for i in static; do
	make clean
	p4_src="main_""$i"".p4"
	config_file="$i"".json"
	make P4_SRC=$p4_src TEST_JSON=$evaluation_config_folder/$config_file
done




# Plot line graphs indicating the real link utilization and the one reported by the monitoring algorithm

python3 $plotting_scripts_folder/link_utilization_plots.py -d 60 -m "$2" -s 2 -u "m" -t "Payless"
