#!/bin/bash

source "/home/pi/.virtualenvs/cv2_env/bin/activate"
cd /home/pi/dev/motion
python main.py --bg-config ./config/rpi_headless_bg_subtract_config.json --pascal-voc ./config/condo_background.xml

