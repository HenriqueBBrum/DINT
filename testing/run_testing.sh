#!/bin/bash

cd ../src
 
make clean
make P4_SRC=main_static.p4 TEST_JSON=../testing/test_config_files/static.json

make clean
make P4_SRC=main_dynamic.p4 TEST_JSON=../testing/test_config_files/dynamic.json


cd ../testing/python_scripts
python3 line_graph.py -i ../results/pkts_output/ -o ../results/graphs_output/ -d 60 -m 1 -s 1

# python3 