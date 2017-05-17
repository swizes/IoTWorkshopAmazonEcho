from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import time
import json
import os
from pyW215.pyW215 import SmartPlug


# These are my AWS IoT login and certificates
host = "a1o1z22t7l92tr.iot.us-east-1.amazonaws.com"
cert_path = "cert/"
rootCAPath = cert_path + "root-CA.crt"
certificatePath = cert_path + "RasPi.cert.pem"
privateKeyPath = cert_path + "RasPi.private.key"
shadowClient = "RasPi"

Power_Status = "ON"
print("Initial Power Status" + Power_Status)



def IoT_to_Raspberry_Change_Power(ShadowPayload):
    global Power_Status
    # Desired = POWER change
    checkPlug()
    sp = SmartPlug('192.168.99.115','225564')
    if ( ShadowPayload == "ON" and Power_Status == "OFF"): #Check if machine is indeed OFF
    	sp.state = 'ON'
        checkPlug()
        JSONPayload = '{ "state" : {'+\
                            '"reported": {'+\
                                '"Power": "' + Power_Status + '" '+\
                            '} '+\
                        '} '+\
                    '}'
        myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values

    elif ( ShadowPayload == "OFF" and Power_Status == "ON"): #Check if machine is indeed ON
        sp.state = 'OFF'
        checkPlug()
        JSONPayload = '{ "state" : {'+\
                            '"reported": {'+\
                                '"Power": "' + Power_Status + '" '+\
                            '}, '+\
                            '"desired": {'+\
                                '"Power": "' + Power_Status + '" '+\
                            '} '+\
                        '} '+\
                    '}'
        myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5) #Send the new status as REPORTED values


def checkPlug():
	global Power_Status
	sp = SmartPlug('192.168.99.115','225564')
    # Get values if available otherwise return N/A
    	print(sp.current_consumption)
    	print(sp.temperature)
    	print(sp.total_consumption)
    	if(sp.state == "ON"):
        	Power_Status = "ON"
    	else:
        	Power_Status = "OFF"


# Shadow callback for when a DELTA is received (this happens when Lamda does set a DESIRED value in IoT)
def IoTShadowCallback_Delta(payload, responseStatus, token):
    print(responseStatus)
    payloadDict = json.loads(payload)
    print("++DELTA++ version: " + str(payloadDict["version"]))

    # Desired = POWER change
    if ("Power" in payloadDict["state"]):
        print("Power: " + str(payloadDict["state"]["Power"]))
        a = str(payloadDict["state"]["Power"])
        IoT_to_Raspberry_Change_Power(a)

# Shadow callback GET for setting initial status
def IoTShadowCallback_Get(payload, responseStatus, token):
    print(responseStatus)
    payloadDict = json.loads(payload)
    print("++GET++ version: " + str(payloadDict["version"]))
    if ("Power" in payloadDict["state"]["desired"]):
        if(str(payloadDict["state"]["reported"]["Power"]).upper() <> str(payloadDict["state"]["desired"]["Power"]).upper()):
            print("Power: " + str(payloadDict["state"]["desired"]["Power"]))
            IoT_to_Raspberry_Change_Power(str(payloadDict["state"]["desired"]["Power"]))




# Shadow callback for updating the AWS IoT
def IoTShadowCallback_Update(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("++UPDATE++ request " + token + " timed out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("++UPDATE++ request with token: " + token + " accepted!")
        if ("desired" in payloadDict["state"]):
            print("Desired: " + str(payloadDict["state"]["desired"]))
        if ("reported" in payloadDict["state"]):
            print("Reported: " + str(payloadDict["state"]["reported"]))
    if responseStatus == "rejected":
        print("++UPDATE++ request " + token + " rejected!")






# Init AWSIoTMQTTShadowClient.
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(shadowClient)
myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
myDeviceShadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("RasPi", True)


time.sleep(3)

def jsonChecker():
    checkPlug()
    # All pins and defaults initialized, upload all system status parameters
    JSONPayload = '{ "state" : {'+\
                        '"reported": {'+\
                            '"Power": "' + Power_Status + '"'+\
                        '} '+\
                    '} '+\
                '}'
    myDeviceShadow.shadowUpdate(JSONPayload, IoTShadowCallback_Update, 5)
    time.sleep(3)




# Listen on deltas from the IoT Shadow
myDeviceShadow.shadowGet(IoTShadowCallback_Get, 5)
myDeviceShadow.shadowRegisterDeltaCallback(IoTShadowCallback_Delta)
loopCount = 0

if __name__ == '__main__':
    try:
        print 'RasPi started, Press Ctrl-C to quit.'
        checkPlug()
        print(Power_Status)
        while True:
		         #pass
                 jsonChecker()
                
            # Listen on deltas from the IoT Shadow
			#myDeviceShadow.shadowGet(IoTShadowCallback_Get, 5)
			#myDeviceShadow.shadowRegisterDeltaCallback(IoTShadowCallback_Delta)            
    finally:
        myAWSIoTMQTTShadowClient.shadowUnregisterDeltaCallback()
        myAWSIoTMQTTShadowClient.disconnect()
        print 'RasPi stopped.'
