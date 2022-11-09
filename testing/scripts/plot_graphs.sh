# Quick script to plot graphs

scripts_input_dir=~/Documents/DINT/testing/results

cd ../testing/plotting_scripts

python3 link_utilization_plots.py -i $scripts_input_dir/pkts_output/  -g \
$scripts_input_dir/graphs_output/ -r $scripts_input_dir/graphs_input/ -d 60 -m 1 -s 1 -u "m" -t "Payless"

python3 comparison_plots.py -i $scripts_input_dir/graphs_input/ -g $scripts_input_dir/graphs_output/ -e "comparison"
