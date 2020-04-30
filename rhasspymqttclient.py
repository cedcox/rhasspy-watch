# coding: utf8

from paho.mqtt.client import Client
from paho.mqtt.client import MQTTMessage
import os
from datetime import datetime
import json
import wave
import io
import re
from termcolor import colored
import codecs


class RhasspyMQTTClient:

    def __init__(self, host="", port=1883, username="", password="", recording=False, jsonfolder="", logger=None):
        """The __init__ function of custom MQTT Class.
        Args:
            host (str)               : MQTT Server name or IP.
            port (int)               : MQTT server TCP port.
            logger (class:logging.Logger): Logger object for logging messages.
            username (str)(option)   : User name to connect MQTT server.
            password (str)(option)   : Password to connect MQTT server.
            recording (bool)          : save all messages as json file (and wave).
            jsonfolder (str)         : Folder where messages are saved
        """ 
        ## Properties
        self.host       = host
        self.port       = port
        self.username   = username
        self.password   = password
        self.recording   = recording
        self.jsonfolder = jsonfolder
        self.logger     = logger
        self.__dateFileFormat = '%Y%m%d%H%M%S%f'

        ## Dict who contains pair key/value by site
        ## Key is site name / Value is array of wave bytes received
        self.__audioFrames = {}
        self.__playBytes   = {}

        ## Paho Mqtt Client
        self.__mqtt = Client()
        self.__mqtt.message_callback_add("hermes/audioServer/#",self.on_audio)

        ## override some methods
        self.__mqtt.on_connect = self.on_cnx ### GRRRR
        self.__mqtt.on_message = self.on_msg



    def __saveJson(self,payload,topic,logTime):
        """Save each MQTT message (not audio) as a json file """
        
        self.logger.debug('enter in show_message method.')

        strFileTime = logTime.strftime(self.__dateFileFormat)

        ## Get payloada nd save topic info in json    
        payload.update({"topic":topic})

        ## Dump the payload to json file
        with open(os.path.join(self.jsonfolder,strFileTime + ".json"), 'w') as outfile:
            json.dump(payload, outfile)
  
        self.logger.debug("payload saved in %s.json file",strFileTime)



    def __saveWave(self,siteId,logTime,arrBytesWav,flux):
        """save all audio messages as wave files """

        self.logger.debug('enter in __saveWave private method.')

        strFileTime = logTime.strftime(self.__dateFileFormat)
 
        ## Generate the wave file name with name, siteId and flux
        wave_filename = os.path.join (self.jsonfolder,strFileTime + "_" + siteId + "_" + flux + ".wav")
        self.logger.debug("Saving array of waves in %s.wav ",strFileTime)

        ## open the wave file with write access
        output = wave.open(wave_filename,'wb') 
        
        ## set wave file parameters from first wave element in array
        with io.BytesIO(arrBytesWav[0]) as wav_buffer:       
            with wave.open(wav_buffer,'rb') as w:                    
                output.setparams(w.getparams())

        ## Extract each frames from all wave elements in arrBytesWav
        ## to add them to output wave file
        for wav in arrBytesWav :
            with io.BytesIO(wav) as wav_buffer:
                with wave.open(wav_buffer,'rb') as w:
                    output.writeframes(w.readframes(w.getnframes()))
        
        output.close()    

        self.logger.debug("%s.wav saved successfully ",strFileTime)

        self.on_saved_wav (strFileTime + ".wav", siteId, flux, logTime)



    def connect(self):
        """Connect to the MQTT broker defined in the configuration. """

        self.logger.debug('enter in show_message method.')

        if self.username != "":
            self.logger.debug('Setting username and password for MQTT broker.')
            self.__mqtt.username_pw_set(self.username, self.password)


        self.logger.info('Connecting to MQTT broker %s:%s...', str(self.host), str(self.port))
        
        self.__mqtt.connect(self.host, self.port)
        self.__mqtt.loop_forever()
 


    def translate_message(self,payload, topic, strLogTime, outputFormat):
        """ 2 possibilities (actually) for output text
            - In human readable text
            - In json text format with dump of payload

            This method returns text in desired format
        """

        self.logger.debug('enter in translate_message method.')

        if (outputFormat == "raw"):
            text = "{0}".format(payload)
            logText = "[{0}] {1} - {2}".format(strLogTime,topic, text)
        else:
            text = self.get_humanText(payload,topic)
            logText = "[{0}] {1}".format(strLogTime,text)

        return logText
        


    def show_message(self,text, outputFile, noStandardOut):
        """ this methods is used to manage the MQTT message display
            - noStandardOut : If true, nothing write to stdout
            - outputFile    : If not empty, all MQTT message will be
                              saved inside this file
        """
        self.logger.debug('enter in show_message method.')

        if not noStandardOut:
            print(text)
        
        if outputFile != "":
            with codecs.open(outputFile, 'a', encoding='utf8') as f:
                f.write(text+"\n")
                f.close()



    def get_humanText(self,payload, topic):
        """ This method translate Rhasspy/snips MQTT message as
            human readable text
            Maybe all topics are not processed. 
        """

        self.logger.debug('enter in get_humanText method.')
        self.logger.debug('Topic : {0}'.format(topic))


        ########################
        #       HOTWORD        #
        ########################
        if "hermes/hotword/toggleOn" in topic:
            text = colored("[hotword]",'magenta') + \
                " was asked to toggle itself 'on' on site {0}"\
                .format (colored(payload['siteId'],'white',attrs=['bold']))

        elif "hermes/hotword/toggleOff" in topic:
            text = colored("[hotword]",'magenta') + \
                " was asked to toggle itself 'off' on site {0}"\
                .format (colored(payload['siteId'],'white',attrs=['bold']))

        elif ("hermes/hotword/" in topic) and ("/detected" in topic):
            text = colored("[hotword]",'yellow') + \
                " detected on site {0}, for model {1}"\
                .format(colored(payload['siteId'],'white',attrs=['bold']),
                        payload['modelId'])  


        ########################
        #         ASR          #
        ########################
        elif "hermes/asr/stopListening" in topic:
            text = colored("[Asr]",'magenta') + \
                " was asked to stop listening on site {0}"\
                .format (colored(payload['siteId'],'white',attrs=['bold']))
            
        elif ("hermes/asr/startListening" in topic):
            text = colored("[Asr]",'magenta') + \
                " was asked to listen on site {0}"\
                .format (colored(payload['siteId'],'white',attrs=['bold']))

        elif ("hermes/dialogueManager/sessionStarted" in topic):
            text = colored("[Dialogue]",'yellow') \
                + " session with id {0} was started on site {1}."\
                .format(payload['sessionId'],
                        colored(payload['siteId'],'white',attrs=['bold']))

        elif ("hermes/asr/textCaptured" in topic):
            text = colored("[Asr]",'yellow') + \
                " captured text '{0}' in {1}s on site {2}"\
                .format(colored(payload['text'],'green',attrs=['bold']),
                        payload['seconds'],
                        colored(payload['siteId'],'white',attrs=['bold']))


        ########################
        #   DIALOGUE MANAGER   #
        ########################
        elif ("hermes/dialogueManager/sessionEnded" in topic):
            text = colored("[Dialogue]",'yellow') + \
                " session with id {0} was ended on site {1}. Reason: {2}"\
                .format(payload['sessionId'],
                        colored(payload['siteId'],'white',attrs=['bold']),
                        payload['termination']['reason'])

        elif ("hermes/dialogueManager/endSession" in topic):
            text = colored("[Dialogue]",'magenta') + \
                " was ask to end session with id {0} by saying '{1}'"\
                .format(payload['sessionId'],
                        (payload['text']))


        ########################
        #         NLU          #
        ########################
        elif ("hermes/nlu/query" in topic):
            text = colored("[Nlu]",'magenta') + \
                " was asked to parse input '{0}'"\
                .format(payload['input'])

        elif ("hermes/nlu/intentNotRecognized" in topic):
            text = colored("[Nlu]",'yellow') + \
                " Intent not recognized for {0}"\
                .format(colored(payload['input'],'red', attrs=['bold']))

        elif ("hermes/nlu/intentParsed" in topic):
            text = colored("[Nlu]",'yellow') + \
                " Detected intent {0} with confidence score {1} for input '{2}"\
                .format(colored(payload["intent"]["intentName"],'green', attrs=['bold']),
                        payload["intent"]["confidenceScore"],
                        payload['input'])


        ########################
        #       INTENT         #
        ########################
        elif ("hermes/intent/" in topic):
            text = colored("[Nlu]",'yellow') + \
                " Intent {0} with confidence score {1} on site {2} "\
                .format(colored(payload["intent"]["intentName"],'green', attrs=['bold']),
                        payload["intent"]["confidenceScore"],
                        colored(payload['siteId'],'white',attrs=['bold']))
                    
            if len(payload['slots']) > 0:
                text = text + "\n           with slots : "
                for slot in payload['slots']:
                    text = text + "\n               {0} => {1} (confidenceScore={2})"\
                        .format(colored(slot['slotName'],'cyan', attrs=['bold']),
                                slot['value']['value'],
                                slot['confidenceScore'])    


        ########################
        #         TTS          #
        ########################
        elif ("hermes/tts/say" == topic):
            text = colored("[Tts]",'yellow') + \
                " was asked to say '{0}' in {1} on site {2}".\
                format(colored(payload['text'],'green', attrs=['bold']),
                    payload['lang'],
                    colored(payload['siteId'],'white',attrs=['bold']))
        
        elif ("hermes/tts/sayFinished" in topic):
            text = colored("[Tts]",'cyan') + \
                " finished speaking with id '{0}'"\
                .format(payload['sessionId'])


        ########################
        #    AUDIO SERVER      #
        ########################
        elif ("hermes/audioServer" in topic):
            text = colored("[audioServer]",'cyan') + \
                " audio on topic {0}".format(topic)


        ########################
        #       UNKNOWN        #
        ########################
        else:
            self.logger.warning('Unknow topic : {0}'.format(topic))
            text = colored("[UNKNOWN]",'red') + \
                " message on topic {0}".format(topic)
        
        return text 


    
    def search_message(self, datestart,datestop,siteId,jsonfolder,searchoutputFormat,outputFile):
        """ This method allow to query all MQTT messages saved as file """

        self.logger.debug('enter in search_message method.')

        ## Get list of all json files sorted by name (so by datetime)
        allJsonFiles = os.listdir(jsonfolder)
        allJsonFiles.sort()
        
        ## For each file, check if it's between the start and stop search date
        for filename in allJsonFiles:
            
            ## Get extension and name of file
            filenameWithoutExt, extension = (os.path.basename(filename)).split(".")

            self.logger.debug('filename %s - ext %s',filenameWithoutExt,extension)

            if extension == "wav":
                """ If extension is .wav, so in name, there are :
                    myDate = date time when the wav was saved
                    siteId = The site of Rhasspy/snips
                    flux   = if it's input or output wave file
                        input  : play on the siteId
                        output : record from the siteId

                    Ex wave filename : 20200429195055646804_bureau_play.wav
                """

                ## Get date, siteId, flux
                strDate, siteId, flux = filenameWithoutExt.split("_")
                myDate = datetime.strptime(strDate,self.__dateFileFormat)

                
                ## We check if file date is between start and stop search date 
                if datestart <= myDate <= datestop:               
                    self.logger.debug('WAV : strDate : %s - siteId : %s - flux : %s',strDate,siteId, flux)

                    ## If yes, call the on_saved_wav
                    self.on_saved_wav (filename, siteId, flux, myDate)
                
            elif extension == "json":                
                ## Get date
                strDate = filenameWithoutExt.split("_")[0]
                myDate = datetime.strptime(strDate,self.__dateFileFormat)

                ## As script knows the format, it can retrieve the date as datetime type
                myDate = datetime.strptime(filenameWithoutExt,self.__dateFileFormat)
                
                ## We check if file date is between start and stop date search
                if datestart <= myDate <= datestop:
                    
                    ## The file is concerned by search. Script open it and load json
                    with open(os.path.join (jsonfolder,filename)) as json_file:
                        payload = json.load(json_file)

                    ## Remove the 'topic' json element imported when json file was saved
                    ## the 'topic' element is added to file only to retieve information
                    topic = bytes(payload['topic'],'utf-8')
                    payload.pop('topic', None)
                    
                    ## Create a paho MQTT message 
                    myMQTTmessage = MQTTMessage(mid=0,topic=topic)
                    myMQTTmessage.payload = json.dumps(payload).encode('utf-8')

                    ## call on_message method and pass the MQTT message
                    self.on_message(None, None, myMQTTmessage, myDate)



    def on_audio (self, client, userdata, msg):
        """ Specific method to intercept audio MQTT message and save data
        in a array of bytearray.
        The entire array will be dump in a wav file on specific MQTT message """
        self.logger.debug('enter in on_audio method. (read audio stream)')

        currentTime = datetime.now()
       
        if self.recording: 
            siteId = ((msg.topic).split("/"))[2]
            flux = ((msg.topic).split("/"))[3]

            ## If it's record stream
            if flux == "audioFrame":
                if siteId not in self.__audioFrames:
                    self.__audioFrames[siteId] = []
                
                ## Add this piece of wave in an array of bytes
                (self.__audioFrames[siteId]).append(bytearray(msg.payload))
            
            ## If it's a play stream
            if flux == "playBytesStreaming":
                if siteId not in self.__playBytes:
                    self.__playBytes[siteId] = []
                
                (self.__playBytes[siteId]).append(bytearray(msg.payload))
            
            ## when topic contains "playBytes" or "streamFinished", it means
            ## play stream has stopped on rhasspy. So the wav file can be saved. 
            ## Use <IS_LAST_CHUNK> instead ?
            if (flux == "playBytes") or (flux == "streamFinished"):
                self.logger.debug("fin streaming on site %s",siteId)
                toto = len(self.__playBytes[siteId]) 
                self.logger.debug("count of item in array %s",str(toto))
                self.__saveWave(siteId,currentTime,self.__playBytes[siteId],'play')
                self.__playBytes[siteId] = []


           
    def on_msg(self, client, userdata, msg):
        """The on_message callback of paho MQTT client is intercepted by this on_msg method 
        before the propagation of MQTT message.
        Here, we can :
            - Save payload to json if porperty recording is True
            - Save output wave file when specific message is received
            - Save input wave file when specific message is received
            - propagate the MQTT message to on_message method of our custom MQTT class

        """
        self.logger.debug('enter in on_msg method.')

        currentTime = datetime.now()

        ## If MQTT message has to be saved in file
        if self.recording: 
            
            ## If message does not come from audioServer
            ## the message is saved as json file
            if "hermes/audioServer/" not in msg.topic: 
                payload = json.loads(msg.payload.decode('utf8'))
                self.__saveJson(payload,msg.topic,currentTime)

            ## If "textCaptured" is in topic, it means ASR stop
            ## to record from Rhasspy. So the wav file can be saved.
            if "hermes/asr/textCaptured" in msg.topic:
                self.__saveWave(payload['siteId'],currentTime,self.__audioFrames[payload['siteId']],'record')
                self.__audioFrames[payload['siteId']] = []
            
        
        ## Propagate the message MQTT
        self.on_message(client, userdata, msg,currentTime)


    
    ## Not good enough in python to avoid this :/
    def on_cnx (self, client, userdata, flags, result_code):
        self.on_connect(client=client, userdata=userdata, flags=flags, result_code=result_code)


    def subscribe (self,topic):
        """Method used to subscribe to private MQTT object topic """
        self.__mqtt.subscribe(topic)


    def on_message(self,client, userdata, msg, logTime):
        """Event method """


    def on_connect(self,client, userdata, flags, result_code):
        """Event method """
 

    def on_saved_wav (self,filename ,siteId, flux, logTime):
        """Event method """
  

