import glob
import time
from w1thermsensor import W1ThermSensor

# temp sensor devices
# 28-00000b854aa2 is the hightemp cable DS18B20
# 28-03166479d9ff is the normal cable DS18B20

for sensor in W1ThermSensor.get_available_sensors():
   print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))

sensor1 = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "00000b854aa2")
sensor2 = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "03166479d9ff")
temperature_in_celsius = sensor1.get_temperature()
#temperature_in_fahrenheit = sensor.get_temperature(W1ThermSensor.DEGREES_F)
#temperature_in_all_units = sensor.get_temperatures([
#    W1ThermSensor.DEGREES_C,
#    W1ThermSensor.DEGREES_F,
#    W1ThermSensor.KELVIN])

print("Sensor1-HiTemp: %0.2f" % sensor1.get_temperature())
print("Sensor2-Temp: %0.2f" % sensor2.get_temperature())
time.sleep(5)