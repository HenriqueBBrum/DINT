# Providing Fine-grained Network Metrics for Monitoring Applications using In-band Telemetry

This repository contains the code and instructions needed to reproduce the experiments for the paper [Providing Fine-grained Network Metrics for
Monitoring Applications using In-band Telemetry](). 


## Installation Guide

Before reading this tutorial, follow the instructions in the section *Obtaining required software* in the [P4 tutorials Repository](https://github.com/p4lang/tutorials). After completing those steps, open the VM, **go to the \~/Documents folder** and clone this repo with the following command: 

```
git clone -b micro --single-branch https://github.com/HenriqueBBrum/DINT.git 
```

> To check our paper's final results go to our google drive folder with the [NetSoft 2023 results](https://drive.google.com/drive/folders/14hhirZpIgI2-LsnEub-rUIznKYLPIxZN?usp=drive_link)

Then, install *tcpreplay*:

```
sudo apt-get install tcpreplay
```

### Python prerequisites 

Even though you can execute P4 programs and get the resulting files just with the installation steps before, to execute the graph plotting Python scripts used in this work, you need to install the following Python packages:

```
pip install matplotlib numpy pandas scapy
```

That's it; now you can start testing DINT!


## Reproduce paper evaluation

To reproduce the exact experiments performed in our paper [Providing Fine-grained Network Metrics for
Monitoring Applications using In-band Telemetry](), start by downloading our [Google Drive folder](https://drive.google.com/drive/folders/1HRkH4al5L0zLIjNbyue1A147HcwH5JTM?usp=sharing) contaning the experiments traffic. Extract the files from the ZIP folder and move the *.pcapng* files with the **elephant_mice** string to the *DINT/testing/experiment_traffic_generator/elephant_mice* and the ones with the **microbursts** string to the *DINT/testing/experiment_traffic_generator/microbursts*

```
unzip ~/Downloads/DINT_NetSoft_Workload-*.zip
```

```
mv ~/Downloads/DINT_NetSoft_Workload/*elephant_mice* ~/Documents/DINT/testing/experiment_traffic_generator/elephant_mice
mv ~/Downloads/DINT_NetSoft_Workload/*microbursts* ~/Documents/DINT/testing/experiment_traffic_generator/microbursts
```

### Case Study 1: Monitoring Microbursts 

Follow the next steps to replicate the results for the microbursts case study. First, create the folder to store your results:

```
cd ~/Documents/DINT
mkdir results
```

Now, go to the testing folder:

```
cd testing
```

And run the following command:

```
./run_experiments.sh microbursts ~/Documents/DINT/results/ 100 0.1 5
```

Let it run; receiving all results will take approximately 26 minutes since each INT algorithm (DINT, LINT, and the static) runs five times. After the experiment, check your final results folder for the *graphs/* folder containing the plotted graphs and the *anomalous_flows_data/* folder for the classification performance results.


### Case Study 2: Monitoring Elephant Flows

Follow the next steps to replicate the elephant flows case study results. First, create the folder to store your results:

```
cd ~/Documents/DINT
mkdir results
```

Now, go to the testing folder:

```
cd testing
```

Three minimum telemetry insertion values will be used for the elephant flows case study: 0.5s, 1s. and 2s. For each one of them, you need to run the following command:

```
./run_experiments.sh elephant_mice ~/Documents/DINT/results/ 100 <min_tel_insertion> 5
```

Let it run; it will take approximately 26 minutes for each \<min_tel_insertion\> value. After a run for one \<min_tel_insertion\> ended, change the \<min_tel_insertion\> to the next one until all three have been evaluated. After running all three experiments, check the last experiment's folder in the final results folder you provided. Look for the *graphs/* folder containing the plotted graphs and the *anomalous_flows_data/* folder for the classification performance results.

## Create your workload

To create your workload, the first thing is to understand how our paper's workload was created. 

### Generate the desired traffic

Initially, we defined our desired workload for the **elephant_mice** and **microbursts** experiments. Check the *flows.txt* files in the *experiment_traffic_generator/elephant_mice* and *experiment_traffic_generator/microbursts* folders. These files are used to define how our workload is supposed to be generated. They have the following format:

- **First line**: 		The type of the experiment, elephant_mice or microbursts
- **Second line**: 		The destination IP
- **Third line**: 		The number of hosts sending the desired workload
- **Fourth line**: 		The experiment's total time
- **Final N lines**: 	The subsequent N lines describe the workload from each one of the hosts with the following format:
                    `<amt_flows> <totalbytes_gen_func> <gen_func_parameters> <duration_gen_func> <gen_func_parameters>, ...` Each line (host) can have multiple flow-generating  strategies, each separated by a comma (,).
 	

These text files were used as input to the *experiment_traffic_generator/generate_eval_traffic.py* script, and the information about each flow of an experiment was created (bandwidth and duration). The resulting text files (one for each host informed) from the *generate_eval_traffic.py* script have the information about each flow, where each line has the following format:
			`<destination_IP> <flow_bandwidth> <flow_duration> <flow_starting_time>`

Check the *\*traffic.txt* files in the *experiment_traffic_generator/elephant_mice* and *experiment_traffic_generator/microbursts* folders. Finally, the *node_communication/send.py* script uses these files to send the desired traffic.

Now that you understand how to generate your traffic, remove the existing files in the *experiment_traffic_generator/elephant_mice* and *experiment_traffic_generator/microbursts* folders and create your workload. Start by defining your *flows.txt* file, then read the *experiment_traffic_generator/generate_eval_traffic.py* code documentation, and, finally, run the *generate_eval_traffic.py* to create the workload for each one of your hosts.

With these steps, you generated your workload. However, to not depend on Python and Scapy, we will use the tcpreplay to capture the base traffic that all our experiments will use.


### Run the same workload for all experiments

To run the same workload for all experiments, we will run one time with the *basic.p4* file and capture it with tcpreplay. 

First, go to the *experiment_config/* folder and open the *get_tcpreplay_pcap.json* file with a text editor. Change the value for the **time** parameter to the one you provided when generating your workload. 

The default experiment for the *get_tcpreplay_pcap.json* is the **elephant_mice**. If your workload is for the **elephant_mice** experiment, you can proceed to build the P4 switch and capture the traffic. If your workload is for the **microbursts** application, change every **elephant_mice** string for  **microbursts**.

Now, it is time to build the *basic.p4* switch, use the *get_tcpreplay_pcap.json* file to configure our experiment and get the tcpreplay *.pcapng* files:

```
cd src/
make clean
```
```
make P4_SRC=basic.p4 TEST_JSON=../testing/experiment_config/get_tcpreplay_pcap.json 
```

After that, you can try DINT and the other algorithms using your workload. Follow the steps in the [Reproduce paper evaluation](#Reproduce-paper-evaluation) section for this.