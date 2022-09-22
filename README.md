
# DINT: A dynamic and efficient algorithm for in-band network telemetry

DINT is a dynamic and efficient in-band network telemetry algorithm, capable of keeping an accurate view of the network information while causing minimal network overhead in prgroammable netwroks. 

This repository contains the necessary tools and information to run DINT as well as the other solutions compared to. The  results obtained and used in the article are also stored here. 


## Installation Guide

To run DINT follow the instructions in the section *Obtaining required software* in the [P4 tutorials Repository](https://github.com/p4lang/tutorials).

After completing those steps, open the VM, clone this repo and you're ready to test DINT.


## Usage Guide


DINT and the other algorithms can be automatically tested by running the script *run_testing.sh* in the *testing* folder. Remenber to give execute permission with *chmod*.
```
./run_testing.sh

```

The *run_testing.sh* script builds each type of switch  (DINT, LINT, etc) and runs the corresponding json test configuration file.

After all algorithms have finished, the results are used to with two python scripts to compare them. The scripts are inside the *evaluation_scripts* folder:

* *link_utilization_plots.py*: This script plots a comparision between the real link utilization (as seen by the destination host) with the telemetry link utilization (as seen by the monitoring host). It also calculates the rmse, telemetry overhead and jitter and saves to another file.
* *comparison_plots.py* This file creates multiple bar graphs of rmse, telemetry overhead and jitter metrics.


To test each switch type individually, go to the *src* folder and first clean previous testing files.

```
make clean
```
Then run *make* with one of the avaible switch p4 code (main_static.p4, main_DINT.p4, etc) and a testing file. With the excepton of the *sINT* testing files the others just differ in the name of the output files. In the [Customization](#Customization) section it's explained on how to create your own test file.

```
make P4_SRC=main_DINT.p4 TEST_JSON=../testing/config_files/DINT_tcpreplay.json
```

All data is saved in the results folder where it is used by the evaluation scripts to plot multiple graphs.

### Reproduce paper executions


### Execution pipeline


### Customization
