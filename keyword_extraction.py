### according the intent to extract keyword
import os
import csv
import re
import pandas as pd

def load_csv(file_name):        ##### load data to extract
    
    file = file_name + '.csv'
    
    df = pd.read_csv(file)
    column_headers = list(df.columns.values)
    data = {}
    for column in column_headers:
        data[column] = list(df[column])
    return data


## types of keywords need to be extracted
staff = ['teacher','lecturer','tutor','who','staff']
location = ['classroom','lab','theater','where','location']
time = ['time','timetable','when']
outline = ['outline']
handbook = ['handbook']
related = ['relative','related','prerequisite','co-related','correlated','exclusion','corequisite','condition']
name = ['course name','title','name']
other = {'staff':staff,'location':location,'time':time,'outline':outline,'handbook':handbook,'related':related,'name':name}

def keyword_extraction(intent,sentence):
    
    sentence = sentence.lower().replace("+", "#")
    # put every keyword extracted into this dictionary
    output = {'intent':intent,'course':[],'stream_name':[],'staff':[],'location':[],'time':[],'outline':[],'handbook':[],'related':[],'name':[]}
    
    courses = load_csv('courses')
    steam_name = load_csv('Stream course recommendation')
    
    for i in list(steam_name.keys()):
        for j in steam_name[i]:
            patt=r'{}'.format(j.lower())
            pattern = re.compile(patt)
            result = pattern.findall(sentence)     # match the keyword of stream names we need
            if result != []:
                output[i].append(j)
    
    for i in list(courses.keys()):
        for j in courses[i]:
            patt=r'{}'.format(j.lower().replace("+", "#"))
            pattern = re.compile(patt)
            result = pattern.findall(sentence)
            if result != []:
                if i == 'course_name':
                    index = courses[i].index(j)
                    course_code = courses['course'][index]
                    if course_code not in output['course']:     # match the keyword of course codes we need
                        output['course'].append(course_code)
                else:
                    output[i].append(j)
    
    for i in list(other.keys()):
        for j in other[i]:
            patt=r'{}'.format(j.lower().replace("+", "#"))
            pattern = re.compile(patt)
            result = pattern.findall(sentence)             # match the keyword of other types we need
            if result != []:
                output[i].append(j)
    return output
