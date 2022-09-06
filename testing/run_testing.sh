#!/bin/bash

cd ../src
 
make clean
make P4_SRC=main_static.p4 TEST_JSON=../testing/test_config_files/static_tcpreplay.json

make clean
make P4_SRC=main_dynamic.p4 TEST_JSON=../testing/test_config_files/dynamic_tcpreplay.json

make clean
make P4_SRC=main_sINT.p4 TEST_JSON=../testing/test_config_files/sINT_tcpreplay.json


cd ../testing/python_scripts
python3 line_graph.py -i ../results/pkts_output/ -g ../results/graphs_output/ -r ../results/rmse_graphs_input/ -d 60 -m 1 -s 2 -u "m" -t "Payless"

python3 rmse_graph_plotter.py -i ../results/rmse_graphs_input/ -g ../results/graphs_output/ 

