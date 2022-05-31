#! /usr/bin/env python3

"""
 SSH Online to you Linux machine (only tested it on linux) for free using ngrok.
 -----------------------------------------------------------------------------
 Author: Radhi SGHAIER: https://github.com/Rad-hi
 -----------------------------------------------------------------------------
 Date: 31-05-2022 (31st of May, 2022)
 -----------------------------------------------------------------------------
 License: Do whatever you want with the code ...
          If this was ever useful to you, and we happened to meet on 
          the street, I'll appreciate a cup of dark coffee, no sugar please.
 -----------------------------------------------------------------------------
"""

import paho.mqtt.client as paho
from paho import mqtt

import threading
import json
from time import sleep
from queue import Queue

# Hive MQ account info
HIVE_MQ_USER, PASSWD = "USERNAME", "PASSWORD"
HIVE_MQ_URL, PORT = "YOUR_HIVE_MQ_URL", 8883
MAIN_TOPIC = "remote_rpi/"

# Credentials saving file path
ADDR_PORT_FILE_PATH = "./addr_port_ngrok.txt"

class MQTTCommunicator():

    TOPICS = {"ALL"         : "#",
              "alive"       : "al",
              "ngrok_creds" : "ngrok"}

    def __init__(self, is_server, RIP=True, debug=False, q_size=10):
        '''
        @param is_server: Whether this'll be instanciated as a server or receiver
        @param RIP      : Whether this object can die after it sends/receives or persist
        @param debug    : Whether to debug-print or not
        @param q_size   : The length of the sending queue
        '''

        self._is_server = is_server
        self._debug = debug
        self._rest_in_peace_after_comm = RIP

        # Flags for various events
        self._received_addr_port = False
        self._sent_addr_port = False
        self._connected = False

        # If you want data to be real_time, decrease the q_size to 1
        self._data_to_be_sent = Queue(maxsize=q_size)

        # Create the client
        self._client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)

        # enable TLS for secure connection
        self._client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self._client.username_pw_set(HIVE_MQ_USER, PASSWD)
        self._client.connect(HIVE_MQ_URL, PORT)

        # Setup callbacks
        self._client.on_connect    = self._on_connected
        self._client.on_disconnect = self._on_disconnected
        self._client.on_message    = self._on_message

        # Keep alive
        self._client.loop_start()

        # Start a seperate thread for MQTT callbacks
        self._thread = threading.Thread(target=self._loop, args=())
        self._thread.daemon = True
        self._thread.start()

    @staticmethod
    def _get_topic(topic_name):
        '''Puts all topics under a unified MAIN_TOPIC (less consumed clusters on hiveMQ)'''
        return MAIN_TOPIC + topic_name

    def _on_connected(self, client, userdata, flags, rc, properties=None):
        """Upon connection --> Suscribe to the needed topics"""
        self._connected = True
        
        if self._is_server:
            self.send_to(self.TOPICS["alive"], "I'm alive!")
        else:
            client.subscribe(self._get_topic(self.TOPICS["ngrok_creds"]), qos=1)
            #client.subscribe(self._get_topic(self.TOPICS["ALL"]), qos=1)

    @staticmethod
    def _on_disconnected(client):
        """Detect disconnection events"""
        print('Disconnected!')
    
    def _on_message(self, client, userdata, msg):
        """Callback function for when data arrives at one of the topics"""
        if self._is_server:
            # For now, no data is needed to be received on the server side
            return
        
        if msg.topic == self._get_topic(self.TOPICS["ngrok_creds"]):
            addr, port = json.loads(msg.payload).values()
            
            # Signal to the master process that we can Rest In Peace 
            self._received_addr_port = True

            # Save the just received data into a file
            self._save_addr_port(ADDR_PORT_FILE_PATH, addr, port, ':')

    @staticmethod
    def _save_addr_port(path, addr, port, sepr):
        '''
        @brief: Save the address and the port we can read through in a file
        @param path: Where to save the file
        @param addr: The public address we just received from ngrok; sender
        @param port: The port we'll read through 
        @param sepr: The seperator of the saved values in the file

        The reason for the seperator is illustrated in the next example
        expl: data = "2.tcp.eu.ngrok.io:17152:"
              data.split(':') == ['2.tcp.eu.ngrok.io', '17152', '']
              addr, port, _ = data.split(':')
        And the final ':', is used to not be sure that the port ends there (no CR/NL ...)
        '''
        with open(path, "w") as file:
            file.writelines([f"{addr}{sepr}{port}{sepr}"])

    def send_to(self, topic, data):
        """Append data to the sending queue"""
        self._data_to_be_sent.put([self._get_topic(topic), data])
    
    @property
    def is_alive(self):
        '''Is the thread still running?'''
        return self._thread.is_alive()
    
    # Sending thread
    def _loop(self):
        '''Main thread, which'll send what have to be sent, or simply wait to receive something'''
        stop = False
        while not stop:
            if self._is_server:
                if self._connected and self._data_to_be_sent.not_empty:
                    data = self._data_to_be_sent.get()

                    # The retain flag must be set here if we want to insure the 
                    # receiving end receives the data even if they aren't 
                    # listening the moment we publish the addr, port.
                    self._client.publish(data[0], data[1], qos=1, retain=True)

                    # We don't need this process to persist forever
                    if data[0] == self._get_topic(self.TOPICS['ngrok_creds']):
                        self._sent_addr_port = True

                    # Debug printing is useful
                    if self._debug:
                        print(f"[INFO] -- Sent: {data[0]}, {data[1]}")
                
            if self._rest_in_peace_after_comm:
                if self._data_to_be_sent.empty()\
                   and (self._sent_addr_port or self._received_addr_port):
                    stop = True
            
            sleep(0.05) # Release the CPU resource for the other threads, worked like a charm 
        else:
            self._client.loop_stop()