#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import board
import busio
import adafruit_bme280

# requires the following pre-requisites
# pip3 install requests
# pip3 install beuatifulsoup4
# pip3 install lxml
# pip3 install adafruit-circuitpython-bme280
# pip3 install RPI.GPIO

# Make a GET request to fetch the raw HTML content
url = "http://www.bom.gov.au/vic/observations/vicall.shtml?ref=hdr"
response = requests.get(url)
html_content = response.text

if response.status_code == 200:
    print('Success')
else:
    print('Failed to get URL')
    raise Exception('Did not get valid response from server for %s' % url)

# Parse the html content
soup = BeautifulSoup(html_content, "lxml")
tableCell = soup.find("td", attrs={"headers":"tCEN-press tCEN-station-melbourne-olympic-park"})


# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

meanSeaLevelPressure = float(tableCell.string)
print(meanSeaLevelPressure)
bme280.sea_level_pressure = meanSeaLevelPressure
print("Altitude = %0.2f meters" % bme280.altitude)