#!/bin/bash

# sudo pip3 is required for installing for all users eg:root
# 
sudo pip3 install adafruit-circuitpython-charlcd 
sudo pip3 install adafruit-circuitpython-bme280
sudo pip3 install RPI.GPIO
sudo pip3 install azure-iot-device
sduo pip3 install w1thermsensor
sudo pip3 install requests
sudo pip3 install beuatifulsoup4
sudo pip3 install lxml
# on raspberry pi, seems to fail to install lxml parser.  requires sudo apt-get install python3-lxml
sudo apt-get install python3-lxml
