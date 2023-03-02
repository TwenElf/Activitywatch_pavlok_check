
from datetime import datetime, time, timedelta
from time import sleep
import socket
import requests
import aw_client
import json
import re

pavlok_code = "____"
aw_category_filename = "aw-category-export.json"

def get_aw_category_export(filename):
    data2 = {}
    with open(filename, 'r') as f:
        data = json.load(f)
        f.close()
    for categories in data['categories']:
        name_list = categories['name']
        name = ""
        for x in range((len(name_list))): # add > between the different category names
            name += name_list[x]
            if (x+1) != len(name_list):
                name+=">"
        if categories['rule']['type'] != None and categories['rule']['type'] == 'regex': # skip empty category checks
            if 'ignore_case' in categories['rule'].keys(): # create a regex object with ignore case if needed
                if categories['rule']['ignore_case'] ==True:
                    data2[name] = re.compile(categories['rule']['regex'],re.IGNORECASE)
                    continue
            data2[name] = re.compile(categories['rule']['regex'])
    print("loaded", filename)
    return data2


def get_timeofevent(events, app, title):
    events = [e for e in events if (e.data["app"] == app and title in e.data['title'].lower())]
    total_duration = sum((e.duration for e in events), timedelta())
    return total_duration

def get_timeofevent_category(events, regex):
    events = [e for e in events if (regex.search(e.data["app"]) or regex.search(e.data["title"]))]
    total_duration = sum((e.duration for e in events), timedelta())
    return total_duration

def send_zap(zap_strength,message, timeout_duration=10):
        try: # catch the pavlok not being online hapens more often than i would like
            r = requests.get(f"https://app.pavlok.com/unlocked/remotes/{pavlok_code}/zap/{zap_strength}?message={message}", timeout=timeout_duration)
            if r.status_code == 200:
                return 0
            else:
                print("connection to pavlok failed status:",r.status_code)
                return 1
        except:
            print("connection to pavlok failed")
            return 2

def check_time_spent(events, check_dict,connection_fail_counter=1):
    if check_dict["zap"] > 255:
        check_dict["zap"] = 255
    check_dict = update_time(events,check_dict)
    #print(f"{str(datetime.now().time()):14} Time on {check_dict['title']:7}: {str(total_duration):14} next zap at: {str(check_dict['check']):14}")
    if check_dict['current_check'] > check_dict["check"]: # schock when passing an amount of time
        message = f"{check_dict['title']}:{check_dict['current_check']}"
        zap_result = send_zap(check_dict["zap"],message)
        if zap_result == 1 or zap_result ==2:
            sleep(30*connection_fail_counter)
            connection_fail_counter += 1
            return check_dict
        else:
            print("zap",message)

        if check_dict["check"] >= check_dict["max_time"]: # after x amount of minutes start giving shocks every minute
            if check_dict["zap_counter"] >= 10: # send more shocks if after 10 + minutes of shocking i am still going so change it to every 10 seconds
                check_dict["check"] += timedelta(seconds=10)
                if check_dict["zap_counter"] > 15: # increase strength if it has happend more than 15 times
                    check_dict["zap"] += 31
            else:
                check_dict["check"] += timedelta(minutes=1)
            check_dict["zap_counter"] += 1
        else: # for the first times before the x minute mark give one every 15 minutes
            check_dict["zap_counter"] += 1
            check_dict["check"] += timedelta(minutes=15)
    return check_dict

def update_time(events,check_dict):
    if 'category_regex' in check_dict.keys():
        check_dict['current_check'] = get_timeofevent_category(events, check_dict["category_regex"])
    else:
        check_dict['current_check'] = get_timeofevent(events, check_dict["app"],check_dict["title"])
    return check_dict

def update_check(check_dict, events):
    check_dict = update_time(events,check_dict)
    if check_dict["current_check"] >= check_dict["check"]: # if it was restarted but time was already registered beyond one of the checks add one second in stead of schoking at startup
        check_dict["check"] = check_dict["current_check"] + timedelta(seconds=1)
    return check_dict

