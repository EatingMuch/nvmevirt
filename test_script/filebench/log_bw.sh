#!/bin/bash
mv bw_nvme0n1.log bw_nvme0n1.log.old
i=0; while true; do iostat | grep "nvme0n1" | awk '{print $3, $4}' |  sudo tee -a bw_nvme0n1.log; ((i++)); sleep 1; done
