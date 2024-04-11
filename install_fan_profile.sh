#!/bin/bash

# This script will install the win minifan profile in the nbfc config directory and set it as the current profile.


if [ "$EUID" -ne 0 ]
    then echo "Please run as root"
    exit
fi
cp ./fan_profiles/GPD_Win_Mini2.json /usr/share/nbfc/configs/GPD_Win_Mini.json
nbfc config -a GPD_Win_Mini