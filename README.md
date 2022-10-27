
# DINT: A Dynamic Algorithm for In-band Network Telemetry

DINT is a dynamic in-band network telemetry algorithm that keeps an accurate view of the network information while causing minimal network overhead in programmable networks. 

This repository contains the necessary tools and information to run DINT and the other solutions compared in the article. The results obtained and used in the article are also stored here. 


## Installation Guide

To run DINT, follow the instructions in the section *Obtaining required software* in the [P4 tutorials Repository](https://github.com/p4lang/tutorials).

After completing those steps, open the VM, clone this repo, and you're ready to test DINT.

## Python prerequisites 

Even though you can execute P4 programs just with the installation step before, to execute the python scripts used in this work, you need to install the following python packages:

```
pip install matplotlib numpy pandas scapy
```



## Usage Guide


DINT and the other algorithms can be automatically tested by running the script *run_testing.sh* in the *testing* folder. Remember to give execution permission with *chmod*.
```
./run_evaluation.sh <test_script> <results_output_folder> <min_time> <loops>

```
* test_script: It can be one of these three value, scripts/run_comparison_evaluation.sh, scripts/run_alfa_evaluation.sh or run_k_evaluation.sh. Correspondingly, the P4 files in the src folder should be related to those evaluation scripts. The default P4 files are for the "comparison" evaluation. If you desire to run another evaluation script, move the current P4 file to their *DINT* folder and move the right P4 files outside their *DINT* folder.

* results_output_folder: Folder where the resulting files and graphs will be stored.

* min_time: Variable used in the DINT, LINT, and static algorithms. This is only used for graphing and not inside the P4 programs.

* loops: The amount of times the experiment is repeated.

The *run_testing.sh* script builds each type of switch  (DINT, LINT, etc.) and runs the corresponding JSON test configuration file.

After each algorithm has finished, the results are used with two python scripts to compare them. The scripts are inside the *evaluation_scripts* folder:

* *link_utilization_plots.py*: This script plots a comparison between the real link utilization (as seen by the destination host) and the telemetry link utilization (seen by the monitoring host). It also calculates the RMSE, telemetry overhead, and jitter and saves it to another file.
* *comparison_plots.py* This file creates multiple bar graphs of RMSE, telemetry overhead, and jitter metrics.


To test each switch type individually, go to the *src* folder and first clean the environment.

```
make clean
```
Then run *make* with one of the available P4 programs (main_static.p4, main_DINT.p4, etc.) and a testing file. Except for the *sINT* testing files, the content is the same and only differs in the output files' names. The [Customization](#Customization) section explains how to create your own test file.

```
make P4_SRC=main_DINT.p4 TEST_JSON=../testing/config_files/DINT_tcpreplay.json
```

All data is saved in the results folder, where the evaluation scripts use it to plot multiple graphs.

### Reproduce paper evaluation

To reproduce the results obtained in the paper [DINT: A Dynamic Algorithm for In-band Network Telemetry]() three tests need to be executed:

1. Evaluation of the alpha parameter
2. Evaluation of the _k_ parameter
3. Comparison between DINT alternatives

You first need to move the P4 files inside their folder in *src/\*DINT\**for each of these tests. Then execute *run_testing.sh* script indicating the specific evaluation script in the *testing/scripts*. 

Obs: One of our future plans is to have only one DINT\*.p4 file for the evaluation and just change the desired parameters. The current approach needs to be optimized...  


### Customization

Information on how to customize the P4 program, test topology, and evaluation traffic.