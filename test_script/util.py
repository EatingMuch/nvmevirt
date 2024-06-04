import subprocess
import os
import sys
import time

def run_command(command, description):
    print(f"Running: {description}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Command failed: {command}\n{stderr.decode('utf-8')}")
        print("Exiting due to failure.")
        sys.exit(1)
    print(f"Completed: {description}")
    return stdout.decode('utf-8')

# Function to read 64-bit integer from a file
def read_proc_file(file_path):
    with open(file_path, 'r') as f:
        return int(f.read().strip())
