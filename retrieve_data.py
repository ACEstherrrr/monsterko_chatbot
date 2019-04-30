import boto3
import pandas as pd
import copy
import datetime
from boto3.dynamodb.conditions import *

# connect with AWS get dataset
def get_table():
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Monster_DB')
    return table

# cut outline text with over length 
def cut_str(s):
    a = s.find('.')
    b = s[a+1:].find('.')
    new_s = s[:a]+s[10:a+b+2] + ' ...'
    return new_s

def split_space(s):
    l = list(s.split(' '))
    len = 50
    new_s = ' '.join(l[:len])
    return new_s

#### graduate requirements
def graduate_req(epic1_return):
    ADK_nb = 0
    total_units = 0
    nb_projects = 0

    code_list = epic1_return['course']
    
    if code_list == []:    # can not retrieve without valid course code
        return 'Please provide valid courses code.'
    
    table = get_table()
    for course in code_list:
        items = table.scan(FilterExpression = Attr('Course').eq(course) & Attr('Function').eq('Courses'))['Items'][0]
        if items['is ADK'] == 'Yes':
            ADK_nb += 1
        if items['is project'] == 'Yes':
            nb_projects += 1
        total_units += int(items['units'])
    
    info = ''

    if ADK_nb < 6:
        info += 'No, you need ' + str(6-ADK_nb)+' more 6-units ADK courses to meet the graduation requirement.\n'
        
    if total_units < 96:
        info += 'You also need to get '+str(96 - total_units)+' more units to meet the graduate requirement.\n'
        
    if nb_projects < 1:
        info += 'You also must enroll at least 1 project.\n'
        
    if info == '':
        return 'Yes, congradulations!'
    else:
        return info

### print fixed format infor    
def print_term_info(label,term):
    info = ''
    if label == 'timetable':
        for t in term.keys():
            if term[t] != {}:
                info += 'Term '+ t + ' has '
                for i in term[t].keys():
                    info += ' , '.join(term[t][i]) + ' in '+ i + ','
                info = info[:len(info)-1]
                info += '\n'
            else:
                info += 'Term '+ t + ' does not have this course.\n'
    else:
        for t in term.keys():
            if term[t] != 'N/a':
                info += term[t] + ' in Term ' + t + '\n'
            else:
                info += 'Term '+ t + ' does not have this course.\n'
    return info


#### find basic course information
def basic_courses_info(epic1_return):
    code_list = epic1_return['course']
    if code_list == []:     # can not retrieve without valid course code 
        return 'Please provide valid courses code.'
    
    info = ''
    handbook = epic1_return['handbook']
    timetable = epic1_return['time']
    outline = epic1_return['outline']
    staff = epic1_return['staff']     
    location = epic1_return['location']
    related = epic1_return['related']
    name = epic1_return['name']
    
    
    table = get_table()
    for course in code_list:
        info += '[' + course + ']\n'
        items = table.scan(FilterExpression = Attr('Course').eq(course) & Attr('Function').eq('Courses'))['Items'][0]
        # if user not specify any kind of information,just return outline context
        if handbook == [] and outline == [] and timetable == [] and staff == [] and location == [] and related == [] and name == []:
            cut_outline = split_space(items['outline text'])
            info += 'Outline link is: '+ items['outline link']+', ' + 'outline is: ' + cut_outline +'.\n'
        # find any kind of information user queries
        else:
            if handbook != []:
                info += 'Handbook link is: ' + items['handbook link'] +'.\n'
            if outline != []:
                cut_outline = split_space(items['outline text'])
                info += 'Outline link is: '+ items['outline link']+', ' + 'outline is: ' + cut_outline +'.\n'
            if timetable != []:
                time_info = print_term_info('timetable',items['timetable'])
                info += 'Time link is: ' + items['timetable link']+', ' + 'timetable is: ' + time_info
            if staff != []:
                staff_info = print_term_info('staff',items['staff'])
                info += 'Staff is: '+ staff_info
            if location != []:
                loc_info = print_term_info('location',items['location'])
                info += 'Location is: '+loc_info
            if related != []:
                if items['prerequisite'] == 'N/a':
                    info += 'There is no prerequisite course.'+ '.\n'
                else:
                    info += items['prerequisite'] + '.\n'
                if items['exclusion list'] == []:
                    info += 'There is no exclusion course.'+ '\n'
                else:
                    info += 'Exclusion course is: '+' '.join(items['prerequisite']) + '.\n'
            if name != []:
                info += 'Course name is ' + items['course name'] + '.\n'
        info += '\n' 
    return info
    
