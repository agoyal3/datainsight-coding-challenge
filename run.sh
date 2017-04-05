#!/usr/bin/env bash

# I'll execute my programs, with the input directory log_input and output the files in the directory log_output
python ./src/process_log.py ./log_input/log.txt ./log_output/hosts.txt ./log_output/hours.txt ./log_output/resources.txt ./log_output/blocked.txt ./log_output/bad_records.txt

