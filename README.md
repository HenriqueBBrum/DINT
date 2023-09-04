# Providing Fine-grained Network Metrics for Monitoring Applications using In-band Telemetry

This repository contains the code and instructions needed to reproduce the experiments for the paper [Providing Fine-grained Network Metrics for
Monitoring Applications using In-band Telemetry](https://ieeexplore.ieee.org/document/10175472/).

> To check our paper's final results go to our Google Drive folder with the [NetSoft 2023 results](https://drive.google.com/drive/folders/14hhirZpIgI2-LsnEub-rUIznKYLPIxZN?usp=drive_link)

## Installation Guide

Before reading this tutorial, follow the instructions in the section "**Obtaining required software**" in the [P4 tutorials Repository](https://github.com/p4lang/tutorials). After completing those steps, open the VM, **go to the \~/Documents folder** and clone this repository with the following command:

```
git clone -b micro --single-branch https://github.com/HenriqueBBrum/DINT.git
```
>  :warning: Clone this repo directly into the **\~/Documents folder** since this code uses hardcoded paths.

Then, install *tcpreplay*:

```
sudo apt-get install tcpreplay
```

### Python prerequisites

Even though you can execute P4 programs and get the resulting files just with the installation steps before, to execute the graph plotting Python scripts used in this work, you need to install the following Python packages:

```
pip install matplotlib numpy pandas scapy
```

### Improve the BMv2 software switch performance

The default BMv2 switch (`simple_switch_grpc` for this project) that comes with the P4 VM has low performance because it uses a log system. To fully replicate our results, you need to use the performance-improved BMv2 that can be obtained by following the steps below.

First, clone the behavioral model repository from the official GitHub:

```
cd Documents
git clone https://github.com/p4lang/behavioral-model.git
```

Enter the behavioral model repository:
```
cd behavioral-model
```

Install the dependencies and required libraries:
```
./install_deps.sh
sudo apt-get  install libreadline-dev
```

> :warning: Increase the virtual machine's processing capacity (memory and CPU) otherwise it might crash for the next step

Now, configure the software switch without the log system to improve the performance (**this step takes some time**, so be patient):
```
./autogen.sh
./configure 'CXXFLAGS=-g -O3' 'CFLAGS=-g -O3' --with-thrift --with-pi --disable-logging-macros --disable-elogger
```

Finally, install the software switch. 
```
make
sudo make install
sudo ldconfig
```
:warning: This will create two software switch executables: the `simple_switch` and the `psa_switch`, but not the `simple_switch_grpc` that is needed for this project. To install the `simple_switch_grpc` target, go to the `simple_switch_grpc` folder

```
cd targets/simple_switch_grpc
```

Next, run the following commands:

```
./configure --with-thrift 'CXXFLAGS=-O0 -g'
make
sudo make install
sudo ldconfig
```

To change from the improved software switch used in this project to the unoptimized version, go to the *src* folder and open the Makefile with a text editor. Change the **BMV2_SWITCH_EXE** value from `/home/p4/Documents/behavioral-model/targets/simple_switch_grpc/simple_switch_grpc` to `simple_switch_grpc`. However, be aware that with this switch version you won't be able to reproduce our experiments.

That's it; now you can start reproducing the experiments!


## Reproduce paper evaluation

To reproduce the experiments performed in our paper [Providing Fine-grained Network Metrics for
Monitoring Applications using In-band Telemetry](https://ieeexplore.ieee.org/document/10175472/), start by downloading our [Google Drive folder](https://drive.google.com/drive/folders/1HRkH4al5L0zLIjNbyue1A147HcwH5JTM?usp=sharing) containing the experiments traffic. Extract the files from the ZIP folder and move the *.pcapng* files with the **elephant_mice** string to the `DINT/testing/experiment_traffic_generator/elephant_mice` and the ones with the **microbursts** string to the `DINT/testing/experiment_traffic_generator/microbursts`

```
unzip -d ~/Downloads/ ~/Downloads/DINT_NetSoft_Workload-*.zip
```

```
mv ~/Downloads/DINT_NetSoft_Workload/*elephant_mice* ~/Documents/DINT/testing/experiment_traffic_generator/elephant_mice
mv ~/Downloads/DINT_NetSoft_Workload/*microbursts* ~/Documents/DINT/testing/experiment_traffic_generator/microbursts
```

> :warning: Despite running the same experiments with the same workload, the final results may vary since the algorithms may behave differently.


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

Let it run; receiving all results will take approximately 26 minutes since each INT algorithm (DINT, LINT, and the static) runs five times. After the experiment, check your final results folder for the `graphs` folder containing the plotted graphs and the `anomalous_flows_data` folder for the classification performance results.


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

Three minimum telemetry insertion values were used for the elephant flows case study: **0.5s, 1s. and 2s**. For each one of them, you need to run the following command:

```
./run_experiments.sh elephant_mice ~/Documents/DINT/results/ 100 <min_tel_insertion> 5
```

Let it run; it will take approximately 26 minutes for each \<min_tel_insertion\> value. After a run for one \<min_tel_insertion\> has ended, change the \<min_tel_insertion\> to the next one until all three have been evaluated. After running all three experiments, check the *last* experiment's folder in the final results folder you provided. Look for the `graphs` folder containing the plotted graphs and the `anomalous_flows_data` folder for the classification performance results.

## Create your workload

To create your workload, the first thing is to understand how our paper's workload was created.

### Generate the desired traffic

Initially, we defined our desired workload for the **elephant_mice** and **microbursts** experiments. Check the **flows.txt** files in the `testing/experiment_traffic_generator/elephant_mice` and `testing/experiment_traffic_generator/microbursts` folders. These files are used to define the experiments workload. They have the following format:

- **First line**: 		The type of the experiment, elephant_mice or microbursts;
- **Second line**: 		The destination IPv4 address;
- **Third line**: 		The number of hosts sending the desired workload;
- **Fourth line**: 		The experiment's total time;
- **Final N lines**: 	The subsequent N lines describe the workload from each one of the hosts with the following format:
                    `<amt_flows> <throughput_function> <throughput_func_parameters> <duration_function> <duration_func_parameters>, ...`--
  Each line (host) can have multiple flow-generating  strategies, each separated by a comma (,).


These text files served as input to the `testing/experiment_traffic_generator/generate_eval_traffic.py` script, and the information about each experiment flow was created (bandwidth and duration). The output of the **generate_eval_traffic.py** script is text files (one for each host informed) containing the information about each flow, where each line (flow) has the following format:
			`<destination_IP> <flow_bandwidth> <flow_duration> <flow_starting_time>`.

Check the **h\*traffic.txt** files in the `testing/experiment_traffic_generator/elephant_mice` and `testing/experiment_traffic_generator/microbursts` folders to understand the generated information about each flow. Finally, the **testing/node_communication/send.py** script was used to send the desired traffic.

You can start creating your workload now that you understand how our traffic was generated. First, remove the existing files in the `testing/experiment_traffic_generator/elephant_mice` and `testing/experiment_traffic_generator/microbursts` folders. Then, read the `testing/experiment_traffic_generator/generate_eval_traffic.py` documentation to understand how to define your workload; after that, create your **flows.txt** file for the *elephant_mice* or *microbursts* scenario; finally, run the **generate_eval_traffic.py** to create the workload for each one of your hosts.

For example, if you wanted an *elephant_mice* workload where there are three hosts (h1, h2, and h3 by default) sending packets to host 10.0.4.4 for 50 seconds, and each host sends ten flows with random bandwidth between 0.5 and 1 Mbps for 8 seconds you would have a **flows.txt** like this:

```
elephant_mice
10.0.4.4
3
50
10 R 0.5 1 SD 8 0
10 R 0.5 1 SD 8 0
10 R 0.5 1 SD 8 0
```

Then, to generate the actual traffic for the **node_communication/send.py** script, run the following command:
```
python3 generate_eval_traffic.py -c elephant_mice/flows.txt -o elephant_mice/
```

Check the `elephant_mice`folder for the resulting files.

The next sub-section will explain how to use the workload created to test the three INT algorithms used in our paper.


### Run the same workload for all experiments

With the previous steps, you generated your workload. However, to not depend on Python, Scapy, and the *send.py* function, we will use the *tcpreplay* tool to capture one execution of your workload in order to repeat it in all future experiments. To this end, we will run your workload **one-time** with the **basic.p4** switch and capture it with *tcpreplay*.

First, go to the **experiment_config/** folder and open the **get_tcpreplay_pcap.json** file with a text editor. Change the value of the **time** parameter to the one you provided when generating your workload plus five seconds to account for the setup time. Also, change each device's `duration:<time>` entry to reflect the new experiment's duration.

The default experiment for the **get_tcpreplay_pcap.json** is the **elephant_mice**. If your workload is for the **elephant_mice** experiment, you can proceed to build the P4 switch and capture the traffic. If your workload is for the **microbursts** application, change every **elephant_mice** string for  **microbursts**. 

After adjusting the **get_tcpreplay_pcap.json**, go to the *src* folder:

```
cd ~/Documents/DINT/src/
```

Open the Makefile with a text editor and edit the **TOPO** to be `topologies/tcpreplay_mesh/topology.json`. Close and save the file.

Now, it is time to build the **basic.p4** switch, use the **get_tcpreplay_pcap.json** file to configure our experiment and get the tcpreplay *.pcapng* files:

```
make clean && make P4_SRC=basic.p4 TEST_JSON=../testing/experiment_config/get_tcpreplay_pcap.json
```

After that, change back the **TOPO** in the *src/Makefile* to `topologies/mesh/topology.json`. The resulting PCAPNG files will be in either the **elephant_mice** or **microbursts** folder in the **experiment_traffic_generator/** directory. With all these steps done, you can try DINT and the other algorithms using your workload. Follow the steps in the [Reproduce paper evaluation](#Reproduce-paper-evaluation) section for this.
