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


# make clean
# make P4_SRC=main_LINT.p4 TEST_JSON=$test_files_folder/LINT.json

cd ../testing/python_scripts

python3 link_util_plot.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m 2 -s 2 -u "m" -t "Payless"

python3 rmse_and_overhead_plot.py -i $scripts_input_dir/graphs_input/ -g $scripts_input_dir/graphs_output/ 

