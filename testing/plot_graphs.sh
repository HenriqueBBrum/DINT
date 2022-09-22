test_files_folder=~/Documents/Masters/testing/test_config_files
scripts_input_dir=~/Documents/Masters/testing/results

cd ../testing/python_scripts

python3 link_util_plot.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m 2 -s 2 -u "m" -t "Payless"

python3 rmse_and_overhead_plot.py -i $scripts_input_dir/graphs_input/ -g $scripts_input_dir/graphs_output/ 

