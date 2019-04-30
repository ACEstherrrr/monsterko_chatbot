import os
import re
import string
import pickle
import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn.externals import joblib
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras import backend as K

MAX_SEQUENCE_LENGTH = 50


# In[21]:

def preprocessing(text):
    text = text.translate(string.punctuation)
    text = text.lower()
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace('requirements','requirement')
    text = text.replace('recommendations', 'recommendation')
    text = text.replace('streams', 'stream')
    text = text.replace('specialisations','specialisation')
    text = text.replace("what's", 'what is')
    text = text.replace("you're", 'you are')
    text = text.replace("i'm",'i am')
    text = text.replace("where's", 'where is')
    text = text.replace("who's", 'who is')
    text = text.strip()
    return text


# In[22]:

def intent_classification(test_text):

    #load pickle file for tokenizer
    label_dict = pickle.load(open("label_encoder.pkl", "rb"))
    
    #clean customer input
    clean_test_text = preprocessing(test_text)
    
    #tokenize cusotmer input
    tokenizer = pickle.load(open('tokenizer.pkl','rb'))
    test_sequences = tokenizer.texts_to_sequences([clean_test_text])
    test_input = pad_sequences(test_sequences, maxlen = MAX_SEQUENCE_LENGTH)
    
    #load pickle file for model
    model = pickle.load(open('model.pkl','rb'))
    
    #using intent classification model to classfy user input
    test_predictions_probas = model.predict([test_input])
    max_prob = np.max(test_predictions_probas)
    test_predictions = test_predictions_probas.argmax(axis=-1)
    
    #find intent
    intent = None
    for index, item in label_dict.items():
        if item == test_predictions[0]:
            intent = index
            break
    K.clear_session()
    return intent,max_prob
            
    

'''
# In[8]:

intent = intent_classification('Who is teaching COMP9321 this semester?')
print(intent)


# In[ ]:
'''


