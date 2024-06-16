#!/bin/bash
set -e
../make.sh
sudo insmod ../../nvmev.ko  memmap_start=16G  memmap_size=16G cpus=7,8

sudo mkfs.f2fs /dev/nvme0n1 -f
sudo mount /dev/nvme0n1 /mnt/f2fs
sudo mkdir /mnt/f2fs/filebench
echo 1000 | sudo tee /proc/sys/vm/vfs_cache_pressure

echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
# Start filebench in the background
sudo filebench -f fileserver.f &
FILEBENCH_PID=$!

# Start iostat and redirect output to a log file
rm bw_nvme0n1.log -rf
./log_bw.sh &
IOSTAT_PID=$!


./log_waf.sh &
PROC_PID=$!

# Wait for filebench to finish
wait $FILEBENCH_PID

# Kill iostat after filebench finishes
kill $IOSTAT_PID
kill $PROC_PID

sleep 3

sudo umount /mnt/f2fs
sudo ../rmmod.sh


