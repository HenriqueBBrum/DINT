#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/p4/Documents/Masters/src/python_scripts/communication')


from copy import *
from telemetry_headers import *

def myfunc(pkt):
	return pkt.time

packets = rdpcap("/home/p4/Documents/Masters/src/sINT_real_output_h1.pcapng")


count = 0

new_pkts = []

for pkt in packets:
	if Telemetry in pkt:
		base_copy = copy.copy(packets[0])
		base_copy.time = pkt.time
		new_pkts.append(base_copy)



no_tel_pkts_list = [x for x in packets if not Telemetry in x]
no_tel_pkts_list.extend(new_pkts)
no_tel_pkts_list.sort(key=myfunc)


wrpcap("/home/p4/Documents/Masters/src/sINT_real_output_h1_mod.pcapng", no_tel_pkts_list)