def update_events(awc,bucket_id,daystart,dayend):
    events = awc.get_events(bucket_id, start=daystart, end=dayend)
    return events

if __name__ == "__main__":
    # Set this to your AFK bucket
    bucket_id = f"aw-watcher-window_{socket.gethostname()}"
    bucket_id = "aw-watcher-window_Lucy"
    awc = aw_client.ActivityWatchClient(host='127.0.0.1')
    connection_fail_counter = 1

    # set times that it checks between currently between 00:00 till 17:00
    workdaystart = datetime.combine(datetime.now().date(), time()) #- timedelta(days=1)
    workdayend = workdaystart + timedelta(hours=17, minutes=00)

    aw_category = get_aw_category_export(aw_category_filename)

    youtube_check ={
        'name':"Youtube",               # to be shown in the print
        "app":'firefox.exe',            # the application to look for
        "title":'youtube',              # title of the window
        'check':timedelta(minutes=15),  # amount of time till first shock
        'current_check':0,              # time of starting will be updated at update_check
        'zap':132,                      # the strength of the first 15 zaps
        'zap_counter':0,                # the amount of zaps already happend to decrease the time and increase the zapstrength. 10 = zap every 10 seconds 15+ = zap every 10 + increase in strength. counter increases every zap
        'max_time': timedelta(minutes=15), # amount of time having passed before start zapping every minute
        'category_regex': aw_category['Time sinks>Youtube'] # not required: name of the rule from the category export typed like {Category name}>{sub category name}
    }
    reddit_check ={
        'name':"Reddit",
        "app":'firefox.exe',
        "title":'reddit',
        'check':timedelta(minutes=15),
        'current_check':0,
        'zap':132,
        'zap_counter':0,
        'max_time': timedelta(minutes=30),
        'category_regex': aw_category['Time sinks>Reddit']
    }
    opera_check ={
        'name':"REDACTED",
        "app":'opera.exe',
        "title":'pornhub',
        'check':timedelta(minutes=1),
        'current_check':0,
        'zap':132,
        'zap_counter':10, # set higher zap counter to increase frequency
        'max_time': timedelta(minutes=1,seconds=30)
    }
    plex_check ={
        'name':"Plex",
        "app":'Plex.exe',
        "title":'plex',
        'check':timedelta(minutes=18),
        'current_check':0,
        'zap':132,
        'zap_counter':0,
        'max_time': timedelta(minutes=20),
        'category_regex': aw_category['Time sinks>Plex']
    }
    print(f"start checking starting from {workdaystart} ending at {workdayend}")

    events = update_events(awc,bucket_id,workdaystart,workdayend)

    youtube_check = update_check(youtube_check, events)
    reddit_check = update_check(reddit_check, events)
    opera_check = update_check(opera_check, events)
    plex_check = update_check(plex_check, events)

    while True:
        events = update_events(awc,bucket_id,workdaystart,workdayend)

        youtube_check = check_time_spent(events,youtube_check,connection_fail_counter)
        reddit_check = check_time_spent(events,reddit_check,connection_fail_counter)
        opera_check = check_time_spent(events,opera_check,connection_fail_counter)
        plex_check = check_time_spent(events,plex_check,connection_fail_counter)

        print(f"{str(datetime.now().time())[:8]}"+ 
              f"\n|{youtube_check['name']:8}: {str(youtube_check['current_check'])[:7]} next zap at: {str(youtube_check['check'])[:7]}"+
              f"\n|{reddit_check['name']:8}: {str(reddit_check['current_check'])[:7]} next zap at: {str(reddit_check['check'])[:7]}"+
              f"\n|{opera_check['name']:8}: {str(opera_check['current_check'])[:7]} next zap at: {str(opera_check['check'])[:7]}"+
              f"\n|{plex_check['name']:8}: {str(plex_check['current_check'])[:7]} next zap at: {str(plex_check['check'])[:7]}")

        sleep(10) # to not spend all my time schocking myself