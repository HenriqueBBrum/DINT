import argparse
from numpy import random


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

			items = line.split(' ')
			amt_flows = int(items[0])
			if(items[1] == 'SD'):
				bandwidth = random.normal(float(items[2]), float(items[3]), amt_flows)

			if(items[4] == 'SD'):
				duration = random.normal(float(items[5]), float(items[6]), amt_flows)

			wait_time = random.randint(low=1, high=(total_time - (2*float(items[5]) + float(items[6]))), size=amt_flows)

			flows = []
			for i in range(amt_flows):
				flows.append(f"{dest_ip} {bandwidth[i]:.4f}M {duration[i]:.4f} {wait_time[i]}\n")

			output_file = f'h{count+1}_{evaluation_type}_traffic.txt'
			with open(output_file, 'w') as output:
				for flow in flows:
					output.write(flow)


			count+=1





def parse_args():
	parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
	parser.add_argument("-c", "--configuration_file", help="Input file containing information about the desired configuration", required=True, type=str)

	return vars(parser.parse_args())




if __name__ == '__main__':
    args = parse_args()
    main(args)
