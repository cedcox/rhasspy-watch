#!/usr/bin/env python3
# coding: utf8
"""
This tools connect to Rhasspy MQTT "nework" based on Hermes-MQTT.
It's a snips-watch like but, with some options (usefull for me).
You will be able to :
    - Watch in live and in human readable text all the messages
      on Rhasspy MQTT Topic
    - Record all messages in json file (or wav file)
    - Query between 2 date all messages received with the same
      display as in live session.

This tool will be very usefull if you want to analyze and optimize
your intents, you hardware audio (recording for example) etc.

The choice to use files instead of database to save the messages 
was made for reasons of simplicity and speed of writing the script. 
And secondly, because the tool is only started a few days,
long enough to analyze a malfunction. The count of generated 
files should not be a problem. 

However, I do not recommend using it for too long or the number 
of files may be very large.

"""
import os
import argparse
import json
from rhasspymqttclient import RhasspyMQTTClient 
from datetime import datetime
from logger import get_logger   
from dateutil import parser as dateparser

def on_message(client, userdata, msg, logTime):
    
    strLogTime = logTime.strftime(TIMELOGFORMAT)

    if "hermes/audioServer/" not in msg.topic: 
        msg.payload = json.loads(msg.payload.decode('utf8'))
        ## process the output of message
        if (not noStandardOut) or (outputFile != ""):
            ## translate message in wanted format
            message = mqtt.translate_message(msg.payload,msg.topic,strLogTime,outputFormatSelected)
            ## show and/or save the message
            mqtt.show_message(message,outputFile,noStandardOut)


def on_connect(client, userdata, flags, result_code):
    
    logger.info  ("Connected to MQTT server %s:%s ",host,port)
    logger.debug ("Subscribing to topics...")

    ## Subscribing to interesting topic
    mqtt.subscribe("hermes/asr/#")
    mqtt.subscribe("hermes/hotword/#")
    mqtt.subscribe("hermes/nlu/#")
    mqtt.subscribe("hermes/intent/#")
    mqtt.subscribe("hermes/tts/#")
    mqtt.subscribe("hermes/dialogueManager/#")
    mqtt.subscribe("hermes/audioServer/#")
        


def on_saved_wav (filename,siteId, flux, logTime):       

    strLogTime = logTime.strftime(TIMELOGFORMAT)

    text = "[Audio] {0} wav file saved for site {1}. name = {2}".format(flux, siteId, filename)
    
    logText = "[{0}] {1}".format(strLogTime,text)

    mqtt.show_message(logText,outputFile,noStandardOut)


############################################################
# START
############################################################

#######################
# VARIABLES
#######################

## Set log tool
logger = get_logger('rhasspy-watch', verbose=False)   
## date log format
TIMELOGFORMAT = '%Y-%m-%d %H:%M:%S'
## Get the current folder script
scriptFolder = os.path.dirname(os.path.abspath(__file__))

## Initialize default value   
recording = False    


logger.info(" ****************** Rhasspy-watch is started ***************************")


#######################
# ARGUMENT MANAGEMENT
#######################

parser = argparse.ArgumentParser()
parser.add_argument("--host",          help="host : MQTT hostname or IP",default="rhasspy-master")
parser.add_argument("--port",          help="port : MQTT server tcp port",default=1883)
parser.add_argument("--username",      help="username : authentication on MQTT",default="")
parser.add_argument("--password",      help="passwrd : authentication on MQTT",default="")
parser.add_argument("--tls",           help="tls : use TLS connection to MQTT broker", default=False)
parser.add_argument("--cacerts",       help="cacerts : CA path to verify the MQTT broker's TLS certificate", default=None)
parser.add_argument("--mode",          help="mqtt : (live) get logs from json files / mqtt_db : like mqtt but with MQTT message recording / search : For searching message in historic",default="mqtt")
parser.add_argument("--outputFormat",  help="human : return human text / raw : return payload as raw",default="human")
parser.add_argument("--datetime_start",help="if search mode, the start date for search. ex: 2020-05-26 23:30:00",default="2020-05-10 01:43:26")
parser.add_argument("--datetime_stop", help="if search mode, the stop date for search. ex: 2020-04-27 01:00:00",default="2020-05-10 01:50:00")
parser.add_argument("--outputFile",    help="file where output is saved",default='')
parser.add_argument("--jsonfolder",    help="folder where payloads are saved as json file",default=os.path.join(scriptFolder,'./archives'))
parser.add_argument("--noStandardOut", help="human view is NOT sent to standard output", default=False)
args = parser.parse_args()

## Set the json folder where json files are saved or read
jsonfolder = str(args.jsonfolder)
logger.info("Json folder : %s", jsonfolder)

## Create folder if not exist
if not os.path.exists(jsonfolder):
    os.makedirs(jsonfolder)

## Set to true if there is no standard output 
noStandardOut = args.noStandardOut
logger.info("No standard output : %s", str(noStandardOut))

## Set the output format. By default it's human view
outputFormatSelected = str(args.outputFormat)
logger.info("Output format : %s", outputFormatSelected)

## Set the log file if  a log file has to be generated
outputFile = str(args.outputFile)
logger.info("Output file : %s", outputFile)

## Set the mqtt server name
host = str(args.host)
logger.info("hostname : %s", host)

## Set the mqtt port
port = int(args.port)
logger.info("TCP port : %s", str(port))

## Set the username for authent
username = str(args.username)
logger.info("username : %s", username)

## Set the password for authent
password = str(args.password)

## Set to True if the connection to MQTT uses TLS.
tls = args.tls
logger.info("TLS : %s", tls)

## Set the CA path
cacerts = args.cacerts
logger.info("CA path : %s", cacerts)

## Create the custom MQTT object
mqtt = RhasspyMQTTClient(host, port, username, password, tls, cacerts, False, jsonfolder, logger )
mqtt.on_connect = on_connect
mqtt.on_message = on_message
mqtt.on_saved_wav = on_saved_wav

## If Live MQTT listening is required
if (args.mode == 'mqtt') or (args.mode == 'mqtt_db'):
    logger.info("Mode : Listen live MQTT topics")

    ## If mode = mqtt, listen MQTT only
    if (args.mode == 'mqtt'):
        logger.info("Record messages : NO")
        recording = False
    ## If mode = mqtt_db, listen MQTT AND save payload to json file
    elif (args.mode == 'mqtt_db'):
        logger.info("Record messages : YES")
        recording = True
        os.makedirs(jsonfolder, exist_ok=True) 

    ## Start to listen MQTT
    mqtt.recording = recording
    mqtt.connect()
    
elif (args.mode == 'search'):
    logger.info("Mode : Query on DB")
    recording = False
    
    logger.info("Start from : {0}".format(args.datetime_start) )
    logger.info("Stop at : {0}".format(args.datetime_stop) )
    datestart = dateparser.parse(args.datetime_start)
    datestop = dateparser.parse(args.datetime_stop)
    
    mqtt.search_message(datestart,datestop,"",jsonfolder,outputFormatSelected,outputFile)

logger.info(" ****************** Rhasspy-watch is stopped ***************************")
