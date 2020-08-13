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
import threading
# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The sample connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message

DEBUG = True

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

# define degrees sign character
degrees_symbol = u'\N{DEGREE SIGN}'
lcd_degrees = chr(223)

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
    if DEBUG:
      print("Entering get_values, %s" % datetime.datetime.now().time())
    self.LoTempDS18B20 = LoTempDS18B20.get_temperature()
    self.HiTempDS18B20 = HiTempDS18B20.get_temperature()
    self.ambientTemp = bme280.temperature
    self.pressure = bme280.pressure
    self.humidity = bme280.humidity
    self.dewpoint = sensorConstant.calcDewPoint(bme280.temperature, bme280.humidity)
    self.altitude = bme280.altitude
    if DEBUG:
      print("Exiting get_values, %s" % datetime.datetime.now().time())


def set_mean_sea_level_pressure():
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
  bme280.sea_level_pressure = meanSeaLevelPressure

def iothub_client_init():
  # The device connection string to authenticate the device with your IoT hub.
  # Using the Azure CLI:
  # az iot hub device-identity show-connection-string –hub-name {YourIoTHubName} –device-id MyNodeDevice –output table
  CONNECTION_STRING = "HostName=iotbrew.azure-devices.net;DeviceId=brew-rpi;SharedAccessKey=QWAixdM8EYoBMDyUL7kqcXfA/Tddx6oE62s6KERGNJI="
  # Create an IoT Hub client
  client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
  return client
    
def iothub_client_telemetry_run():
  # Define the JSON message to send to IoT Hub.
  MSG_TXT = "{\"temperature\": %.2f,\"pressure\": %.2f,\"humidity\": %.2f,\"sensor1_temp\": %.2f,\"sensor2_temp\": %.2f,\"dewpoint\": %.2f,\"datetime\": %s}"
  
  client = iothub_client_init()
  print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )
  try:
      while True:
          sensor.get_values()
          # Build the message with telemetry values.
          msg_txt_formatted = MSG_TXT % (sensor.ambientTemp, sensor.pressure, sensor.humidity, sensor.LoTempDS18B20, sensor.HiTempDS18B20, sensor.dewpoint, datetime.datetime.now())
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

def set_sensor_values():
  while True:
    sensor.get_values()

def print_sensor_values():
  while True:
    #lcd is getting sensor values every two seconds.
    #sensor.get_values() 
    print ("\nTime: %s" % datetime.datetime.now()) 
    print ("Temperature: %0.1f%sC" % (sensor.ambientTemp, degrees_symbol))
    print ("LoTemp:      %0.1f%sC" % (sensor.LoTempDS18B20, degrees_symbol))
    print ("HiTemp:      %0.1f%sC" % (sensor.HiTempDS18B20, degrees_symbol))
    print ("Humidity:    %0.1f%%" % sensor.humidity)
    print ("Pressure:    %0.1f hPa" % sensor.pressure)
    print ("Altitude:    %0.2f meters" % sensor.altitude)
    print ("Dewpoint:    %0.1f%sC" % (sensor.dewpoint, degrees_symbol))
    time.sleep(5)
            
def set_lcd_color(temperature):
  if temperature < 18:
    lcd.color = [0,0,100]
  elif temperature < 24:
    lcd.color = [0,100,0]
  else:
    lcd.color = [100,0,0]

def scroll_lcd_text(lengthOfMessage, displayTime):
  if DEBUG:
    print("Entering scroll_lcd_text, %s" % datetime.datetime.now().time())
  if lengthOfMessage > 16:
    speed = (displayTime/((lengthOfMessage-16)*2))
  else:
    speed = 0
    time.sleep(displayTime)
  for i in range(lengthOfMessage-16):
    lcd.move_left()
    time.sleep(speed)
  for i in range(lengthOfMessage-16):
    lcd.move_right()
    time.sleep(speed)
  if DEBUG:
    print("Exiting scroll_lcd_text, %s" % datetime.datetime.now().time())

def write_lcd_message(line1, line2, msgDisplayTime):
  if DEBUG:
    print("Entering write_lcd_message, %s" % datetime.datetime.now().time())
  lcd.clear()
  lcd.cursor_position(0,0)
  lcd.message = line1
  lcd.cursor_position(0,1)
  lcd.message = line2
  if len(line1) > len(line2):
    msgLength = len(line1)
  else:
    msgLength = len(line2)
  scroll_lcd_text(msgLength,msgDisplayTime)
  if DEBUG:
    print("Exiting write_lcd_message, %s" % datetime.datetime.now().time())
  
def write_lcd():
  # put values on LCD
  if DEBUG:
    print("Entering write_lcd, %s" % datetime.datetime.now().time())
  msgDisplayTime = 2
  while True:
    set_lcd_color(sensor.ambientTemp)
    line1 = "Temp: %0.1f%sC" % (sensor.ambientTemp, lcd_degrees)
    line2 = "Pressure: %0.1f hPa" % (sensor.pressure)
    write_lcd_message(line1, line2, msgDisplayTime)
    
    line1 = "LoTemp: %0.1f%sC" % (sensor.LoTempDS18B20, lcd_degrees)
    line2 = "HiTemp: %0.1f%sC" % (sensor.HiTempDS18B20, lcd_degrees)
    write_lcd_message(line1, line2, msgDisplayTime)
    
    line1 = "Humidity: %0.1f%%" % (sensor.humidity)
    line2 = "Dew Point: %0.1f%sC" % (sensor.dewpoint, lcd_degrees)
    write_lcd_message(line1, line2, msgDisplayTime)
    if DEBUG:
      print("Exiting write_lcd, %s" % datetime.datetime.now().time())

if __name__ == '__main__':
    print ( "IoT Hub client started" )
    sensor = sensors()
    t_set_msl_pressure = threading.Thread(target=set_mean_sea_level_pressure)
    t_set_sensor_val = threading.Thread(target=set_sensor_values)
    t_print_sensor_val = threading.Thread(target=print_sensor_values)
    t_write_lcd = threading.Thread(target=write_lcd)
    t_iothub_client = threading.Thread(target=iothub_client_telemetry_run)
    
    t_set_msl_pressure.start()
    t_set_sensor_val.start()
    t_print_sensor_val.start()
    t_write_lcd.start()
    #t_iothub_client.start()
