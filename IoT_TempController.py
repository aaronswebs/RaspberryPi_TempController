#!/usr/bin/env python3
import time
import datetime
import board
import busio
import adafruit_bme280
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from w1thermsensor import W1ThermSensor
import sensorConstant
from bs4 import BeautifulSoup
import requests
# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The sample connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# Initialise the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
lcd.clear()
lcd.color = [100, 0, 0]

# Initialise the temp sensors
LoTempDS18B20 = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorConstant.normaltempSensor)
HiTempDS18B20 = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorConstant.hightempSensor)

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string –hub-name {YourIoTHubName} –device-id MyNodeDevice –output table
CONNECTION_STRING = "HostName=iotbrew.azure-devices.net;DeviceId=brew-rpi;SharedAccessKey=QWAixdM8EYoBMDyUL7kqcXfA/Tddx6oE62s6KERGNJI="

# Define the JSON message to send to IoT Hub.
MSG_TXT = "{\"temperature\": %.2f,\"pressure\": %.2f,\"humidity\": %.2f,\"sensor1_temp\": %.2f,\"sensor2_temp\": %.2f,\"dewpoint\": %.2f}"

# define degrees sign character
degrees_symbol = u'\N{DEGREE SIGN}'

def get_mean_sea_level_pressure():
  # Make a GET request to fetch the raw HTML content
  url = "http://www.bom.gov.au/vic/observations/vicall.shtml?ref=hdr"
  try:
    response = requests.get(url)
    html_content = response.text

    if response.status_code == 200:
        print('Success - retrieved BOM observations') 
    else:
        print('Failed to get %s or content' % url)
        raise Exception('Did not get valid response from server for %s' % url)
  except:
    print('Failed to retrieve HTML weather data')

  # Parse the html content
  soup = BeautifulSoup(html_content, "lxml")
  tableCell = soup.find("td", attrs={"headers":"tCEN-press tCEN-station-melbourne-olympic-park"})
  meanSeaLevelPressure = float(tableCell.string)
  return meanSeaLevelPressure

class sensors():
  def __init__(self):
    self.LoTempDS18B20 = 0.0
    self.HiTempDS18B20 = 0.0
    self.ambientTemp = 0.0
    self.pressure = 0.0
    self.humidity = 0.0
    self.dewpoint = 0.0
    self.altitude = 0.0

  def get_values(self):
    self.LoTempDS18B20 = LoTempDS18B20.get_temperature()
    self.HiTempDS18B20 = HiTempDS18B20.get_temperature()
    self.ambientTemp = bme280.temperature
    self.pressure = bme280.pressure
    self.humidity = bme280.humidity
    self.dewpoint = sensorConstant.calcDewPoint(bme280.temperature, bme280.humidity)
    bme280.sea_level_pressure = get_mean_sea_level_pressure()
    self.altitude = bme280.altitude

def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    return client
    
def iothub_client_telemetry_run():
    client = iothub_client_init()
    print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )
    try:
        while True:
            sensor.get_values()
            # Build the message with telemetry values.
            msg_txt_formatted = MSG_TXT % (sensor.ambientTemp, sensor.pressure, sensor.humidity, sensor.LoTempDS18B20, sensor.HiTempDS18B20, sensor.dewpoint)
            message = Message(msg_txt_formatted)

            # Add a custom application property to the message.
            # An IoT hub can filter on these properties without access to the message body.
            if sensor.ambientTemp < 17:
              message.custom_properties["temperatureAlert"] = "true"
            else:
              message.custom_properties["temperatureAlert"] = "false"
            # Send the message.
            print ( "Sending message: {}".format(message) )
            client.send_message(message)
            print ( "Message successfully sent" )
            time.sleep(300)
    except KeyboardInterrupt:
        print ("\nStopped IoT Messages and Device")

def print_readings():
  print ("\nTemperature: %0.1f%sC" % sensor.ambientTemp, degrees_symbol)
  print ("LoTemp: %0.1f%sC" % sensor.LoTempDS18B20, degrees_symbol)
  print ("HiTemp: %0.1f%sC" % sensor.HiTempDS18B20, degrees_symbol)
  print ("Humidity: %0.1f %%" % sensor.humidity)
  print ("Pressure: %0.1f hPa" % sensor.pressure)
  print ("Altitude = %0.2f meters" % sensor.altitude)
  print ("Dewpoint: %0.1f%sC" % sensor.dewpoint, degrees_symbol)
            
def set_lcd_color(temperature):
  if temperature < 18:
    lcd.color = [0,0,100]
  elif temperature < 24:
    lcd.color = [0,100,0]
  else:
    lcd.color = [100,0,0]

def write_lcd():
  # put values on LCD
  temperature = sensor.ambientTemp
  lcd.message = "Temp: %0.2f C\nTime: %s" % (temperature, datetime.datetime.now().time())

if __name__ == '__main__':
    print ( "IoT Hub client started" )
    #iothub_client_telemetry_run()
    sensor = sensors()
    sensor.get_values()
    set_lcd_color(sensor.ambientTemp)
    print_readings()