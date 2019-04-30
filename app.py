
## the server connected with Facebook


### the library import
import random
import os
from flask import Flask,request
from pymessenger.bot import Bot
import boto3
from textblob import TextBlob

import IntentClassification as intent_classify
import keyword_extraction as keyword_extract
import retrieve_data as retrieve
import feedback

import time
import ssl

#the verify token for facebook webhook
facebook_verify = 'haha'
# the access token for facebook flask request
access_token = 'EAAD1PpqbNz0BAE1C2ZAkvzg2eotZA66Ad3rQZAFKyX2WfOxNZBUQhLtFpIOlNuUyJwRzHLt5euP07q3bZAb1wKjCO5S5xSpqzp7lxVnq9XfLdqZCAT7KTmXsZC6NTW2l9d7VZBuIXAuFsxEQZCayYtn3bIHWCpnO0vIFom6uCZC2v5hgZDZD' #os.environ['access_token']    #the access token
# create a class names server using functions of Bot
server = Bot(access_token)


# store the key info by user id
global store
store = {}



app = Flask(__name__)


#check the facebook verification token if matches the token by developer sent
@app.route('/',methods = ['GET'])

def verify_facebook():
    verify_token = request.args.get("hub.verify_token")
    if verify_token == facebook_verify:
        #request.args.get("hub.challenge")
        return request.args.get("hub.challenge")
    return 'Can not match Facebook verification!'

button = [{'type':'postback', 'title': 'It helps me!','payload': 'Yes'}, {'type':'postback', 'title': 'It does no help!','payload': 'No'}]

continue_button = [{'type':'postback', 'title': 'I wanna continue.','payload': '1'}, {'type':'postback', 'title': 'Stop here.','payload': '0'}]



intent_bound = 0.8    ## least accuracy rate for recognizing wrong intent classification 

#processing the message sent by user and return response searched by Chatbot
@app.route('/',methods = ['POST'])

