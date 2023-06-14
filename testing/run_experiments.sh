#!/bin/bash

# This is the main file to execute any type of experiment. 
# With this file it's possible to execute multiple experiments of a a single configuration.


# parent_path is DINT's main folder
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

plotting_scripts_folder="$parent_path""/plotting_scripts"
output_dir="$parent_path""/results"

if [ $# -lt 4 ]
then 
	echo "No arguments provided"
	exit 1
fi

experiment_type=$1
final_output_folder=$2
experiment_time=$3
min_time=$4
loops=$5


echo $experiment_type
echo $final_output_folder
echo $experiment_time
echo $min_time


mkdir $output_dir
mkdir $output_dir/nrmse_overhead_data/
mkdir $output_dir/graphs/
mkdir $output_dir/traffic_data/
mkdir $output_dir/anomalous_flows_data/


# Substitutes the (min)telemtry push time in all p4 files autmatically according to the <min_time> parameter provided
min_time_microseg=$(echo "$min_time"*1000000 | bc)
min_time_microseg=$(echo "$min_time_microseg/1" | bc)

sed -i "s/const bit<48> tel_insertion_window = [^ ]*/const bit<48> tel_insertion_window = $min_time_microseg;/" ../src/main_static.p4 

sed -i "s/const bit<48> tel_insertion_min_window = [^ ]*/const bit<48> tel_insertion_min_window = $min_time_microseg;/" ../src/main_DINT.p4 
sed -i "s/const bit<48> obs_window = [^ ]*/const bit<48> obs_window = $min_time_microseg;/" ../src/main_DINT.p4 

sed -i "s/const bit<48> obs_window = [^ ]*/const bit<48> obs_window = $min_time_microseg;/" ../src/main_LINT.p4 



# Main experimnet running <loop> times
for ((i = 1; i <= $loops; i++ )); do
	echo $experiment_type
	# Runs experiment script, plots the network throughput results, and saves the NRMSE, telemetry overhead, classification performance and detection delay info
	/bin/bash ./experiment_scripts/experiment.sh $experiment_type $parent_path $plotting_scripts_folder $experiment_time $min_time

	# Create the folder for this iteration results within the provided <final_output_folder>
	name="results_mintime_""$min_time"_loop_"$i"
	mkdir "$final_output_folder""$experiment_type"
	folder="$final_output_folder""$experiment_type"/"$name"
	echo $folder

	# If it's the last iteration, plot the NMRSE and telemetry overhead graphs
	if [ "$i" -eq "$loops" ] 
	then
		python3 $plotting_scripts_folder/comparison_plots.py -e $experiment_type -u k
	fi

	# Copies the results in the temporary folder to to correponsing folder within the <final_output_folder> directory
	sh ./experiment_scripts/copy_and_remove.sh "$folder" 
done


stty erase ^H