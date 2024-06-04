SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

cd "$SCRIPT_DIR"
sudo insmod ../nvmev.ko  memmap_start=16G  memmap_size=16G cpus=7,8

cd ../spdk
sudo ./setup_spdk.sh
cd -
