import subprocess
import time
import sys
import os
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import util

# Read fio_template from file
with open('fio_template.fio', 'r') as file:
    fio_template = file.read()

# Configuration
total_size = 16054972416  # 16,054,972,416 bytes
num_streams = 4  # Number of multi-streams (N)
runtime = 60  # Runtime for each job

# Ensure output directory exists
output_dir = "fio_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Function to parse bandwidth log
def parse_bw_log(log_file):
    timestamps = []
    bandwidths = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            timestamp = float(parts[0]) / 1000.0
            bandwidth = int(parts[1])
            timestamps.append(timestamp)
            bandwidths.append(bandwidth)
    return timestamps, bandwidths

# Function to combine bandwidth logs
def combine_bandwidths(bandwidth_data):
    combined_bandwidths = defaultdict(int)

    for timestamp, bandwidth in bandwidth_data:
        combined_bandwidths[round(timestamp, 1)] += bandwidth

    return combined_bandwidths

def calculate_job_sizes(total_size, num_jobs):
    job_sizes = []
    remaining_size = total_size
    divider = 0
    for i in range(num_jobs):
        divider = divider + 2 ** i
    for i in range(num_jobs):
        job_size = (total_size * (2 ** i) / divider + 4095) // 4096 * 4096
        job_sizes.append(job_size)
        remaining_size -= job_size
    job_sizes[-1] = job_sizes[-1] + remaining_size
    print (divider, total_size, sum(job_sizes), job_sizes)
    return job_sizes

# Function to generate fio script and run it
def run_fio(num_jobs, output_file_prefix):
    job_configs = []
    job_sizes = calculate_job_sizes(total_size, num_jobs)

    offset = 0
    for i in range(num_jobs):
        directive_id = i % num_streams + 1
        job_config = f"""
[job{i}]
rw=write
bs=128k
numjobs=1
offset={offset}B
size={job_sizes[i]}B
iodepth=4
filename=trtype=PCIe traddr=0001\:10\:00.0 directive_id={directive_id} ns=1
write_bw_log={output_file_prefix}_bw.{i}.log
runtime={runtime}
"""
        job_configs.append(job_config)
        offset += job_sizes[i]
    fio_script = fio_template + "\n".join(job_configs)
    with open('current_fio_script.fio', 'w') as f:
        f.write(fio_script)

    # Log the current configuration
    print(f"Running FIO with {num_jobs} jobs, output prefix: {output_file_prefix}")

    # Run make.sh and insmod.sh before starting the test
    util.run_command("../make.sh", "make.sh")
    util.run_command("../insmod.sh", "insmod.sh")

    # Run fio
    run_command(f"fio current_fio_script.fio --output-format=json --output={output_file_prefix}.json", "fio")

    # Parse bandwidth logs
    bandwidth_data = []
    for i in range(num_jobs):
        log_file = f"{output_file_prefix}_bw.{i + 1}.log"
        timestamps, bandwidths = parse_bw_log(log_file)
        bandwidth_data.extend(zip(timestamps, bandwidths))

    # Run rmmod.sh after finishing the test
    util.run_command("../rmmod.sh", "rmmod.sh")

    return bandwidth_data

# Generate and run all test cases
result_table = []
result_file = 'fio_test_results.txt'
num_jobs_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Number of jobs to run in each test

for num_jobs in num_jobs_list:
    output_file_prefix = os.path.join(output_dir, f"fio_output_{num_jobs}_jobs")
    bandwidth_data = run_fio(num_jobs, output_file_prefix)
    combined_bandwidths = combine_bandwidths(bandwidth_data)

    with open(f"{output_file_prefix}_combined_bw.log", 'w') as bw_file:
        for timestamp in sorted(combined_bandwidths):
            bw_file.write(f"{timestamp} {combined_bandwidths[timestamp]}\n")

    result_table.append(f"{num_jobs} {output_file_prefix}.json")

# Write result table to text file
with open(result_file, 'w') as rf:
    for line in result_table:
        rf.write(line + "\n")

print("All tests completed successfully.")

