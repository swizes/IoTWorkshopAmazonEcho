from __future__ import print_function
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import datetime
import json

# These are my AWS IoT login and certificates
host = "a1o1z22t7l92tr.iot.us-east-1.amazonaws.com"
cert_path = "cert/"
rootCAPath = cert_path + "root-CA.crt"
certificatePath = cert_path + "RasPi.cert.pem"
privateKeyPath = cert_path + "RasPi.private.key"
shadowName = "RasPi"

myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(shadowName)
myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print(
        "on_session_started requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """

    print("on_launch requestId=" + launch_request['requestId'] + ", sessionId=" + session['sessionId'])

    # Dispatch to your skill's launch
    intent = launch_request
    return Welcome_response(intent, session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "Plug":
        return smartplug_resspone(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])

    # add cleanup logic here
    return Stop_response()


# Shadow callback for updating the AWS IoT
def IoTShadowCallback_Update(payload, responseStatus, token):
    print("IoT update response: " + responseStatus.upper())
    payloadDic = json.loads(payload)
    deviceStatusNew = str(payloadDic["state"]["reported"])
    
    reprompt_text = "Device turned " + deviceStatusNew
    speech_output = "Device turned " + deviceStatusNew
    card_title = "Response from RasPi"
    should_end_session = false
    
    session_attributes = create_attributes(deviceStatusNew)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        

# --------------- Functions that control the skill's behavior ------------------
def smartplug_resspone(intent, session):
    # Connect to AWS IoT Shadow
    myAWSIoTMQTTShadowClient.connect()
    myDeviceShadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(shadowName, True)
    

    # Set other defaults
    card_title = "Plug"
    should_end_session = False

    speech_output = "DUNNO"
    reprompt_text = "DUNNO"

    if 'slots' in intent:
        if 'status' in intent['slots']:
            if 'value' in intent['slots']['status']:
                deviceStatus = intent['slots']['status']['value'].upper()
                speech_output = "Turning device " + deviceStatus
                reprompt_text = "Turning device " + deviceStatus


    # Publish to AWS IoT Shadow
    if(deviceStatus == "ON"):
        myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\" "\
                                                "} "\
                                    "} "\
                    "}"
        myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
        
    elif(deviceStatus == "OFF"):
        myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"OFF\" "\
                                                "} "\
                                    "} "\
                    "}"
        myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
        
    
    
    
    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(deviceStatus)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Helpers that build all of the responses ----------------------

def create_attributes(deviceStatus):
    return {"DeviceStatus": deviceStatus.upper()}


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
