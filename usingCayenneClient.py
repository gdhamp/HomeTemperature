#!/usr/bin/env python
import cayenne.client
#import paho.mqtt.client as mqtt
import smbus
import time
import sys

def readSI7021():
	# SI7021 address, 0x40(64)
	#		0xF5(245)	Select Relative Humidity NO HOLD master mode
	bus.write_byte(0x40, 0xF5)
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	# Read data back, 2 bytes, Humidity MSB first
	data0 = bus.read_byte(0x40)
	data1 = bus.read_byte(0x40)
	
	# Convert the data
	humidity = ((data0 * 256 + data1) * 125 / 65536.0) - 6
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	#		0xF3(243)	Select temperature NO HOLD master mode
	bus.write_byte(0x40, 0xF3)
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	# Read data back, 2 bytes, Temperature MSB first
	data0 = bus.read_byte(0x40)
	data1 = bus.read_byte(0x40)
	
	# Convert the data
	cTemp = ((data0 * 256 + data1) * 175.72 / 65536.0) - 46.85
	fTemp = cTemp * 1.8 + 32
	

	return fTemp, humidity


# The callback for when a message is received from Cayenne.
def on_message(message):
	print("message received: " + str(message))
	# If there is an error processing the message return an error string,
	# otherwise return nothing.


if __name__== "__main__":
	# Get I2C bus
	bus = smbus.SMBus(1)
	#	time.sleep(30) #Sleep to allow wireless to connect before starting MQTT
	
	MQTT_USERNAME = "cbff9200-ffef-11e7-ac3d-75f57fc470ba"
	MQTT_PASSWORD = "2a1b95fc2bb43e360d9c601d4a17b882d2a4c918"
	MQTT_CLIENT_ID = "c92c24b0-0005-11e8-8412-27102f4df5be"
	
	client = cayenne.client.CayenneMQTTClient()
	client.on_message = on_message
	client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)

	timestamp = 0
	
	while True:

		client.loop()
	    
		if (time.time() > timestamp + 10):
			temperature, humidity = readSI7021()

			print temperature
			print humidity

			client.fahrenheitWrite(1, temperature)
			client.virtualWrite(2, humidity, 'rel_hum', 'p')
			timestamp = time.time()





