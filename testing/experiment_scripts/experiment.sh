#!/bin/bash

# Run the evaluation that compares DINT with sINT, LINT and a static method

experiment_type=$1
parent_script_path=$2
plotting_scripts_folder=$3
experiment_time=$4
min_time=$5

echo "Running $experiment_type experiment"
echo "Min push time is: $min_time"


evaluation_config_folder="$parent_script_path""/experiment_config/""$experiment_type""/"



# Subsitute total time in configuration files

extended_experiment_time=$(("$experiment_time" + 5))
echo $extended_experiment_time

for filename in "$evaluation_config_folder"*; do
	sed -i -e "s/\"time\":[^ ]*/\"time\":"$extended_experiment_time",/; 
				s/duration:[^ &]*/duration:"$extended_experiment_time"/;
					s/-t [^ &]*/-t "$extended_experiment_time"/; 
						s/-e [^ -]*/-e "$experiment_type"/;" $filename
done


cd ../src


#for i in static DINT sINT LINT; do

for i in static; do
	make clean
	p4_src="main_""$i"".p4"
	config_file="$i""_tcpreplay.json"
	make P4_SRC=$p4_src TEST_JSON=$evaluation_config_folder/$config_file
done




# Plot line graphs indicating the real link utilization and the one reported by the monitoring algorithm
cd $plotting_scripts_folder

python3 link_utilization_plots.py -e $experiment_type -d $experiment_time -m $min_time -s 4 -u m 	
python3 save_anomalous_flows_stats.py -e $experiment_type -d $experiment_time -m $min_time -s 4
