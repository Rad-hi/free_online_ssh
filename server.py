#! /usr/bin/env python3

'''
Starts an ngrok session, sends the URL:PORT to HiveMQ
for the consumer script to retrieve and save to a file.
Voilà, SSH!
'''

from mqtt_communicator.mqtt_communicator import MQTTCommunicator

from pyngrok import ngrok # Ref: https://pyngrok.readthedocs.io/en/latest/index.html#open-a-tunnel
import json

TUNNEL, PORT = "tcp", "YOUR_SSH_PORT"
NGROK_AUTH_TOKEN = "PUT_YOUR_AUTH_TOKEN_HERE" # Make a free account and get this

def main():
    '''Starts the ngrok ssh-tunnel, and sends the URL/PORT to the MQTT broker'''

    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    ssh_tunnel = ngrok.connect(PORT, TUNNEL)
    
    # print(ssh_tunnel) to understand this split madness
    addr, port = str(ssh_tunnel).split(' ')[1].split('//')[1][:-1].split(':') 

    mqtt_comm = MQTTCommunicator(is_server=True, RIP=True, debug=True)
    payload = json.dumps({'addr': addr, 'port': port})
    mqtt_comm.send_to(mqtt_comm.TOPICS["ngrok_creds"], data=payload)

    # Keep the ngrok connection alive
    ngrok_process = ngrok.get_ngrok_process()
    try:
        # Block until CTRL-C or some other terminating event
        ngrok_process.proc.wait()
    except KeyboardInterrupt:
        print(" Shutting down server.")
        ngrok.kill()

if __name__ == '__main__':
    main()
