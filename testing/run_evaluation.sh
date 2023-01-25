#!/bin/bash

# This is the main file to execute any type of experiment. 
# With this file it's possible to execute multiple experiments of a a single configuration.


parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

plotting_scripts_folder="$parent_path""/plotting_scripts"
output_dir="$parent_path""/results"

if [ $# -lt 4 ]
then 
	echo "No arguments provided"
	exit 1
fi


evaluation_file=$1
final_output_folder=$2
min_time=$3
loops=$4



echo "$1"
echo "$2"
echo "$3"


mkdir $output_dir
mkdir $output_dir/rmse_overhead_input/
mkdir $output_dir/graphs_output/
mkdir $output_dir/pkts_output/


for ((i = 1; i <= "$loops"; i++ )); do
	/bin/bash ./"$evaluation_file" $parent_path $plotting_scripts_folder "$min_time" 

	name="results_""$min_time""_$i"
	folder="$final_output_folder""$name"
	echo $folder

	# if [ "$i" -eq "$loops" ] 
	# then
	# 	python3 $plotting_scripts_folder/comparison_plots.py -i $output_dir/graphs_input/ -g $output_dir/graphs_output/ -e $evaluation_file
	# fi

	#sh ./scripts/copy_and_remove.sh "$folder" 
done
