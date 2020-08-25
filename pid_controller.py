#!/usr/bin/env python3
import time
import datetime
import board
import busio
import adafruit_bme280
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from w1thermsensor import W1ThermSensor
import sensorConstant
import threading
from simple_pid import PID # https://github.com/m-lundberg/simple-pid
import RPi.GPIO as GPIO

DEBUG = 3

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# Initialise the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
lcd.clear()
lcd.color = [100, 100, 100]

# Initialise the temp sensors
outside_container_temp = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorConstant.normaltempSensor)
liquid_temp = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorConstant.hightempSensor)

# define degrees sign character
degrees_symbol = u'\N{DEGREE SIGN}'
lcd_degrees = chr(223)

# initialise relay GPIO control pin
relay_pin = 17
GPIO.setmode(GPIO.BCM) 
GPIO.setup(relay_pin, GPIO.OUT, initial=GPIO.LOW) 

# PID defaults
default_temp_setpoint = 25
pid = PID(5, 0.1, 0.1, setpoint=default_temp_setpoint)

class sensors():
  def __init__(self):
    if (DEBUG > 0) and (DEBUG >= 9):
      print("Initialising sensors, %s" % datetime.datetime.now().time())
    self.outside_container_temp = 0.0
    self.liquid_temp = 0.0
    self.ambientTemp = 0.0
    # using a resolution of 9 bits has a 93.75ms response time.  12 bits is 750 ms.
    # there is about ~100ms of overhead on the w1-therm library function calls.
    liquid_temp.set_resolution(11)
    outside_container_temp.set_resolution(11)

  def get_values(self):
    if (DEBUG > 0) and (DEBUG >= 5):
      print("Entering get_values, %s" % datetime.datetime.now().time())
      start_time = time.time()
      time_split = time.time()
    self.liquid_temp = liquid_temp.get_temperature()
    if (DEBUG > 0) and (DEBUG >= 9):
      liquid_sensor_time = time.time() - time_split
      time_split = time.time()
    self.outside_container_temp = outside_container_temp.get_temperature()
    if (DEBUG > 0) and (DEBUG >= 9):
      outside_sensor_time = time.time() - time_split
      time_split = time.time()
    self.ambientTemp = bme280.temperature
    if (DEBUG > 0) and (DEBUG >= 9):
      ambient_sensor_time = time.time() - time_split
      time_split = time.time()
    if (DEBUG > 0) and (DEBUG >= 9):
      time_split = time.time()
      runtime = time.time() - start_time
      print("Function run time:  {runtime:0.7f}".format(runtime=runtime,))
      print("Outside Sensor:     {outside:0.7f}".format(outside=outside_sensor_time,))
      print("Liquid Sensor:      {liquid:0.7f}".format(liquid=liquid_sensor_time,))
      print("Ambient Sensor:     {ambient:0.7f}".format(ambient=ambient_sensor_time,))
    if (DEBUG > 0) and (DEBUG >= 5):
      print("Exiting get_values, %s" % datetime.datetime.now().time())

def set_sensor_values(update_interval, thread_event):
  while not thread_event.isSet():
    if (DEBUG > 0) and (DEBUG >= 5):
        print("Entering set_sensor_values loop, %s" % datetime.datetime.now().time())
    entry_time = time.time()
    sensor.get_values()
    exit_time = time.time()
    if (DEBUG > 0) and (DEBUG >= 5):
        print("Exiting set_sensor_values loop, %s" % datetime.datetime.now().time())
    thread_event.wait(update_interval-(exit_time - entry_time))

def print_sensor_values(thread_event):
  while not thread_event.isSet():
    # main thread gets frequent upates of sensors
    print ("\nTime: %s" % datetime.datetime.now()) 
    print ("Ambient:     %0.2f%sC" % (sensor.ambientTemp, degrees_symbol))
    print ("Container:   %0.2f%sC" % (sensor.outside_container_temp, degrees_symbol))
    print ("Liquid:      %0.2f%sC" % (sensor.liquid_temp, degrees_symbol))
    print ("PID Components")
    print ("P=%0.3f I=%0.3f D=%0.3f" % (pid.components))
    thread_event.wait(5)
            
def set_lcd_color(temperature):
  if temperature < 18:
    lcd.color = [0,0,100]
  elif temperature < 24:
    lcd.color = [0,100,0]
  else:
    lcd.color = [100,0,0]

def scroll_lcd_text(lengthOfMessage, displayTime, thread_event):
  if (DEBUG > 0) and (DEBUG >= 5):
    print("Entering scroll_lcd_text, %s" % datetime.datetime.now().time())
  
  #calculate how many chars over flow LCD columns (16) and add padding
  lcd_column_overflow = lengthOfMessage-lcd_columns
  lcd_column_padding = 2
  scroll_iterations = lcd_column_overflow + lcd_column_padding
  scroll_speed = 0

  if lengthOfMessage > 16:
    scroll_speed = (displayTime/((scroll_iterations)*2))
    for i in range(scroll_iterations*2):
      if thread_event.isSet():
        break
      if i < scroll_iterations:
        lcd.move_left()
      else:
        lcd.move_right()
      thread_event.wait(scroll_speed)
  else:
    if thread_event.isSet():
      return
    thread_event.wait(displayTime)

  if (DEBUG > 0) and (DEBUG >= 5):
    print("Exiting scroll_lcd_text, %s" % datetime.datetime.now().time())

