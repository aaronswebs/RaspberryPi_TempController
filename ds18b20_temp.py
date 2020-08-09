import glob
import time

# devices
# 28-00000b854aa2 is the high temp DS18B20
# 28-03166479d9ff is the normal DS18B20

base_dir = '/sys/bus/w1/devices/'

def read_temp_raw(tempdevice_file):
    f = open(tempdevice_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

while True:
    devices_folder = glob.glob(base_dir + '28*')
    for x in devices_folder:
      device_file = x + '/w1_slave'
      device_arr = device_file.rsplit("/")
      deviceID = device_arr[5]
      if deviceID == "28-03166479d9ff":
          print("Ambient: " + format(read_temp(device_file)))
      elif deviceID == "28-00000b854aa2":
          print("HiTemp: " + format(read_temp(device_file)))
      else:
          print(deviceID)
      #print("Device: " + x + " Temp: " + format(read_temp(device_file)))
    time.sleep(60)