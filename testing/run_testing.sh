#!/bin/bash

cd ../src
 
make clean
make P4_SRC=main_static.p4 TEST_JSON=../testing/test_config_files/static.json

make clean
make P4_SRC=main_dynamicV1.p4 TEST_JSON=../testing/test_config_files/dynamicV1.json

make clean
make P4_SRC=main_dynamicV2.p4 TEST_JSON=../testing/test_config_files/dynamicV2.json

make clean
make P4_SRC=main_sINT.p4 TEST_JSON=../testing/test_config_files/sINT.json


cd ../testing/python_scripts
python3 line_graph.py -i ../results/pkts_output/ -g ../results/graphs_output/ -r ../results/rmse_graphs_input/ -d 60 -m 1 -s 1

python3 rmse_graph_plotter.py -i ../results/rmse_graphs_input/ -g ../results/graphs_output/ 

