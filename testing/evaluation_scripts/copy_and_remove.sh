#!/bin/bash

# Copy some of the contents of the testing/results folder and remove them afterwards

output_folder=$1
scripts_input_dir=~/Documents/DINT/testing/results



mkdir $output_folder

sudo rm $scripts_input_dir/pkts_output/*.csv


cp -r $scripts_input_dir/* $output_folder


sudo rm $scripts_input_dir/graphs_output/*
sudo rm $scripts_input_dir/pkts_output/*
sudo rm $scripts_input_dir/graphs_input/*

# Keep the file used in the comparion_plots.py script. When changing the experiment (comparson, alpha or k) delete the file
cp $output_folder/graphs_input/* $scripts_input_dir/graphs_input
