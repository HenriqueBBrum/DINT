# DINT: A Dynamic Algorithm for In-band Network Telemetry

DINT is a dynamic in-band network telemetry algorithm that keeps an accurate view of the network information while causing minimal network overhead in programmable networks. 

This repository contains the necessary tools and 
 to run DINT and the other solutions compared in the article. The results obtained and used in the article are also stored here. 


## Installation Guide

To run DINT, follow the instructions in the section *Obtaining required software* in the [P4 tutorials Repository](https://github.com/p4lang/tutorials).

After completing those steps, open the VM, **go to the \~/Documents folder** and clone this repo with the following command: 

```
git clone -b main --single-branch https://github.com/HenriqueBBrum/DINT.git 

```

If you would also like to clone the results used in the DINT article run this:

```
git clone https://github.com/HenriqueBBrum/DINT.git 

```

That's it, now you can start testing DINT!


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
* test_script: It can be one of these three values, scripts/run_comparison_evaluation.sh, scripts/run_alpha_evaluation.sh, or run_k_evaluation.sh. Correspondingly, the P4 files in the src folder should be related to those evaluation scripts. The default P4 files are for the "comparison" evaluation. If you want to run another evaluation script, move the current P4 file to their *DINT* folder and the correct P4 files outside their *DINT* folder.

* results_output_folder: Folder where the resulting files and graphs will be stored.

* min_time: Variable used in the DINT, LINT, and static algorithms. This is only used for graphing and not inside the P4 programs.

* loops: The amount of times the experiment is repeated.

The *run_testing.sh* script builds each type of switch  (DINT, LINT, etc.) and runs the corresponding JSON test configuration file.

After each algorithm has finished, the results are used with two python scripts to compare them. The scripts are inside the *evaluation_scripts* folder:

* *link_utilization_plots.py*: This script plots a comparison between the real link utilization (seen by the destination host) and the telemetry link utilization (seen by the monitoring host). It also calculates the RMSE and telemetry overhead and saves it to another file.
* *comparison_plots.py* This file creates multiple bar graphs of RMSE and telemetry overhea.


To test each switch type individually, go to the *src* folder and first clean the environment.

```
make clean
```
Then run *make* with one of the available P4 programs (main_static.p4, main_DINT.p4, etc.) and a testing file. Except for the *sINT* testing files, the content is the same and only differs in the output files' names. The [Customization](#Customization) section explains how to customize different parts of this project, including P4 files.

```
make P4_SRC=main_DINT.p4 TEST_JSON=../testing/config_files/DINT_tcpreplay.json
```

All data is saved in the results folder, where the evaluation scripts use it to plot multiple graphs.

### Reproduce paper evaluation

To reproduce the results obtained in the paper [DINT: A Dynamic Algorithm for In-band Network Telemetry]() three tests need to be executed:

1. Evaluation of the alpha parameter
2. Evaluation of the _k_ parameter
3. Comparison between DINT alternatives


You first need to move the P4 files of the desired test from their folder (in _src/DINT*_) to the parent folder (_src/_). After that, execute the *run_testing.sh* script informing the specific evaluation file in the *testing/scripts* folder as well as the rest of the parameters already mentioned. In the article we used 0.25, 0.5 and 1 for the <min_time> arguments and used 5 for the <loops> parameter. Besides changing the <min_time> in your execution command you also need to change the _obs_window_ variable in the DINT and LINT files and the _tel_insertion_min_window_ in the DINT files to be your <min_time>. Note that the time in p4 is in microseconds.

Obs: One of our future plans is to have only one DINT\*.p4 file for the evaluation and just change the desired parameters. 

### Customization

It is possible to customize the P4 code, the network topology, and the testing configuration used.

#### P4 Program

To customize the P4 code, go to the desired file and change to your requirements. To create a new P4 file, add a new file and write your P4 code. When creating a new P4 file, it's essential to consider the *table_entries* specified in your topology (see the next section for more information). Run your new P4 file with the following command:

```
make P4_SRC=<your_p4_file_name>.p4 TEST_JSON=../testing/config_files/<your_testing_file>.json
```

For more information about P4, go to these links:
- [P4 Tutorials](https://github.com/p4lang/tutorials)
- [P4_16 specification](https://p4.org/p4-spec/docs/P4-16-v1.0.0-spec.html)

#### Network Topology

Besides modifying how the switches process packets, it's also possible to change the network topology. There are three topology examples in the *src/topologies/* folder. To change between those topologies,  go to the *src/Makefile* and modify the value of the *TOPO* variable to be the path of the desired topology. 

To create a new topology, check the ones in the *src/topologies* folder, but the idea is to follow these steps:
- Create a *topology.json* file with the following fields:
	- A *hosts* section with information such as IP, MAC, and commands to be executed.
	- A *switches* section with the *runtime_json* object literal containing the path to the control plane information about each switch and an optional parameter called *cli_input* with CLI commands.
	- A *links* section informing the links in the topology.
- A *JSON* file with the control plane information about table entries for each switch. The tables in this file should match the tables described in the P4 program.
- An optional *txt* file with CLI commands for a switch. This is used in this project to add a mirroring port to allow cloning a packet.


#### Testing configuration

Finally, it's possible to specify the desired testing configuration. First, go to the *testing/config_files* and check the structure of the configuration files. In the configuration files, it's possible to define the testing time and what happens in each device specified in the topology file. Essentially, each device needs to either send or receive traffic. Since the configuration files receive shell commands, you can easily customize them to send any traffic you want (Scapy, IPerf, DITG, etc.) and to receive and process the incoming packets as desired. Keep in mind that the commands are executed sequentially, starting with the first defined device in your configuration file. Besides that, commands block other commands, so always put an "&" after a command if it is a non-blocking command.



## Branches

There are two branches in this repository:

* _main_: This branch contains all the source code used in the article.
* _results_: In this branch all the results obtained are stored.