def recieve_message():
    global store
    user_input = request.get_json()
    
    if user_input.get('entry'):
          event = user_input['entry'][0]
          if event.get('messaging'):
            message = event['messaging'][0]
            # server get text type message
            if message.get('message'):
                
                text = message['message'].get('text')   #user input on Facebook Messenger
                user_ID = message['sender']['id']     #Facebook Messenger ID for user so we know where to send response back to
                
                sent_time = time.time()   # current time
                
                if user_ID not in store.keys():    #new user, create a new record for this ID
                    store[user_ID] = {'input': '', 're_intent':'', 'keyword':{}, 're_ask': 0, 'time': sent_time, 'intent_acc':0.0,'response':''}
                else:           #old user, update record of this ID
                    break_time = sent_time - store[user_ID]['time']
                    if break_time > 120:  # longer than 2 mins, renew the record
                        store[user_ID] = {'input': '', 're_intent':'','keyword':{}, 're_ask': 0, 'time': sent_time, 'intent_acc':0.0,'response':''}
                    else:
                        store[user_ID]['time'] = sent_time
                
                if store[user_ID]['re_ask'] == 0 or store[user_ID]['re_ask'] > 1:   ## the server do not need re-ask or server had re-asked more than twice
                    store[user_ID]['re_ask'] = 0
                    new_text = intent_classify.preprocessing(text)     # preprocessing the user input
                    intent,intent_acc = intent_classify.intent_classification(new_text)     # get intent and the accuracy
                    store[user_ID]['intent_acc'] = intent_acc
                    
                    # Corresponding actions for intents of 'Greetings','Goodbye','Name'
                    if intent == 'Greetings':
                        greet_response = ['Hi, I am here to help you!', 'Hi nice to meet u!', 'Hey there!','Yo!','Hey, boo!']
                        response = random.choice(greet_response)   #random chooser one response
                        if store[user_ID]['intent_acc'] <= intent_bound:     # intent accuracy lower than the bound
                            # store response and intent into record for further continue sending
                            store[user_ID]['response'] = response
                            store[user_ID]['re_intent'] = intent
                            # send ask-continue button type message to user
                            res = 'We think your input may lead to wrong response, do you want continue?'
                            server.send_button_message(user_ID, res, continue_button)
                            return "Message Processed"
                        else:  # send the reponse back to user
                            server.send_text_message(user_ID,response)
                            return "Message Processed"
                    
                    elif intent == 'Goodbye':
                        bye_response = ['See you soon!','Thanks!','ByeBye!','Thank you for choosing us!','I will miss you!']
                        response = random.choice(bye_response)
                        if store[user_ID]['intent_acc'] <= intent_bound:
                            store[user_ID]['response'] = response
                            store[user_ID]['re_intent'] = intent
                            res = 'We think your input may lead to wrong response, do you want continue?'
                            server.send_button_message(user_ID, res, continue_button)
                            return "Message Processed"
                        else:
                            server.send_text_message(user_ID,response)
                            return "Message Processed"
                    
                    elif intent == 'Name':
                        name_response = ['My name is KOBO. :）','Please call me KOBO ~','I am KOBO ^^']
                        response = random.choice(name_response)
                        if store[user_ID]['intent_acc'] <= intent_bound:
                            store[user_ID]['response'] = response
                            store[user_ID]['re_intent'] = intent
                            res = 'We think your input may lead to wrong response, do you want continue?'
                            server.send_button_message(user_ID, res, continue_button)
                            return "Message Processed"
                        else:
                            server.send_text_message(user_ID,response)
                            return "Message Processed"
                    
                    store[user_ID]['input'] = text    #record the input of user
                    
                else:       #server is re-asking for course code or stream name
                    print(store[user_ID])
                    intent = store[user_ID]['re_intent']       #get recorded intent
                    text = store[user_ID]['input'] + ' ' + text    # combine the new input with recorded input for further actions 
                    print('new reask text is '+ text)
                
                keyword = keyword_extract.keyword_extraction(intent,text)  # extract keyword fron input
                print('keyword is ' + str(keyword))
                
                response = retrieve.retrieval_func(keyword)  # get response from data-retrieving
                print('data retrieve is '+response)
                
                if response == 'Please provide valid courses code.':      # can not retrieve without valid course codes
                    # search record for valid course code
                    if store[user_ID]['keyword']!={}:
                        print(store[user_ID])
                        if store[user_ID]['keyword']['course'] != []:      # recorded valid course code
                            store[user_ID]['keyword']['intent'] = intent
                            print(store[user_ID]['keyword'])
                            keyword['course'] = store[user_ID]['keyword']['course']   #conbine keyword with recorded course codes
                            response = retrieve.retrieval_func(keyword)               # re-data_retrieving for response with new keyword
                            if store[user_ID]['intent_acc'] <= intent_bound:          # intent accuracy lower than the bound
                                store[user_ID]['response'] = response                 # recorded the response for further sending
                                # send ask-continue button type message to user
                                res = 'We think your input may lead to wrong response, do you want continue?'
                                server.send_button_message(user_ID, res, continue_button)     
                            else:
                                # send response back to user
                                res = response 
                                server.send_button_message(user_ID,res,button)
                        else:                                # no valid course code in recorded keyword
                            store[user_ID]['re_ask'] += 1    # add one more time to re-ask label of record,server need re-ask
                            # record intent and keyword
                            store[user_ID]['re_intent'] = intent
                            store[user_ID]['keyword'] = keyword
                            if store[user_ID]['intent_acc'] <= intent_bound:
                                store[user_ID]['response'] = response
                                res = 'We think your input may lead to wrong response, do you want continue?'
                                server.send_button_message(user_ID, res, continue_button)
                            else:
                                res = response 
                                server.send_text_message(user_ID,res)
                    else:                                  # not record keyword
                        store[user_ID]['re_ask'] += 1      # add one more time to re-ask label of record
                        # record intent and keyword
                        store[user_ID]['re_intent'] = intent
                        store[user_ID]['keyword'] = keyword
                        if store[user_ID]['intent_acc'] <= intent_bound:
                            store[user_ID]['response'] = response
                            res = 'We think your input may lead to wrong response, do you want continue?'
                            server.send_button_message(user_ID, res, continue_button)
                        else:
                            res = response 
                            server.send_text_message(user_ID,res)
                
                elif response[(len(response)-43):] == 'Do you want query one specific stream name?':     # can not retrieve without an valid stream name
                    # search record for valid stream name
                    if store[user_ID]['keyword']!={}:
                        print(store[user_ID])
                        if store[user_ID]['keyword']['stream_name'] != []:        # recorded valid stream name
                            store[user_ID]['keyword']['intent'] = intent
                            print(store[user_ID]['keyword'])
                            keyword['stream_name'] = store[user_ID]['keyword']['stream_name']    #conbine keyword with recorded course codes
                            response = retrieve.retrieval_func(keyword)                          # re-data_retrieving for response with new keyword
                            if store[user_ID]['intent_acc'] <= intent_bound:                     # intent accuracy lower than the bound
                                store[user_ID]['response'] = response                            # recorded the response for further sending
                                # send ask-continue button type message to user
                                res = 'We think your input may lead to wrong response, do you want continue?'
                                server.send_button_message(user_ID, res, continue_button)
                            else:
                                # send response back to user
                                res = response 
                                server.send_button_message(user_ID,res,button)
                        else:                                              # no valid stream name in recorded keyword
                            store[user_ID]['re_ask'] += 1                  # add one more time to re-ask label of record, server need re-ask
                            # record intent and keyword
                            store[user_ID]['re_intent'] = intent
                            store[user_ID]['keyword'] = keyword
                            if store[user_ID]['intent_acc'] <= intent_bound:
                                store[user_ID]['response'] = response
                                res = 'We think your input may lead to wrong response, do you want continue?'
                                server.send_button_message(user_ID, res, continue_button)
                            else:
                                res = response 
                                server.send_text_message(user_ID,res)
                    else:                                                # not record keyword
                        store[user_ID]['re_ask'] += 1                    # add one more time to re-ask label of record,server need re-ask
                        store[user_ID]['re_intent'] = intent
                        store[user_ID]['keyword'] = keyword
                        if store[user_ID]['intent_acc'] <= intent_bound:
                            store[user_ID]['response'] = response
                            res = 'We think your input may lead to wrong response, do you want continue?'
                            server.send_button_message(user_ID, res, continue_button)
                        else:
                            res = response #+ ' ' + str(store[user_ID]['re_ask'])
                            server.send_text_message(user_ID,res)
                
                else:            # getting an response from retrieving data
                    store[user_ID]['re_ask'] = 0          # set re-ask label as 0 in record, server did not re-ask 
                    store[user_ID]['keyword'] = keyword   # record the keyword
                    store[user_ID]['re_intent'] = ''
                    if store[user_ID]['intent_acc'] <= intent_bound:      # intent accuracy lower than the bound
                        store[user_ID]['response'] = response             # recorded the response for further sending
                        # send ask-continue button type message to user
                        res = 'We think your input may lead to wrong response, do you want continue?'
                        server.send_button_message(user_ID, res, continue_button)
                    else:
                        # send response back to user
                        res = response
                        server.send_button_message(user_ID,res,button)
                    
                
            # server get message from button  
            elif message.get('postback'):
                user_ID = message['sender']['id']           #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message["recipient"]["id"]
                    
                payload = message["postback"]["payload"]    # get button text
                if payload == 'Yes':                        # user feedback that response is helpful
                    res = 'It is good to hear!'
                    #  upload user input into AWS dataset for further model training
                    feedback.feedback(user_ID, store[user_ID]['input'], store[user_ID]['keyword']['intent'])
                    server.send_text_message(user_ID,res)
                elif payload == 'No':                      # user feedback that response is helpless
                    res = 'We will improve soon!'
                    sent_time = time.time()
                    # renew the record of user for new query
                    store[user_ID] = {'input': '', 're_intent':'', 'keyword':{}, 're_ask': 0, 'time': sent_time, 'intent_acc':0.0,'response':''}
                    server.send_text_message(user_ID,res)
                elif payload == '1':                       # user feedback that wanna continue
                    res = store[user_ID]['response']
                    if store[user_ID]['re_ask'] == False:   # server not re-ask
                        # send stored response back to user
                        if store[user_ID]['re_intent'] in ['Greetings','Goodbye','name']:   # send text type message for 3 types of intent 
                            server.send_text_message(user_ID,res)
                        else:                                              # send button type message for other kinds of intent
                            server.send_button_message(user_ID,res,button)
                    else:    #server is re-asking
                        # send stored response back to user
                        server.send_text_message(user_ID,res)
                elif payload == '0':                             # user feedback that wanna not continue
                    res = 'Please reinput with more details.'
                    sent_time = time.time()
                    # renew the record of user for new query
                    store[user_ID] = {'input': '', 're_intent':'', 'keyword':{}, 're_ask': 0, 'time': sent_time, 'intent_acc':0.0,'response':''}
                    server.send_text_message(user_ID,res)
                                 
    return "Message Processed"
    

## setting up files for AWS EC2
key_file = "/etc/letsencrypt/live/www.monsterko.ml/privkey.pem"
cert_file = "/etc/letsencrypt/live/www.monsterko.ml/fullchain.pem"
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(certfile = cert_file, keyfile = key_file)

if __name__ == '__main__':
    app.run(ssl_context = context, host = '0.0.0.0', port = '55555',threaded = True,debug = True)



