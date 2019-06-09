import tweepy
import time
import utils
import json
import wankosobaround
import pymongo
import random
import directmessage
import timelimitround
from datetime import datetime

import APIControler


ctrls = APIControler.APIControler()

utils.getmentions.lastgettime = datetime(2000,10,1,0,0,0,0)
utils.getmentions.lastid = ctrls.twapi.mentions_timeline(count=1)[0].id


roundrange = [2,58]

while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
    utils.sleepwithlisten(ctrls, 1)

roundstart = None
timelimit = None
mode = None
roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)

with open('rounds.json') as f:
    rounds = json.load(f)

if roundname in rounds.keys():
    roundstart = rounds[roundname]['roundstart']
    timelimit = datetime.strptime(rounds[roundname]['timelimit'], '%Y/%m/%d %H:%M:%S')
    mode = rounds[roundname]['mode']

while True:
    
    if roundstart == None:
        mode = ['Time-Limited', 'Wanko-Soba'][datetime.now().hour%2]

        utils.absolutedofunc(ctrls.twapi.update_status, mode + ' Round ' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour))
        
        with open('history.json','r') as f:
            history = json.load(f)
            roundstart = int(len(history) + 1)

        roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)
        timelimit = datetime.now()
        timelimit = datetime(timelimit.year, timelimit.month, timelimit.day, timelimit.hour, roundrange[1], 0, 0)
        
        with open('rounds.json', 'w') as f:
            rounds[roundname] = {}
            rounds[roundname]['mode'] = mode
            rounds[roundname]['roundstart'] = roundstart
            rounds[roundname]['timelimit'] = timelimit.strftime('%Y/%m/%d %H:%M:%S')
            json.dump(rounds,f)
            
        ctrls.db['user'].update_many({}, {'$set' : {'roundscore' : 0}})
            
    if mode == 'Wanko-Soba':
        wankosobaround.startround(ctrls, roundstart, timelimit, roundname)
        
    if mode == 'Time-Limited':
        timelimitround.startround(ctrls, roundstart, timelimit, roundname)


    roundstart = None
    
    while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
        utils.sleepwithlisten(ctrls, 10)
    