import tweepy
import time
import utils
import wankosobaround
import pymongo
import random
import directmessage
import timelimitround
import contest
from datetime import datetime

import APIControler

ctrls = None

if __name__ == '__main__':
    print("start up")
    
    ctrls = APIControler.APIControler()
    
    utils.getmentions.lastgettime = datetime(2000,10,1,0,0,0,0)
    utils.getmentions.lastid = ctrls.twapi.mentions_timeline(count=1)[0].id
    
    
    roundrange = [1,59]
    
    while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
        utils.sleepwithlisten(ctrls, 1)
    
    print('mode [0 default 1 tl 2 wanko 3 contest]:')
    modei = int(input())
    
    if modei == 0:
        mode = None
    else:
        mode = ['Time-Limited', 'Wanko-Soba', 'Contest'][modei-1]

    roundstart = None
    timelimit = None



    roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)
    
    rounddict = ctrls.db['round'].find_one({'round_num': roundname})
    
    if rounddict != None:
        roundstart = rounddict['roundstart']
        timelimit = datetime.strptime(rounddict['timelimit'], '%Y/%m/%d %H:%M:%S')
        mode = rounddict['mode']

    
    while True:
        
        if roundstart == None:
            if mode == None:
                mode = ['Time-Limited', 'Wanko-Soba', 'Contest'][datetime.now().hour%2]
    
            if mode != 'Contest':
                utils.absolutedofunc(ctrls.twapi.update_status, mode + ' Round ' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour))
            
            roundstart = list(ctrls.db['problem'].find({'used' : True}).sort('problem_num', direction=pymongo.DESCENDING) )[0]['problem_num'] + 1
    
            roundname = str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + str(datetime.now().hour)
            timelimit = datetime.now()
            timelimit = datetime(timelimit.year, timelimit.month, timelimit.day, timelimit.hour, roundrange[1], 0, 0)
            
            rounddict = {}
            rounddict['mode'] = mode
            rounddict['roundstart'] = roundstart
            rounddict['timelimit'] = timelimit.strftime('%Y/%m/%d %H:%M:%S')
            rounddict['round_num'] = roundname
            ctrls.db['round'].insert(rounddict)
                
            ctrls.db['user'].update_many({}, {'$set' : {'roundscore' : 0}})
                
        if mode == 'Wanko-Soba':
            wankosobaround.startround(ctrls, roundstart, timelimit, roundname)
            
        if mode == 'Time-Limited':
            timelimitround.startround(ctrls, roundstart, timelimit, roundname)

        if mode == 'Contest':
            contest.startround(ctrls, roundstart, timelimit, roundname)
    
    
        roundstart = None
        
        while datetime.now().minute < roundrange[0] or datetime.now().minute >= roundrange[1]:
            utils.sleepwithlisten(ctrls, 10)
        