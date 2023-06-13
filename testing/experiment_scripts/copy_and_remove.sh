#!/bin/bash

# Copy some of the contents of the testing/results folder to the <output_folder> and remove them afterwards

output_folder=$1
scripts_input_dir=~/Documents/DINT/testing/results



mkdir $output_folder

sudo rm $scripts_input_dir/traffic_data/*.pcapng


cp -r $scripts_input_dir/* $output_folder


sudo rm $scripts_input_dir/traffic_data/*
sudo rm $scripts_input_dir/graphs/*
sudo rm $scripts_input_dir/nrmse_overhead_data/*
sudo rm $scripts_input_dir/anomalous_flows_data/*


# Keep the file used in the comparion_plots.py script. When changing the experiment (comparson, alpha or k) delete the file
cp $output_folder/nrmse_overhead_data/* $scripts_input_dir/nrmse_overhead_data
cp $output_folder/anomalous_flows_data/* $scripts_input_dir/anomalous_flows_data
