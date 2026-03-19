#!/bin/bash

# Detect OS
. /etc/os-release

if [[ "$ID" == "ubuntu" || "$ID_LIKE" == *"debian"* ]]; then
    DHCP_SERVICE="isc-dhcp-server"
    NFS_SERVICE="nfs-kernel-server"
    TFTP_SERVICE="tftpd-hpa"
else
    # Fedora / RHEL
    DHCP_SERVICE="dhcpd"
    NFS_SERVICE="nfs-server"
    TFTP_SERVICE="tftp"
    sudo systemctl stop tftp.socket
fi

sudo systemctl stop "${DHCP_SERVICE}.service"
sudo systemctl stop "${NFS_SERVICE}.service"
sudo systemctl stop "${TFTP_SERVICE}.service"

if mountpoint -q /rpi/firmware; then
	echo "UNMOUNTING /rpi/firmware"
	sudo umount -f -l /rpi/firmware
fi

if mountpoint -q /rpi/root; then
	echo "UNMOUNTING /rpi/root"
	sudo umount -f -l /rpi/root
fi

if mountpoint -q /rpi/internals/base; then
	echo "UNMOUNTING /rpi/internals/base"
	sudo umount -f -l /rpi/internals/base
fi

sudo rm -rf /rpi

ssh-keygen -R 192.168.0.100
ssh-keygen -R pi

sudo mkdir -p /rpi/internals
sudo mkdir -p /rpi/firmware
sudo mkdir -p /rpi/root
sudo mkdir -p /rpi/internals/workdir
sudo mkdir -p /rpi/internals/changes-base
sudo mkdir -p /rpi/internals/base

sudo wget -O /rpi/pi.img.xz https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2025-05-13/2025-05-13-raspios-bookworm-arm64-lite.img.xz

sudo unxz /rpi/pi.img.xz

IMG=/rpi/pi.img

ETH_IF=$(nmcli -t -f DEVICE,TYPE device status | grep ':ethernet$' | cut -d: -f1)
echo $ETH_IF
IP=$(ifconfig $ETH_IF | awk '/inet / && $2 !~ /^127/ {print $2; exit}')
echo $IP

echo "server $IP iburst" > chrony.sources

user=${SUDO_USER:-$USER}
SSH_DIR=$(eval echo "~$user")/.ssh
echo $SSH_DIR

sudo ../sdm/sdm \
  --customize \
  --batch \
  --extend --xmb 4096 \
  --plugin user:"deluser=pi" \
  --plugin user:"adduser=robotino|password=dynabot|uid=1000" \
  --plugin disables:piwiz \
  --plugin L10n:host \
  --plugin copyfile:"from=camera-server.service|to=/etc/systemd/system/" \
  --plugin system:"service-enable=camera-server.service" \
  --plugin apps:"apps=vim libcamera-dev python3-libcamera libcap-dev python3-dev build-essential libgl1-mesa-glx python3-kms++ git cmake" \
  --plugin venv:"path=/home/robotino/venv|create=true|requirements=object-detection/requirements.txt|createoptions=--system-site-packages" \
  --plugin copyfile:"from=settings.yaml|to=/home/robotino/.config/Ultralytics|mkdirif|chown=robotino:robotino|chmod=644" \
  --cscript ./config-phase \
  --custom1 $IP \
  --custom2 $SSH_DIR \
  --plugin chrony:"sources=chrony.sources|nodistsources" \
  --apt-options noupgrade \
  --regen-ssh-host-keys \
  $IMG


rm chrony.sources

sudo 7z x $IMG -o/rpi/internals

sudo rm $IMG

sudo mv /rpi/internals/0.fat /rpi/internals/firmware.fat
sudo mv /rpi/internals/1.img /rpi/internals/base.img

sudo mount -o ro /rpi/internals/firmware.fat /rpi/firmware
sudo mount -o ro /rpi/internals/base.img /rpi/internals/base

sudo mount -t overlay overlay /rpi/root \
  -o lowerdir=/rpi/internals/base,upperdir=/rpi/internals/changes-base,workdir=/rpi/internals/workdir,\
index=on,nfs_export=on,redirect_dir=nofollow

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart "${DHCP_SERVICE}.service"
sudo systemctl restart "${NFS_SERVICE}.service"
sudo systemctl restart "${TFTP_SERVICE}.service"
