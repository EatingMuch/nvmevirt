import subprocess
import re
import time
import sys
import os
import argparse
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import util

# Read fio_template from file
with open('fio_template.fio', 'r') as file:
    fio_template = file.read()

# Configuration for each test case
configs = [
    {'job0_rw': 'write', 'job0_bs': '128k', 'job0_iodepth': 4,
     'job1_rw': 'write', 'job1_bs': '128k', 'job1_iodepth': 4},
    {'job0_rw': 'write', 'job0_bs': '128k', 'job0_iodepth': 4,
     'job1_rw': 'randwrite', 'job1_bs': '4k', 'job1_iodepth': 16},
    {'job0_rw': 'randwrite', 'job0_bs': '4k', 'job0_iodepth': 16,
     'job1_rw': 'randwrite', 'job1_bs': '4k', 'job1_iodepth': 16}
]

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
def combine_bandwidths(job0_data, job1_data):
    combined_bandwidths = defaultdict(int)

    for t, b in zip(job0_data[0], job0_data[1]):
        combined_bandwidths[round(t, 2)] += b

    for t, b in zip(job1_data[0], job1_data[1]):
        combined_bandwidths[round(t, 2)] += b

    return combined_bandwidths

# Function to run fio and capture output
def run_fio(config, output_file):
    fio_script = fio_template.format(**config)
    with open('current_fio_script.fio', 'w') as f:
        f.write(fio_script)

    # Run make.sh and insmod.sh before starting the test
    util.run_command("../make.sh", "make.sh")
    util.run_command("../insmod.sh", "insmod.sh")
    util.run_command("rm -rf test*waf", "remove test waf output")

    # Start fio
    fio_process = subprocess.Popen(['fio', 'current_fio_script.fio'])
    for every_second in range(0, 60): # during 60s
        nand_write_count = util.read_proc_file(
            "/proc/nvmev/ftls/nand_write_count")
        write_count = util.read_proc_file(
            "/proc/nvmev/ftls/write_count")
        with open(output_file + ".waf", 'a') as rf:
            rf.write(f"{every_second} {nand_write_count} {write_count}\n")
        time.sleep(1)
    fio_process.wait()
    util.run_command("fio current_fio_script.fio", "fio")

    # Parse bandwidth logs
    job0_data = parse_bw_log('write_bw.1.log')
    job1_data = parse_bw_log('write_bw.2.log')

    # Combine bandwidths
    combined_bandwidths = combine_bandwidths(job0_data, job1_data)

    # Write combined bandwidths to output file
    with open(output_file, 'w') as f:
        for t in sorted(combined_bandwidths.keys()):
            f.write(f"{t:.3f} {combined_bandwidths[t]}\n")

    # Run rmmod.sh after finishing the test
    util.run_command("../rmmod.sh", "rmmod.sh")

def main():
    parser = argparse.ArgumentParser(
        description="Run fio benchmarks and process output.")
    parser.add_argument("--result", default="result",
                        help="Directory to save result files.")
    args = parser.parse_args()

    if os.path.exists(args.result):
        print(f"Warning: The directory '{args.result}' already exists.")
        sys.exit(1)

    os.makedirs(args.result, exist_ok=True)

    # Run all test cases
    for i, config in enumerate(configs):
        output_file = os.path.join(args.result,
            f"{config['job0_rw']}_{config['job0_bs']}_{config['job0_iodepth']}_"
            f"{config['job1_rw']}_{config['job1_bs']}_{config['job1_iodepth']}.log")
        print(f"Starting test case {i+1}")
        run_fio(config, output_file)
        print(f"Completed test case {i+1}")

if __name__ == "__main__":
    main()
