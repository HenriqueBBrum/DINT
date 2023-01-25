import os

FLOW_TIMEOUT = 10 # In seconds

ELEPHANT_FLOW_BANDWIDTH_THRESHOLD = 100000 # In bits/second
ELEPHANT_FLOW_TIME_THRESHOLD = 7 #In seconds

MICROBURST_FLOW_BANDWIDTH_THRESHOLD = 100000 # In bits/second
MICROBURST_FLOW_TIME_THRESHOLD = 0.1 #In seconds

MICROSEG = 1000000


PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PKTS_DATA_FOLDER=PARENT_FODLER+"/results/pkts_output/"
RMSE_OVERHEAD_FOLDER=PARENT_FODLER+"/results/rmse_overhead_input/"
GRAPHS_OUTPUT_FOLDER=PARENT_FODLER+"/results/graphs_output/"



METRIC_UNIT = {'b': 1, 'k':1000, 'm':1000000, 'g':1000000000}
