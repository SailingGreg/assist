#
#
#

import time
#import math
import logging
import paho.mqtt.client as mqtt
from ruuvi_decoders import Df5Decoder

decoder = Df5Decoder()

# warm or cooling modes
WARM = 1
COOL = 2
# the Ruuvi tags
outerTag = "ec991753cb34"
innerTag = "d202c44b291d"
tags = [innerTag, outerTag]
tagData = {innerTag: {"mac": innerTag, "temp": 20.0, "humidity": 0.0, \
        "pressure": 0.0, "battery": 0},
        outerTag: {"mac": outerTag, "temp": 15.0, "humidity": 0.0, \
                "pressure": 0.0, "battery": 0}}

loc = "home/pi/assist/"
print (loc + 'heatpump.log')

# adding filemode='w' will truncate the log on each retstart
logging.basicConfig(filename='/home/pi/assist/heatpump.log', \
        format='%(asctime)s %(message)s', \
        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
#logging.basicConfig(format='%(asctime)s %(message)s')

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    sub = client.subscribe("ruuvi/#")
    print ("sub: ", sub)

def on_message(client, userdata, msg):
    #print (msg.payload, str(msg.payload.decode("utf-8")), msg.topic)
    #print (msg.payload.decode())
    #print("message received  ", str(msg.payload.decode("utf-8")),
    #                    "topic", msg.topic, "retained ", msg.retain)
    # store the message
    #if msg.payload.decode() == "Hello world!":
    '''
    msg.topic will be ruuvi/C3:FC:59:E9:91:36/{MAC}
    for example ruuvi/C3:FC:59:E9:91:36/EC:99:17:53:CB:34
    '''
    if (msg.topic != "ruuvi/C3:FC:59:E9:91:36/gw_status"):
        # convert to string
        #print("msg.topic: - ", msg.topic)
        rmsg = str(msg.payload.decode("utf-8"))
        #print("rmsg: ", rmsg)

        clean_data = rmsg.split("FF9904")[1]
        data = decoder.decode_data(clean_data)
        #print(data)
        # revord temp, humidity and battery
        tagData[data['mac']]['temp'] = data['temperature']
        tagData[data['mac']]['humidity'] = data['humidity']
        tagData[data['mac']]['pressure'] = data['pressure']
        tagData[data['mac']]['battery'] = data['battery']
        #print(tagData[data['mac']])
    #else:
        # this will just be the gw_status message
        #print("msg.topic: ", msg.topic)


client = mqtt.Client()
#client = mqtt.Client("myclient")
client.connect("localhost", 1883, 60)

client.on_connect = on_connect
client.on_message = on_message

client.loop_start() # start a handler for messages

print ("sleeping 15 to initialise values")
time.sleep(15)
SLEEP = 5 * 60 # 5 minutes
mode = WARM
prevHPTemp = 20.0
hpTemp = 20 # the default for room heating
while True:
    for tag in tags:
        print(tagData[tag])
    '''
    # main processing loop - calc moving average?
    we have three conditions - cool and heat, hot and cool
    If inside < 20.0 then heat
    if inside > 21.0 and outside > 18.0 then cool
    if inside > 22.00 and outside > 20.0 then really cool!
    in the case of the later it diff above 20 from 18
    '''
    if (tagData[innerTag]['temp'] < 20.0 and
            tagData[outerTag]['temp'] < 16.0):
        print ("Need to heat ...")
        hpTemp = 20 # this is auto
        if (mode != WARM):
            logging.info(f"Need to warm {tagData[innerTag]['temp']} {hpTemp}")
            # set mode to warm and flag
            #res = assistant.assist('change heat pump in family room to heat mode')[0])
            mode = WARM
    if (tagData[innerTag]['temp'] >= 21.0 and \
            tagData[outerTag]['temp'] > 18.0):
        hpTemp = 18
        if (mode != COOL):
            logging.info(f"Need to cool {tagData[innerTag]['temp']} {hpTemp}")
            # set mode to cool and flag
            #res = assistant.assist('change heat pump in family room to cool mode')[0])
            mode = COOL
        print(f"it's hot - go to cool mode - {hpTemp}")
    if (tagData[innerTag]['temp'] >= 22.0 and \
            tagData[outerTag]['temp'] > 20.0):
        # calc offset as integer
        hpTemp = round(18 - (tagData[innerTag]['temp'] - 20), 0)
        if (hpTemp != prevHPTemp): # then change up/down
            logging.info(f"Need to accelerate {tagData[innerTag]['temp']} {hpTemp}")
            prevHPTemp = hpTemp
            # change the cool temp
            #res = assistant.assist(f'change the temperature of heat pump in family room to {hpTemp}')[0])
        print(f"it's really hot - go to exta cool - {hpTemp}")

    logging.info(f"Current temps inside/outside/set {tagData[innerTag]['temp']} {tagData[outerTag]['temp']} {hpTemp}")


    print ("sleeping: ", SLEEP)
    time.sleep(SLEEP)
# end of file
