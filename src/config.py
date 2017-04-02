import os

log_file = os.path.abspath('../log_input/log.txt')
number_of_active_hosts = 10
number_of_top_resources = 10
number_of_busiest_periods = 10
busy_period_window_in_min = 60
hosts_file = os.path.abspath('../log_output/hosts.txt')
resources_file = os.path.abspath('../log_output/resources.txt')
hours_file = os.path.abspath('../log_output/hours.txt')
blocked_file = os.path.abspath('../log_output/blocked.txt')
