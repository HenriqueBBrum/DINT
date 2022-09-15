#!/bin/bash

test_files_folder=~/Documents/Masters/testing/test_config_files
scripts_input_dir=~/Documents/Masters/testing/results

cd ../src 

make clean
make P4_SRC=main_static.p4 TEST_JSON=$test_files_folder/static_tcpreplay.json

make clean
make P4_SRC=main_dynamic.p4 TEST_JSON=$test_files_folder/dynamic_tcpreplay.json

make clean
make P4_SRC=main_sINT.p4 TEST_JSON=$test_files_folder/sINT_tcpreplay.json

cd ../testing/python_scripts

python3 line_graph.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/rmse_graphs_input/ -d 60 -m 0.25 -s 2 -u "m" -t "Payless"

python3 rmse_graph_plotter.py -i $scripts_input_dir/rmse_graphs_input/ -g $scripts_input_dir/graphs_output/ 

