import argparse
from numpy import random


# M/bits per seconds the throughput

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





def parse_args():
	parser = argparse.ArgumentParser(description=f"Send packets to a certain ip and port")
	parser.add_argument("-c", "--configuration_file", help="Input file containing information about the desired configuration", required=True, type=str)
	parser.add_argument("-o", "--output_folder", help="Output folder for the traffic files", required=True, type=str)


	return vars(parser.parse_args())




if __name__ == '__main__':
    args = parse_args()
    main(args)
