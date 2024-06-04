import subprocess
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import util

# Configuration for each test case
job0_write_percentages = [i for i in range(10, 100, 10)]
job1_write_percentages = [i for i in range(90, 0, -10)]
write_ranges = [20, 40, 60, 80]  # percent of total size
total_bw = 300 * 1024 * 1024  # 600MB/s in bytes

# Ensure output directory exists
output_dir = "fio_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Function to run fio and capture output
def run_fio(config, output_file, result_file):
    fio_script = fio_template.format(**config)
    with open('current_fio_script.fio', 'w') as f:
        f.write(fio_script)

    # Log the current configuration
    print(f"Running FIO with config: job0_offset={config['job0_offset']}, job0_size={config['job0_size']}, job1_offset={config['job1_offset']}, job1_size={config['job1_size']}, job0_rate={config['job0_rate']}, job1_rate={config['job1_rate']}")

    # Run make.sh and insmod.sh before starting the test
    util.run_command("../make.sh", "make.sh")
    util.run_command("../insmod.sh", "insmod.sh")

    # Start fio and sleep for rampup period
    fio_process = subprocess.Popen(['fio', 'current_fio_script.fio', '--output-format=json', '--output=' + output_file])
    print("Sleeping for 180 seconds (rampup period)")
    time.sleep(180)
    print("Rampup period completed")

    # Read initial values after rampup period
    initial_nand_write_count = util.read_proc_file("/proc/nvmev/ftls/nand_write_count")
    initial_write_count = util.read_proc_file("/proc/nvmev/ftls/write_count")

    # Wait for fio to complete
    fio_process.wait()

    # Read final values
    final_nand_write_count = util.read_proc_file("/proc/nvmev/ftls/nand_write_count")
    final_write_count = util.read_proc_file("/proc/nvmev/ftls/write_count")

    # Calculate deltas
    delta_nand_write_count = final_nand_write_count - initial_nand_write_count
    delta_write_count = final_write_count - initial_write_count

    # Record the result
    with open(result_file, 'a') as rf:
        rf.write(f"{config['job0_offset']} {config['job0_size']} {config['job1_offset']} {config['job1_size']} {config['job0_rate']} {config['job1_rate']} {delta_nand_write_count} {delta_write_count}\n")

    # Run rmmod.sh after finishing the test
    util.run_command("../rmmod.sh", "rmmod.sh")

# Read fio_template from file
with open('fio_template.fio', 'r') as file:
    fio_template = file.read()

# Generate and run all test cases
result_table = []
result_file = 'fio_test_results.txt'
print(job0_write_percentages, job1_write_percentages)
for job0_pct, job1_pct in zip(job0_write_percentages, job1_write_percentages):
    for range_percent in write_ranges:
        job0_offset = "0"
        job0_size = f"{range_percent}"
        job1_offset = f"{range_percent}"
        job1_size = f"{100 - range_percent}"

        # Calculate rate for job0 and job1
        job0_rate = int(total_bw * (job0_pct / 100.0))
        job1_rate = int(total_bw * (job1_pct / 100.0))

        config = {
            'job0_offset': job0_offset + "%",
            'job0_size': job0_size + "%",
            'job1_offset': job1_offset + "%",
            'job1_size': job1_size + "%",
            'job0_rate': job0_rate,
            'job1_rate': job1_rate
        }

        output_file = os.path.join(output_dir, f"fio_output_{job0_pct}_{job1_pct}_{range_percent}.json")
        run_fio(config, output_file, 'fio_test_results_waf.txt')

        result_table.append(f"{job0_pct} {job1_pct} {range_percent} {output_file}")

# Write result table to text file
with open(result_file, 'w') as rf:
    for line in result_table:
        rf.write(line + "\n")

print("All tests completed successfully.")

