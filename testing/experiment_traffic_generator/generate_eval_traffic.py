### Script that creates the experiments workload ###

# Input: a configuration file describing how the traffic should be created and where the resulting files should be stored


## The input configuration file should have the following format:
# - First line: 	The evaluation type, meaning elephant_mice or microbursts
# - Second line: 	The destination IP
# - Third line: 	The number of hosts sending the desired workload
# - Fourth line: 	The experiment's total time
# - Final N lines: 	The subsequent N lines describe the workload from each one of the hosts with the following format:
#									<amt_flows> <totalbytes_gen_func> <gen_func_parameters> <duration_gen_func> <gen_func_parameters>, ....
#					Each line (host) can have multiple flow-generating  strategies, each separated by a comma (,)
# 	
## The resulting files are in .txt format, where each line has the following format:
# 			<destination_IP> <bandwidth> <duration> <starting_time>
#  The node_communication/send.py script uses the .txt files to send the desired traffic

import argparse
from numpy import random


def parse_args():
	parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
	parser.add_argument("-c", "--configuration_file", help="Input file containing information about the desired configuration", required=True, type=str)
	parser.add_argument("-o", "--output_folder", help="Output folder for the traffic files", required=True, type=str)

	return vars(parser.parse_args())

def main(args):
	unique_flows = []
	with open(args['configuration_file'], 'r') as config:
		evaluation_type = config.readline().strip('\n')
		dest_ip = config.readline().strip('\n')
		amt_hosts = int(config.readline())
		total_time = int(config.readline())

		count = 0
		for line in config:
			if count>=amt_hosts:
				break


			output_file = f"{args['output_folder']}/h{count+1}_{evaluation_type}_traffic.txt"
			output_file = open(output_file, 'w')

			for column in line.split(','):

				items = column.split(' ')
				print(items)
				amt_flows = int(items[0])

				# The bandwidth is in Mbits per second
				if(items[1] == 'SD'):
					bandwidth = random.normal(float(items[2]), float(items[3]), amt_flows)
				elif(items[1] == 'R'):
					bandwidth = random.uniform(float(items[2]), float(items[3]), amt_flows)

				if(items[4] == 'SD'):
					duration = random.normal(float(items[5]), float(items[6]), amt_flows)
				elif(items[1] == 'R'):
					duration = random.uniform(float(items[5]), float(items[6]), amt_flows)

				highest_wait_time = total_time - (float(items[5]) + float(items[6]))
				if(highest_wait_time>1):
					wait_time = random.randint(low=1, high=highest_wait_time, size=amt_flows)
				else:
					wait_time = [0]*amt_flows

				flows = []
				for i in range(amt_flows):
					flows.append(f"{dest_ip} {bandwidth[i]:.4f}M {duration[i]:.4f} {wait_time[i]}\n")

				for flow in flows:
					output_file.write(flow)

			output_file.close()				

			count+=1


if __name__ == '__main__':
    args = parse_args()
    main(args)
