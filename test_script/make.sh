#!/bin/bash

SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

cd "$SCRIPT_DIR"

cd ..
make -C /mnt/modules M=$(pwd) modules -j
cd -
