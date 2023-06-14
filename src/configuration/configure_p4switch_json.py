# Script to modify s*-runtime.json files to change "p4info" and "bmv2_json" to have <p4_file> in the path


import argparse
import glob
import os
import json

def parse_args():
    parser = argparse.ArgumentParser(description=f"Configure control plane switch json")
    parser.add_argument("-p", "--p4_file", help="P4 file to be executed", required=True, type=str)
    parser.add_argument("-t", "--topology_file", help="Topology file", required=True, type=str)

    return vars(parser.parse_args())


def main(p4_file_name, topology_file):
    topology_file = "/".join(topology_file.split('/')[:-1])
    os.chdir(topology_file+'/')

    p4_file_name = p4_file_name.split('.')[0]

    # For each switch runtime json, update json with 'p4_file_name'
    for file in glob.glob('s*-runtime.json'):
        with open(file, 'r') as file_:
            json_object = json.load(file_)

        json_object['p4info'] = "build/"+p4_file_name+".p4.p4info.txt"
        json_object['bmv2_json'] = "build/"+p4_file_name+".json"

        with open(file, 'w') as file_:
            json.dump(json_object, file_, indent=3)


if __name__ == '__main__':
    args = parse_args()
    main(args['p4_file'], args['topology_file'])
