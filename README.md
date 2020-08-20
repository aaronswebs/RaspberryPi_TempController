# Raspberry Pi Temp controller

The concept for this project originated from being a first time brewer and all of the stories about managing temperature for fermentation.

Initially I started out with a Raspberry Pi and a BME280 sensor, however I quickly added an LCD and 1-wire DS18B20 sensors - one designed for the outside of the fermenter, held in place with blu-tac as an insulator from ambient temperature, and another sensor with food safe heat shrink to be placed in the fermentation liquid.

I also wanted this to be used to control still temperature and avoid overheating the wash and then reducing heat with high amounts of water.

I have added a Sparkfun Beefcake relay to manage comfortably switching 10 amps of 240v for chillers / heaters or a still heating element.

A five button keyboard has been added to give some menu capability and control temperature set points and scroll through various values.

Target state is to introduce some PID control as well, however the relay will need to be swapped out for something like a MOSFET for current control rather on / off switching.

#TODO Implement PID using simplepid

#TODO Implement LCD menu interface

Application Architecture:

![](https://github.com/the-ranga/RaspberryPi_TempController/blob/master/menu-stub%20(main).gif)