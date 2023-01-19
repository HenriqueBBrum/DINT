#!/bin/bash

# This is the main file to execute any type of experiment. 
# With this file it's possible to execute multiple experiments of a a single configuration.


testing_scripts_folder=~/Documents/DINT/testing/plotting_scripts
scripts_input_dir=~/Documents/DINT/testing/results


evaluation_file=$1
final_output_folder=$2
min_time=$3
loops=$4

echo "$1"
echo "$2"
echo "$3"

mkdir $scripts_input_dir
mkdir $scripts_input_dir/graphs_input/
mkdir $scripts_input_dir/graphs_output/
mkdir $scripts_input_dir/pkts_output/



for ((i = 1; i <= "$loops"; i++ )); do
	/bin/bash ./"$evaluation_file" "$min_time" $scripts_input_dir
	name="results_""$min_time""_$i"
	folder="$final_output_folder""$name"
	echo $folder

	# if [ "$i" -eq "$loops" ] 
	# then
	# 	python3 $testing_scripts_folder/comparison_plots.py -i $scripts_input_dir/graphs_input/ -g $scripts_input_dir/graphs_output/ -e $evaluation_file
	# fi

	#sh ./scripts/copy_and_remove.sh "$folder" 
done
