#!/usr/bin/env python
import paho.mqtt.client as mqtt
import smbus
import time
import logging
import sys

from logging import config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
			'format': '%(module)s[%(process)d]: <%(levelname)s> %(message)s'
            },
        },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
            },
        'sys-logger6': {
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'facility': "local6",
            'formatter': 'verbose',
            },
        },
    'loggers': {
        'my-logger': {
            'handlers': ['sys-logger6','stdout'],
            'level': logging.DEBUG,
            'propagate': True,
            },
        }
    }

config.dictConfig(LOGGING)

logger = logging.getLogger("my-logger")

def readSI7021():
	# SI7021 address, 0x40(64)
	#		0xF5(245)	Select Relative Humidity NO HOLD master mode
	bus.write_byte(0x40, 0xF5)
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	# Read data back, 2 bytes, Humidity MSB first
	data = bus.read_word(0x40)
	
	# Convert the data
	humidity = (data * 125 / 65536.0) - 6
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	#		0xF3(243)	Select temperature NO HOLD master mode
	bus.write_byte(0x40, 0xF3)
	
	time.sleep(0.3)
	
	# SI7021 address, 0x40(64)
	# Read data back, 2 bytes, Temperature MSB first
	data = bus.read_word(0x40)
	
	# Convert the data
	cTemp = (data * 175.72 / 65536.0) - 46.85
	fTemp = cTemp * 1.8 + 32
	

	return fTemp, humidity

if __name__== "__main__":
#logger.debug("Debug")
#logger.info("Info")
#logger.warn("Warn")
#logger.error("Error")
#logger.critical("Critical")

	# so if starting at boot, wait for the wireless to come up
	logger.info("Sleeping to wait for system up")
	time.sleep(60)

	# Get I2C bus
	bus = smbus.SMBus(1)
	
	username = "cbff9200-ffef-11e7-ac3d-75f57fc470ba"
	password = "2a1b95fc2bb43e360d9c601d4a17b882d2a4c918"
	clientid = "c92c24b0-0005-11e8-8412-27102f4df5be"
	try:
		mqttc = mqtt.Client(client_id=clientid)
		mqttc.username_pw_set(username, password=password)
		mqttc.connect("mqtt.mydevices.com", port=1883, keepalive=60)
		mqttc.loop_start()
	except Exception as e:
		logger.error("Cound not connect to MQTT broker")
		logger.error(str(e))
		sys.exit()

	logger.info("Connected to MQTT broker")
	
	topic_temp = "v1/" + username + "/things/" + clientid + "/data/1"
	topic_humidity = "v1/" + username + "/things/" + clientid + "/data/2"
	

	queryInterval = 5
	reportInterval = 300
	count = 0
	while True:
		try:
			temperature, humidity = readSI7021()
		except IOError as e:
			logger.error("Error reading sensor")
			logger.error(str(e))
			mqttc.disconnect()
			sys.exit()

		logger.info("Temp = {: >5.2f}F Humidity = {: >2.0f}".format(temperature, humidity))

		if count == 0:
			try:

				temp = "temp,f=" + str(temperature)
				mqttc.publish(topic_temp, payload=temp, retain=True)

				humid = "rel_hum,p=" + str(humidity)
				mqttc.publish(topic_humidity, payload=humidity, retain=True)
			
			except (SystemExit, KeyboardInterrupt):
				logger.info("Normal Exit")
				mqttc.disconnect()
				sys.exit()
	
			except (EOFError):
				logger.error("Lost MQTT Broker Link")
				mqttc.disconnect()
				sys.exit()

			except IOError as e:
				logger.error(str(e))
				mqttc.disconnect()

			print("sent info");
	
	
		time.sleep(queryInterval)
		count = count + 1
		if count >= (reportInterval / queryInterval):
			count = 0
	
