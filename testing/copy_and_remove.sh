#!/bin/bash


output_folder=~/Documents/Masters/past_results/round1/results_0.25_3
scripts_input_dir=~/Documents/Masters/testing/results



mkdir $output_folder

sudo rm $scripts_input_dir/jitter_input/*.csv
sudo rm $scripts_input_dir/pkts_output/*.csv


cp -r $scripts_input_dir/* $output_folder


sudo rm $scripts_input_dir/graphs_output/*
sudo rm $scripts_input_dir/pkts_output/*
sudo rm $scripts_input_dir/rmse_graphs_input/*
sudo rm $scripts_input_dir/jitter_input/*


cp $output_folder/rmse_graphs_input/* $scripts_input_dir/rmse_graphs_input