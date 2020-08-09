#!/usr/bin/env python3
import time
import glob
import math
import datetime
# prerequisite installs are:
# pip3 install adafruit-circuitpython-charlcd 
# pip3 install adafruit-circuitpython-bme280
# pip3 install RPI.GPIO
# pip3 install azure-iot-device
# pip3 install w1thermsensor
# sudo pip3 is required for installing for all users eg:root
import board
import busio
import adafruit_bme280
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The sample connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message

# temp sensor devices
# 28-00000b854aa2 is the hightemp cable DS18B20
# 28-03166479d9ff is the normal cable DS18B20
#example usage
# from w1thermsensor import W1ThermSensor
#for sensor in W1ThermSensor.get_available_sensors():
#    print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
# sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "00000588806a")
# temperature_in_celsius = sensor.get_temperature()
# temperature_in_fahrenheit = sensor.get_temperature(W1ThermSensor.DEGREES_F)
# temperature_in_all_units = sensor.get_temperatures([
#     W1ThermSensor.DEGREES_C,
#     W1ThermSensor.DEGREES_F,
#     W1ThermSensor.KELVIN])

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

#directory for One-Wire devices
base_dir = '/sys/bus/w1/devices/'
devices_folder = glob.glob(base_dir + '28*')

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# Initialise the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
lcd.clear()

#set variables for dewpoint calc
b = 17.62
c = 243.12

# OR create library object using our Bus SPI port
# spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# bme_cs = digitalio.DigitalInOut(board.D10)
# bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1014.5
lcd.color = [100, 0, 0]

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string –hub-name {YourIoTHubName} –device-id MyNodeDevice –output table
CONNECTION_STRING = "HostName=iotbrew.azure-devices.net;DeviceId=brew-rpi;SharedAccessKey=QWAixdM8EYoBMDyUL7kqcXfA/Tddx6oE62s6KERGNJI="

# Define the JSON message to send to IoT Hub.
TEMPERATURE = bme280.temperature
PRESSURE = bme280.pressure
HUMIDITY = bme280.humidity
MSG_TXT = "{\"temperature\": %.2f,\"pressure\": %.2f,\"humidity\": %.2f,\"sensor1_temp\": %.2f,\"sensor2_temp\": %.2f}"

def read_temp_raw(tempdevice_file):
    f = open(tempdevice_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    return client
    
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def iothub_client_telemetry_run():
    client = iothub_client_init()
    print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )
    try:
        while True:
            #calculate dew point
            gamma = (b * bme280.temperature /(c + bme280.temperature)) + math.log(bme280.humidity / 100.0)
            dewpoint = (c * gamma) / (b - gamma)
            print ("\nTemperature: %0.1f C" % bme280.temperature)
            print ("Humidity: %0.1f %%" % bme280.humidity)
            print ("Pressure: %0.1f hPa" % bme280.pressure)
            #Altitude requires Mean Sea Level Pressure from Weather web site
            #print ("Altitude = %0.2f meters" % bme280.altitude)
            print ("Dewpoint: %0.1f C" % dewpoint)
            for x in devices_folder:
              device_file = x + '/w1_slave'
              device_arr = device_file.rsplit("/")
              deviceID = device_arr[5]
              if deviceID == "28-03166479d9ff":
                  AmbientDS18B20 = read_temp(device_file)
                  print("Sensor1: " + format(AmbientDS18B20))
              elif deviceID == "28-00000b854aa2":
                  HiTempDS18B20 = read_temp(device_file)
                  print("Sensor2: " + format(HiTempDS18B20))
              else:
                  print(deviceID)

            # Build the message with telemetry values.
            temperature = bme280.temperature
            pressure = bme280.pressure
            humidity = bme280.humidity
            msg_txt_formatted = MSG_TXT % (temperature, pressure, humidity, AmbientDS18B20, HiTempDS18B20)
            message = Message(msg_txt_formatted)
            
            # set LCD colour
            if temperature < 18:
              lcd.color = [0,0,100]
            elif temperature < 24:
              lcd.color = [0,100,0]
            else:
              lcd.color = [100,0,0]
            # put values on LCD
            lcd.message = "Temp: %0.2f C\nTime: %s" % (temperature, datetime.datetime.now().time())

            # Add a custom application property to the message.
            # An IoT hub can filter on these properties without access to the message body.
            if temperature < 17:
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

if __name__ == '__main__':
    print ( "IoT Hub client started" )
    iothub_client_telemetry_run()