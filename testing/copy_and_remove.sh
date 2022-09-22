#!/bin/bash


output_folder=~/Documents/Masters/past_results/latest/results_2_5
scripts_input_dir=~/Documents/Masters/testing/results



mkdir $output_folder

sudo rm $scripts_input_dir/jitter_input/*.csv
sudo rm $scripts_input_dir/pkts_output/*.csv


cp -r $scripts_input_dir/* $output_folder


sudo rm $scripts_input_dir/graphs_output/*
sudo rm $scripts_input_dir/pkts_output/*
sudo rm $scripts_input_dir/graphs_input/*
sudo rm $scripts_input_dir/jitter_input/*


cp $output_folder/graphs_input/* $scripts_input_dir/graphs_input