### stream recommendation
def stream_courses_rec(epic1_return):
    stream_name = epic1_return['stream_name']
    if stream_name == []:    #can not retrieve without valid stream name,just return all stream names
        a = ['Artificial intelligence', 'Bioinformatics','Data science and engineering','Database systems','E-Commerce systems','Geospatial','Information technology','Internetworking']
        res = ' '.join(a)
        s = 'CSE has these stream names: ' + res + '. ' + 'Do you want query one specific stream name?' 
        return s#'Please provide valid stream name.'
    
    code_list = epic1_return['course']
    
    info = ''
    table = get_table()
    if code_list == []:
        for stream in stream_name:
            courses_list = table.scan(FilterExpression = Attr('Course').eq(stream) & Attr('Function').eq('Specialisations'))['Items'][0]['stream courses list']
            info += 'My recommendations for '+ stream + ' are: ' + ' '.join(courses_list) + '.\n'
    else:
        # exclude the course that user had attended
        for stream in stream_name:
            courses_list = list(set(table.scan(FilterExpression = Attr('Course').eq(stream) & Attr('Function').eq('Specialisations'))['Items'][0]['stream courses list']) - set(code_list)) 
            info += 'My recommendations for '+ stream + ' are: ' + ' '.join(courses_list) + '.\n'
    return info
    
 
### course planning
def course_planning(epic1_return):
    
    code_list = epic1_return['course']
    if code_list == []:    #can not retrieve without valid course code,just return 4 basic courses 
        return 'You can choose basic courses like COMP9021, COMP9020, COMP9311, GSOE9820.'
    info = ''
    table = get_table()
    for course in code_list:
        items = table.scan(FilterExpression = Attr('Course').eq(course) & Attr('Function').eq('Courses'))['Items'][0]
        if items['prerequisite'] != 'N/a':
            info += 'For ' + course + ' you can choose, \n'
            info += items['prerequisite'] +'\n'
        else:
            if items['exclusion list'] != []:
                info += 'For ' + course + ' you can choose, \n'
                info += 'Exclusions: ' + ' '.join(items['exclusion list']) + '\n'
            else:
                info += 'There is no related course with ' + course + '\n'
    return info

### time clash check
def check_hour(t11,t12,t21,t22):
    if t22 <= t11:
        return True
    if t21 >= t12:
        return True
    if t11 <= t21 and t21 < t12:
        return False
    if t21 <= t11 and t11 < t22:
        return False
    if t11 <= t21 and t22 <= t12:
        return False
    if t21 <= t11 and t12 <= t22:
        return False

def check_time(table1,table2):
    days = ''
    if table1 == {} or table2 == {}:
        return days
    else:
        for day in table1:
            if day in table2.keys():
                t1 = table1[day]
                t2 = table2[day]
                for t in t1:
                    t11 = datetime.datetime.strptime(t[0:6].strip(), '%H:%M')
                    t12 = datetime.datetime.strptime(t[8:].strip(), '%H:%M')
                    for tt in t2:
                        t21 = datetime.datetime.strptime(tt[0:6].strip(), '%H:%M')
                        t22 = datetime.datetime.strptime(tt[8:].strip(), '%H:%M')
                        result = check_hour(t11,t12,t21,t22)
                        if result == False:
                            days += day + ' '
        return days

def clash_check(epic1_return):

    code_list = copy.copy(epic1_return['course'])
    
    if code_list == []:    # can not retrieve without valid course code
        return 'Please provide valid courses code.'
    
    if len(code_list) < 2:   # no clash for just one course
        return 'There is no clash for one course.'
    
    info = ''
    table = get_table()
    for course in code_list:
        timetable = table.scan(FilterExpression = Attr('Course').eq(course) & Attr('Function').eq('Courses'))['Items'][0]['timetable']
        code_list.remove(course)
        for other in code_list:    # every two course need to be compared with timetable
            other_timetable = table.scan(FilterExpression = Attr('Course').eq(other) & Attr('Function').eq('Courses'))['Items'][0]['timetable']
            for t in timetable:
                result = check_time(timetable[t],other_timetable[t])
                if result != '':
                    info += course + ' and ' + other
                    info += ' has clash in Term ' + t + ' in ' + result + '.\n'
    if info == '':
        #print(epic1_return['course'])
        info += 'There is no time clash.\n'
    
    return info
    
    
### divide into retrieve functions by intents
def retrieval_func(epic1):
    response = 'eorro'
    if epic1['intent'] == 'Graduate requirements':
        response = graduate_req(epic1)
    elif epic1['intent'] ==  'Stream course recommendation':
        response = stream_courses_rec(epic1)
    elif epic1['intent'] == 'Time clash checking':
        response =  clash_check(epic1)
    elif epic1['intent'] == 'Course planning':
        response = course_planning(epic1)
    elif epic1['intent'] == 'Basic courses information':
        response = basic_courses_info(epic1)
    return response
