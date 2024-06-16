#!/bin/bash
mv proc_nvme0n1.log proc_nvme0n1.log.old
i=0; while true; do echo "$i $(cat /proc/nvmev/ftls/nand_write_count) $(cat /proc/nvmev/ftls/write_count)" | sudo tee -a proc_nvme0n1.log; ((i++)); sleep 1; done
