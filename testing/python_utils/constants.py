import os


### Generic constants

TELEMETRY_HEADER_SZ = 8
TELEMETRY_METADATA_SZ = 17

MICROSEG = 1000000

METRIC_UNIT = {'b': 1, 'k':1000, 'm':1000000, 'g':1000000000}




### Thresholds used by the python_utils/flows.py and the plotting_scripts/save_anomalous_flows_stats.py scripts


FLOW_TIMEOUT = 10 # In seconds

ELEPHANT_FLOW_THROUGHPUT_THRESHOLD = 8000000 # In bits/second
ELEPHANT_FLOW_TIME_THRESHOLD = 10 #In seconds

MICROBURST_FLOW_THROUGHPUT_THRESHOLD = 20000000 # In bits/second
MICROBURST_FLOW_TIME_THRESHOLD = 0.1 #In seconds


### Common folders to multiple files where temporary and final data is stored

PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRAFFIC_DATA_FOLDER=PARENT_FODLER+"/results/traffic_data/"
GRAPHS_FOLDER=PARENT_FODLER+"/results/graphs/"
NRMSE_OVERHEAD_DATA_FOLDER=PARENT_FODLER+"/results/nrmse_overhead_data/"
ANOMALOUS_FLOWS_DATA_FOLDER=PARENT_FODLER+"/results/anomalous_flows_data/"


