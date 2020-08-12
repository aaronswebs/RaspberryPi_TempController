#!/usr/bin/env python3

import math
# Addresses of DS18B20 Temperature sensors
# 00000b854aa2 is the hightemp cable DS18B20
# 03166479d9ff is the normal cable DS18B20
hightempSensor = '00000b854aa2'
normaltempSensor = '03166479d9ff'

# dewpoint calc using Magnus formula
# https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point
def calcDewPoint(temperature, humidity):
  b = 17.62
  c = 243.12
  gamma = (b * temperature /(c + temperature)) + math.log(humidity / 100.0)
  dewpoint = (c * gamma) / (b - gamma)
  return dewpoint

if __name__ == '__main__':
    print ( "Designed to be imported not run as script" )
