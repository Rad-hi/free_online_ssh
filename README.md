# SSH into your Linux machine over the internet FOR FREE

## The WHY?

Integrating single board computers into robots could pose a couple problems, like powering them, or accessing them when still developing to tweak something. 

And while you can easily find, almost everywhere, how to SSH into your **headless** RPI in the same network, when you add the "over the internet" or "online" keyword to your search, suddenly you're on your own, or at least if you're someone like me who isn't willing yet to pay for a solution or just want to experiment with something, you are indeed left with no solution.

Well, I had a robot with a **Nvidia Jetson Nano** onboard, and I wanted to SSH to it over the internet, since it had no WiFi card, and **I wanted to**. So I went searching .. with no avail.

At this point I've tried more than 6 tools I found online that claimed to be free, but none worked, until I tried [ngrok](https://ngrok.com/) which was seriously one of the easiest tools to use that I ever tried. But there was a problem, ngrok only gives only **a single open port at a time** and more importantly, **changes the public URL:PORT each time it's relaunched**, and here was my problem.

## The HOW?

Upon further research, I had the idea of "if I only had a way to retrieve the URL:PORT programmatically, I would send them over one of the free MQTT brokers over there {[Adafruit.IO](https://io.adafruit.com/), [HiveMQ](https://www.hivemq.com/), ..},launch the sending script on startup, and life'd be beautiful". So I researched, and I eventually came across [pyngrok](https://pypi.org/project/pyngrok/), and suddenly it clicked.

So using pyngrok, I found their example on how to launch an SSH tunnel using Python, I then figured how to retrieve the URL:PORT, and once I saw them printed on my terminal knew that I did it.

From there, I scripted a simple ```MQTTCommunicator``` class that does the basic functionalities, and within a couple hours, I'm SSH-ing to my Nvidia Jetson with absolutely no problems.

## The QUICKSTART:

***What you'll only have to do once***

1- You'll need to create a **free** ngrok account (and get your authtoken, which you'll need for creating TCP tunnels)

2- You'll need to create a **free** HiveMQ account (and get your user name, and password, which you'll need to connect to the broker)

3- Modify ```mqtt_communicator.py``` with your HiveMQ account info

    # Hive MQ account info
    HIVE_MQ_USER, PASSWD = "USERNAME", "PASSWORD"
    HIVE_MQ_URL, PORT = "YOUR_HIVE_MQ_URL", 8883

4- Modify ```server.py``` with your ngrok authtoken, and the SSH port on your machine

    TUNNEL, PORT = "tcp", "YOUR_SSH_PORT"
    NGROK_AUTH_TOKEN = "PUT_YOUR_AUTH_TOKEN_HERE" # Make a free account and get this

> By default, your SSH port will be 22, please change it to something like 6969, [tutorial](https://www.interserver.net/tips/kb/change-ssh-port-ubuntu/)

***What you'll only have to do each time you want a connection***

On the Linux machine that you want to SSH into, run ```python3 server.py```, this script will launch the ngrok SSH tunnel, send the URL:PORT over MQTT, kill the MQTT connection, and keep the SSH tunnel.

And on the other machine, run ```python3 consumer.py```, this script will connect to the MQTT broker, read the last retained data (URL:PORT), save it to a file named ```addr_port_ngrok.txt```, then die.

Now using the data you just retrieved from HiveMQ (the broker in general), ```ssh [USER]@[URL] -p [PORT]```

## The WHAT'S NEXT?

Well, my robot is headless, and accessible online, and doesn't have WiFi, and I solved a problem. Otherwise, hopefully the ngrok free tear stays like this, I can see this being very helpful for hobbiests like me.