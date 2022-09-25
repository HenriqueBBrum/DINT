scripts_input_dir=~/Documents/Masters/testing/results

cd ../testing/plotting_scripts

# python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/ -j $scripts_input_dir/jitter_input/ -g \
# $scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m 0.25 -s 2 -u "m" -t "Payless" --plot_jitter

python3 comparison_plots.py -i $scripts_input_dir/graphs_input/ -g $scripts_input_dir/graphs_output/ 
