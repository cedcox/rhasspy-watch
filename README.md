# rhasspy-watch

Rhasspy-watch is a tool for dynamic display of Rhasspy MQTT messages with recording and query functionalities.

Text messages are saved in json format and audio streaming are saved in .wav format. So you can listen again to what was recorded by the microphone and sent to the ASR ! 

![Alt Text](https://nsm09.casimages.com/img/2020/04/30//20043002134924155416769151.png)

## Installation
To work, the script needs :
* colorlog
* paho-mqtt
* python-dateutil
* termcolor

Quick and dirty :
```
pip3 install -r requirements.txt
```

Get repository :
```
git clone https://github.com/cedcox/rhasspy-watch
cd rhasspy-watch
```

## Run the script
```
python3 ./rhasspy-watch.py
```

## Parameters
* **--host**     : MQTT hostname or IP" (default="rhasspy-master")
* **--port**     : MQTT server tcp port" (default=1883)
* **--username** : user for authentication,default=''
* **--password** : password for authentication,default=''
* **--tls**      : use TLS connection to MQTT broker,default=False
* **--cacerts**  : CA path to verify the MQTT broker's TLS certificate,default=None
* **--mode**     :
  * 'mqtt'    : Just live display (default)
  * 'mqtt_db' : Like 'mqtt' but MQTT messages are saved
  * 'search'  : Use to get saved messages between 2 datetimes
* **--outpoutFormat** : 
  * 'human' : Display messages in human readable text (default)
  * 'raw'   : Display messages in json format
* **--datetime_start** : the start date for search. ex: 2020-04-26 23:30:00
* **--datetime_stop**  : the stop date for search. ex: 2020-04-26 23:30:00
* **--outputFile**     : Save the live display in log file. If empty or not specified, no file is generated
* **--jsonfolder**     : folder where payloads are saved as json file. (default 'archives' in script folder)
* **--noStandardOutput** : Messages are not displayed on stdout

## Examples
#### Just display live messages in human readable text
```
python3 ./rhasspy-watch.py --host rhasspy-master.local 
```

#### Display live messages in human readable text and record messages
```
python3 ./rhasspy-watch.py --host rhasspy-master.local  --mode mqtt_db
```

#### Display recorded messages in json format between 2 hours
```
python3 ./rhasspy-watch.py --mode search --datetime_start "2020-04-25 15h30" --datetime_stop "2020-04-25 17h30" --outputFormat "raw"
```

## Infos
I did not test authentication for MQTT :) I added it just in case someone wants to try

it's just a tool quickly developped to answer to a need, not a real soft

French article about tool : https://www.coxprod.org/domotique/rhasspy-watch/

## Warning
The choice to use files instead of database to save the messages was made for reasons of simplicity and speed of writing the script. 
And secondly, because the tool is only started a few days, long enough to analyze a malfunction. The count of generated files should not be a problem. 

However, I do not recommend using it for too long because the number of files may be very large.

## Thanks
Thanks to **Koen Vervloesem** - [*hermes-audio-server*](https://github.com/koenvervloesem/hermes-audio-server)
   I helped myself with what he had done on this project
   
## License

This project is licensed under the GNU License - see the [LICENSE](LICENSE) file for details