def write_lcd(thread_event):
    # put values on LCD
    if (DEBUG > 0) and (DEBUG >= 5):
      print("Entering write_lcd, %s" % datetime.datetime.now().time())
    msgDisplayTime = 3
    
    while not thread_event.isSet():
      set_lcd_color(sensor.ambientTemp)
      # set text for LCD lines
      message_lines = [ \
      "Ambient: %0.2f%sC" % (sensor.ambientTemp, lcd_degrees), \
      "Container: %0.2f%sC" % (sensor.outside_container_temp, lcd_degrees), \
      "Liquid: %0.2f%sC" % (sensor.liquid_temp, lcd_degrees), \
      "PID Values", \
      "P=%0.2f I=%0.2f D=%0.2f" % (pid.components) ]

      for i in range(0, len(message_lines), 2):
        if thread_event.isSet():
          break
        lcd.clear()
        lcd.cursor_position(0,0)
        lcd.message = message_lines[i]
        msgLength = len(message_lines[i])
        if not (i+1 > len(message_lines)):
          if (DEBUG > 0) and (DEBUG >= 3):
            print("i= {}, i+1= {} length= {}, calc= {}".format(i,i+1,len(message_lines),not (i+1 > len(message_lines))))
          lcd.cursor_position(0,1)
          lcd.message = message_lines[i+1]
          if len(message_lines[i]) < len(message_lines[i+1]):
            msgLength = len(message_lines[i+1])
        scroll_lcd_text(msgLength,msgDisplayTime, thread_event)
      if (DEBUG > 0) and (DEBUG >= 5):
        print("Exiting write_lcd, %s" % datetime.datetime.now().time())

def relay_on(control):
  if (DEBUG > 0) and (DEBUG >= 5):
    print("Entering relay_on, %s" % datetime.datetime.now().time())

  if control:
    if (DEBUG > 0) and (DEBUG >= 3):
      print("Relay On; Control value: {}".format(control))
    GPIO.output(relay_pin, True)
  else:
    if (DEBUG > 0) and (DEBUG >= 3):
      print("Relay Off; Control value: {}".format(control))
    GPIO.output(relay_pin, False)
  if (DEBUG > 0) and (DEBUG >= 5):
    print("Exiting relay_on, %s" % datetime.datetime.now().time())

def pid_control(interval, thread_event):
  if (DEBUG > 0) and (DEBUG >= 5):
    print("Entering pid_control, %s" % datetime.datetime.now().time())
  if (DEBUG > 0) and (DEBUG >= 3):
    start_time = time.time()
    setpoint, y, x, pidcomponents, pidoutput = [], [], [], [], []
   
  # output value will be between 0 and 100. need duty cycle for relay.  
  pid.output_limits = (0, 100) 
  pid.sample_time = interval  # update PID model every interval seconds
  pid.auto_mode = True
  # pid.setpoint = 10 # reset setpoint to value

  while not thread_event.isSet():
    if (DEBUG > 0) and (DEBUG >= 5):
      print("Entering pid_control loop, %s" % datetime.datetime.now().time())
    entry_time = time.time()
    # initial thought of grabbing from class - may not be updated frequently enough.
    # relay_on(pid(sensor.outside_container_temp))

    # grab sensor value directly - ie: do not rely on the set_sensor_val function for updates.
    # using a resolution of 9 bits has a 93.75ms response time.  12 bits is 750 ms.
    relay_on(pid(outside_container_temp.get_temperature()))
    
    if (DEBUG > 0) and (DEBUG >= 3):
      current_time = time.time()
      x += [current_time - start_time]
      y += [sensor.outside_container_temp]
      setpoint += [pid.setpoint]
      pidcomponents += [pid.components]
      pidoutput += [pid(outside_container_temp.get_temperature())]

    exit_time = time.time()
    # run every interval.  Calc wait time based on processing time.
    if (DEBUG > 0) and (DEBUG >= 5):
      print("Exiting pid_control loop, %s" % datetime.datetime.now().time())
    thread_event.wait(interval-(exit_time - entry_time))  

  if (DEBUG > 0) and (DEBUG >= 3):
    for points in len(y):
        print("{},{},{},{},{}\n".format(setpoint[points],x[points],y[points],pidoutput[points],pidcomponents[points],))
        #print(y)
        #print(x)
  if (DEBUG > 0) and (DEBUG >= 5):
    print("Exiting pid_control, %s" % datetime.datetime.now().time())

def start_menu():
    lcd.clear()
    lcd.home()
    lcd.message = "I am in the menu\nPress Select to continue"
    
    while True:
      if lcd.select_button:
        lcd.clear()
        lcd.message = "Bye!"
        return None

# ############
# main process
# ############
if __name__ == '__main__':
    sensor = sensors()
    thread_event = threading.Event()

    # initialise thread instances
    t_set_sensor_val = threading.Thread(target=set_sensor_values, args=(5, thread_event,))
    t_print_sensor_val = threading.Thread(target=print_sensor_values, args=(thread_event,))
    t_write_lcd = threading.Thread(target=write_lcd, args=(thread_event,))
    t_pid_control = threading.Thread(target=pid_control, args=(1, thread_event,))
    
    # start threads
    t_set_sensor_val.start()
    print ( "Brew IoT Controller Started." )
    lcd.message = "Brew IoT Control\nStarted!"
    thread_event.wait(2)
    if (DEBUG > 0) and (DEBUG >= 1):
      t_print_sensor_val.start()
    t_write_lcd.start()
    t_pid_control.start()
    
    while not thread_event.isSet():
      try:
        if lcd.select_button:
          lcd.message = "Select!"
          thread_event.set()
          start_menu()
          print("Set event and halting")
          break
        thread_event.wait(2)
      except KeyboardInterrupt:
        thread_event.set()
        print("Got a keyboard interupt and terminating, %s" % datetime.datetime.now().time())
        break
