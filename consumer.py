#! /usr/bin/env python3

'''
Reads the last retained value of the URL:PORT that exists on HiveMQ, and saves it to a file
Voilà, SSH!
'''

from mqtt_communicator.mqtt_communicator import MQTTCommunicator

from time import sleep

def main():
    mqtt_com = MQTTCommunicator(is_server=False, RIP=True)

    # Wait until we get the data we want
    while mqtt_com.is_alive:
        sleep(1.0)

if __name__ == '__main__':
    main()