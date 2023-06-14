#!/bin/bash

# This script converts a pcapng file to a csv and only saves relevant information. The traffic is only UDP

traffic_data_folder=$1
cd $traffic_data_folder

switch_type=$2

input_file="$switch_type""_real_output.pcapng"
output_csv="$switch_type""_real_flows.csv"


headers="src_ip,src_port,dest_ip,dest_port,dest_src_pkts,dest_src_bytes,src_dest_pkts,src_dest_bytes,total_pkts,total_bytes,relative_time,total_time"

tshark -q -r "$input_file" -z conv,udp > temp.txt
sed -i -e 1,5d temp.txt
sed -i 's/[-=><|]//g' temp.txt

cat temp.txt | tr -s ' ' | sed 's/[: ]/,/g' > "$output_csv"


sed -i "1s/^/$headers\n/" "$output_csv"


rm temp.txt